import os
import numpy as np
import multiprocessing as mp
import shutil
import glob
import h5py
import hdf5plugin
import xsocs
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


def _get_eta_shift(path_dset, shifts):
    with h5py.File(path_dset, "r") as h5f:
        scan_nums = [f"{x}.1" for x in range(1, len(list(h5f.keys())) + 1)]

    etashift = dict()
    for s, shift in zip(scan_nums, shifts):
        eta = np.round(get_positioner(path_dset, s, "eta"), 4)
        etashift[str(eta)] = shift

    return etashift


def _shift_write_data(path_dset, shifts, n_chunks, roi, subh5):

    t_init = time.time()
    scan_no = subh5.split("_")[-1][:-3]
    print(f"\nShifting #{scan_no}...")

    etashift = _get_eta_shift(path_dset, shifts)
    roi = (
        np.s_[roi[0] : roi[1], roi[2] : roi[3]] if roi is not None else np.s_[...]
    )  # TODO!

    with h5py.File(subh5, "r", libver="latest") as h5f:

        root = list(h5f.keys())[0]
        data = h5f[f"/{root}/instrument/detector/data"]  # shape: (x*y, detx, dety)
        eta = str(np.round(h5f[f"{root}/instrument/positioners/eta"][()], 4))
        shift = etashift[eta]

        sh_map = tuple(
            [h5f[f"{root}/scan/motor_{i}_steps"][()] for i in (0, 1)]
        )  # (x, y)
        try:
            sh_chunk = data.chunks[1:]
        except TypeError:  # data is not chunked
            sh_chunk = tuple([x // n_chunks for x in data.shape[1:]])

        fname_subh5_shifted = os.path.abspath(subh5).split(".")[0]
        fname_subh5_shifted = shutil.copy(subh5, f"{fname_subh5_shifted}.1_shifted.h5")

        t2 = 0
        with h5py.File(fname_subh5_shifted, "a", libver="latest") as f:
            det_shift = f[f"{root}/instrument/detector/"]
            det_shift_link = f[f"{root}/measurement/image/"]

            del det_shift["data"]
            del det_shift_link["data"]

            data_shift = det_shift.create_dataset(
                "data",
                shape=data.shape,
                dtype=data.dtype,
                chunks=(1, *sh_chunk),
                **hdf5plugin.Bitshuffle(nelems=0, lz4=True),
            )
            det_shift_link["data"] = data_shift

            # for each chunk of data
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
        f"\n{os.path.basename(subh5)} finished after "
        f"{t_tot:.2f}s. I/O time: {t2:.2f}s"
    )


def make_shift_master(path_out, path_dset):

    namelist = os.path.basename(path_dset).split(".")[0].split("_")
    name_sample = "_".join(namelist[:-1])
    name_dset = namelist[-1]

    master_shifted = shutil.copy(
        f"{path_out}/{name_sample}_{name_dset}_master.h5",
        f"{path_out}/{name_sample}_{name_dset}_master_shifted.h5",
    )

    with h5py.File(master_shifted, "a") as h5f:
        scan_nos = list(h5f.keys())
        for s in scan_nos:
            ftolink = f"{name_sample}_{name_dset}_{s}_shifted.h5"
            del h5f[s]
            h5f[s] = h5py.ExternalLink(ftolink, f"/{s}")


# TODO use concurrent.futures instead
def shift_xsocs_data(path_dset, path_out, shifts, n_chunks=3, roi=None):
    print(f"Using XSOCS installation: {xsocs.__file__}\n")
    name_sample = os.path.basename(path_dset).split("_")[0]
    subh5_list = glob.glob(f"{path_out}/{name_sample}*.1.h5")

    with mp.Pool() as pool:
        pf = partial(_shift_write_data, path_dset, shifts, n_chunks, roi)
        pool.map(pf, subh5_list)

    _make_shift_master(path_out, path_dset)
