import os
import numpy as np
import multiprocessing as mp
import shutil
import glob
import h5py
import hdf5plugin
import time

from functools import partial
import scipy.ndimage as ndi

from xsocs.io.XsocsH5 import XsocsH5
from xsocs.process.qspace import qspace_conversion
from xsocs.process.qspace import QSpaceConverter

from id01lib.io.bliss import get_positioner
from id01lib.xrd.qspace.bliss import _det_aliases


def grid_qspace_xsocs(
    path_qconv,
    path_master,
    nbins,
    roi=None,
    medfilt_dims=None,
    offsets=None,
    overwrite=False,
    correct_mpx_gaps=True,
    normalizer=None,
    mask=None,
    n_proc=None,
    center_chan=None,
    chan_per_deg=None,
    beam_energy=None,
):

    converter = QSpaceConverter(
        path_master,
        nbins,
        roi=roi,
        medfilt_dims=medfilt_dims,
        output_f=path_qconv,
        offsets=offsets,
    )

    converter.maxipix_correction = correct_mpx_gaps
    converter.normalizer = normalizer
    converter.mask = mask
    converter.n_proc = n_proc
    converter.disp_times = True
    if center_chan is not None:
        converter.direct_beam = center_chan
    if chan_per_deg is not None:
        converter.channels_per_degree = chan_per_deg
    if beam_energy is not None:
        converter.beam_energy = beam_energy

    converter.convert(overwrite=overwrite)

    rc = converter.status
    if rc != QSpaceConverter.DONE:
        raise ValueError(
            "Conversion failed with CODE={0} :\n"
            "{1}"
            ""
            "".format(converter.status, converter.status_msg)
        )


def get_qspace_vals_xsocs(path_master, offsets=dict()):

    h5f = XsocsH5(path_master)
    entry0 = h5f.get_entry_name(entry_idx=0)
    with h5f:
        detpath = h5f._XsocsH5Base__file[f"/{entry0}/measurement/image/data"].name
        detalias = detpath.split("/")[-1]

    det = _det_aliases[detalias]
    angles = {key: None for key in "phi,eta,nu,del".split(",")}
    for a in angles:
        angles[a] = np.sort(np.array([h5f.positioner(e, a) for e in h5f.entries()]))

    nrj, cen_pix, cpd = h5f.acquisition_params().values()

    q_array = qspace_conversion(
        det.pixnum, cen_pix[::-1], cpd, nrj, *angles.values(), offsets=offsets
    )

    qx, qy, qz = q_array.transpose(3, 0, 1, 2)

    return qx, qy, qz


def estimate_n_bins(path_master, offsets=dict()):

    qx, qy, qz = get_qspace_vals_xsocs(path_master, offsets=offsets)

    maxbins = []
    for dim in (qx, qy, qz):
        maxbin = np.inf
        for j in range(dim.ndim):
            step = abs(np.diff(dim, axis=j)).max()
            bins = (abs(dim).max() - abs(dim).min()) / step
            maxbin = min(maxbin, bins)
        maxbins.append(int(maxbin) + 1)

    return maxbins


def _get_motor_dict(path_master, ls, motor_name="eta"):
    """
    Match the chosen motor (default: eta) associated with the master or dataset file
    `path_master` with a list `ls` of something (e.g. shifts). Returns a dict.
    """

    motor_dict = dict()
    with h5py.File(path_master, "r") as h5f:
        scan_nums = sorted(h5f.keys(), key=lambda s: int(s.split(".")[0]))

        if len(ls) != len(scan_nums):
            msg = "The number of scans in `path_master` is different than the length"
            msg += "of `ls`."
            raise ValueError(msg)

        for n, s in zip(scan_nums, ls):
            eta = np.round(h5f[f"{n}/instrument/positioners/{motor_name}"][()], 4)
            motor_dict[str(eta)] = s

    return motor_dict


def _shift_write_data(path_master, shifts, n_chunks, roi, path_subh5, overwrite=False):
    """
    Apply one of `shifts` to the chosen `path_subh5` file.
    """

    t_init = time.time()

    scan_no = path_subh5.split("_")[-1][:-3]
    etashift = _get_motor_dict(path_master, shifts)
    roi = (
        np.s_[roi[0] : roi[1], roi[2] : roi[3]] if roi is not None else np.s_[...]
    )  # TODO not implemented yet

    with h5py.File(path_subh5, "r", libver="latest") as h5f:

        # get shift in pixels for this eta value
        root = list(h5f.keys())[0]
        data = h5f[f"/{root}/instrument/detector/data"]  # shape: (x*y, detx, dety)
        eta = str(np.round(h5f[f"{root}/instrument/positioners/eta"][()], 4))
        shift = etashift[eta]

        # establish data chunk shape
        sh_map = tuple(
            [h5f[f"{root}/scan/motor_{i}_steps"][()] for i in (0, 1)]
        )  # (x, y)
        try:
            sh_chunk = data.chunks[1:]
        except TypeError:  # data is not chunked
            sh_chunk = tuple([x // n_chunks for x in data.shape[1:]])

        # establish shifted file name and get output directory name
        _name_base = os.path.abspath(path_subh5).split(".")[0]
        path_subh5_shift = f"{_name_base}.1_shifted.h5"
        path_out = os.path.dirname(path_subh5)

        # check if the shifted file exists in the output dir, if yes stop
        name_subh5_shift = os.path.basename(path_subh5_shift)
        if name_subh5_shift in os.listdir(path_out) and overwrite is False:
            print(f"\nNOT overwriting #{scan_no}!", flush=True)
            return

        # generate shifted file
        path_subh5_shift = shutil.copy(path_subh5, path_subh5_shift)
        print(f"\n>> Shifting #{scan_no}...", flush=True)

        t2 = 0
        with h5py.File(path_subh5_shift, "a", libver="latest") as f:

            # delete original dataset and its link
            det_shift = f[f"{root}/instrument/detector/"]
            det_shift_link = f[f"{root}/measurement/image/"]

            del det_shift["data"]
            del det_shift_link["data"]

            # create empty dataset where the original was
            data_shift = det_shift.create_dataset(
                "data",
                shape=data.shape,
                dtype=data.dtype,
                chunks=(1, *sh_chunk),
                **hdf5plugin.Bitshuffle(nelems=0, cname='lz4'),
            )
            det_shift_link["data"] = data_shift

            # for each chunk of original (unshifted) data
            for i1 in range(data.shape[1] // sh_chunk[0]):
                for i2 in range(data.shape[2] // sh_chunk[1]):
                    sl_chunk = np.s_[
                        :,
                        i1 * sh_chunk[0] : (i1 + 1) * sh_chunk[0],
                        i2 * sh_chunk[1] : (i2 + 1) * sh_chunk[1],
                    ]

                    # read the chunk
                    _t2 = time.time()
                    chunk = data[sl_chunk].reshape(sh_map[::-1] + (-1,)).copy()
                    t2 += time.time() - _t2

                    # if shifts are non-zero within tolerance
                    if not np.allclose(shift, 0, atol=1e-3):
                        # shift each data point in the chunk
                        for i in range(chunk.shape[-1]):
                            chunk[..., i] = ndi.shift(chunk[..., i], shift)

                    # write the shifted chunks to the shift file
                    _t2 = time.time()
                    chunk.resize((np.prod(sh_map),) + sh_chunk)
                    data_shift[sl_chunk] = chunk
                    t2 += time.time() - _t2
                    del chunk

    t_tot = time.time() - t_init
    print(
        f"\n{os.path.basename(path_subh5)} finished after "
        f"{t_tot/60:.2f}m. I/O time: {t2:.2f}s",
        flush=True,
    )


def _make_shift_master(path_master, path_out):
    """
    Generate a copy of a master file and link it to the shifted subh5s.
    """

    xsocs_dset_name = os.path.basename(path_master).split(".")[0]
    path_master_shifted = f"{path_out}/{xsocs_dset_name}_shifted.h5"

    master_shifted = shutil.copy(path_master, path_master_shifted)

    with h5py.File(master_shifted, "a") as h5f:
        scan_nos = list(h5f.keys())
        for s in scan_nos:
            ftolink = f"{path_out}/{xsocs_dset_name[:-7]}_{s}_shifted.h5"
            del h5f[s]
            h5f[s] = h5py.ExternalLink(ftolink, f"/{s}")


# TODO use concurrent.futures instead
def shift_xsocs_data(
    path_master,
    path_out,
    shifts,
    subh5_list=None,
    n_chunks=3,
    roi=None,
    overwrite=False,
):
    """
    TODO
    """

    if subh5_list is None:
        pattern = f"{path_out}/{os.path.basename(path_master)[:-10]}*.1.h5"
        subh5_list = glob.glob(pattern)
        print(f"Using subh5_list=None, shifting file pattern {pattern} !\n")

    subh5_list = sorted(subh5_list, key=lambda x: x.split("_")[-1].split(".1")[-2])
    if len(subh5_list) != len(shifts):
        raise ValueError("subh5_list and shifts are not the same length!")

    pf = partial(_shift_write_data, path_master, shifts, n_chunks, roi)
    with mp.Pool() as pool:
        pool.map(pf, subh5_list)

    _make_shift_master(path_master, path_out)
