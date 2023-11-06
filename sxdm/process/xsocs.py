import os
import numpy as np
import multiprocessing as mp
import shutil
import glob
import h5py
import hdf5plugin
import time
import concurrent.futures

from functools import partial
import scipy.ndimage as ndi

from xsocs.io.XsocsH5 import XsocsH5
from xsocs.process.qspace import qspace_conversion
from xsocs.process.qspace import QSpaceConverter

from id01lib.io.bliss import get_positioner
from id01lib.xrd.qspace.bliss import _det_aliases

from ..io.utils import list_available_counters, _get_chunk_indexes_detector


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
    qconv=None,
    sample_ip=[1, 0, 0],
    sample_oop=[0, 0, 1],
    det_ip="y+",
    det_oop="z-",
    sampleor='det'
):

    converter = QSpaceConverter(
        path_master,
        nbins,
        roi=roi,
        medfilt_dims=medfilt_dims,
        output_f=path_qconv,
        offsets=offsets,
        qconv=qconv,
        sample_ip=sample_ip,
        sample_oop=sample_oop,
        det_ip=det_ip,
        det_oop=det_oop,
        sampleor=sampleor,
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


def get_qspace_vals_xsocs(
    path_master,
    offsets=dict(),
    center_chan=None,
    chan_per_deg=None,
    beam_energy=None,
    qconv=None,
    roi=None,
    sample_ip=[1, 0, 0],
    sample_oop=[0, 0, 1],
    det_ip="y+",
    det_oop="z-",
    sampleor='det',
):

    h5f = XsocsH5(path_master)
    entry0 = h5f.get_entry_name(entry_idx=0)
    with h5f:
        detpath = h5f._XsocsH5Base__file[f"/{entry0}/measurement/image/data"].name
        detpath_list = detpath.split("/")
        try:
            det = _det_aliases[detpath_list[-1]]
        except KeyError:  # nanomax syntax, Merlin/data
            try:
                det = _det_aliases[detpath_list[-2]]
            except KeyError:  # no recognisible det name, xsocs file
                counters = list_available_counters(path_master, entry0)

                for d in _det_aliases.keys():
                    matches = []
                    for c in counters:
                        matches.append(d in c)
                    if any(matches):
                        det = _det_aliases[d]
                        break

    angles = {key: None for key in "phi,eta,nu,del".split(",")}
    for a in angles:
        angles[a] = np.sort(np.array([h5f.positioner(e, a) for e in h5f.entries()]))

    nrj, cen_pix, cpd = h5f.acquisition_params().values()
    if center_chan is None:
        center_chan = cen_pix[::-1]
    if chan_per_deg is None:
        chan_per_deg = cpd
    if beam_energy is None:
        beam_energy = nrj

    if roi == None:
        img_size = det.pixnum
    else:
        img_size = (roi[1] - roi[0], roi[3] - roi[2])

    q_array = qspace_conversion(
        img_size,
        center_chan,
        chan_per_deg,
        beam_energy,
        *angles.values(),
        offsets=offsets,
        qconv=qconv,
        sample_ip=sample_ip,
        sample_oop=sample_oop,
        det_ip=det_ip,
        det_oop=det_oop,
        sampleor=sampleor,
    )

    qx, qy, qz = q_array.transpose(3, 0, 1, 2)

    return qx, qy, qz


def estimate_n_bins(
    path_master,
    offsets=dict(),
    center_chan=None,
    chan_per_deg=None,
    beam_energy=None,
    qconv=None,
    roi=None,
):

    qx, qy, qz = get_qspace_vals_xsocs(
        path_master,
        offsets=offsets,
        center_chan=center_chan,
        chan_per_deg=chan_per_deg,
        beam_energy=beam_energy,
        qconv=qconv,
        roi=roi,
    )

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

    with h5py.File(path_subh5, "r", libver="latest") as h5f:

        # get shift in pixels for this eta value
        root = list(h5f.keys())[0]
        data = h5f[f"/{root}/instrument/detector/data"]  # shape: (x*y, detx, dety)
        eta = str(np.round(h5f[f"{root}/instrument/positioners/eta"][()], 4))
        shift = etashift[eta]

        # shapes
        if roi is None:
            sh_data = data.shape
        else:
            sh_data = (data.shape[0], roi[1] - roi[0], roi[3] - roi[2])
        
        sh_map = tuple(
            [h5f[f"{root}/scan/motor_{i}_steps"][()] for i in (0, 1)]
        )  # (x, y)

        # chunk indexes for two detector dimensions
        idx0, idx1 = _get_chunk_indexes_detector(
            path_subh5, data.name, n_chunks=n_chunks, roi=roi
        )

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

        # chunk size
        sh_chunk = np.diff(idx0)[0, 0], np.diff(idx1)[0, 0]
        chsize = (n_chunks, *sh_chunk)
        print(f"\n>> Shifting #{scan_no}... chunk size {chsize}", flush=True)

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
                shape=sh_data,
                dtype=np.uint16,
                # dtype=data.dtype,
                chunks=(1, *sh_chunk),
                **hdf5plugin.Bitshuffle(nelems=0, cname="lz4"),
            )
            det_shift_link["data"] = data_shift

            # for each chunk of original (unshifted) data
            for (ir0, ir1) in idx0:
                for (ic0, ic1) in idx1:
                    sl_chunk = np.s_[:, ir0:ir1, ic0:ic1]

                    # read the chunk
                    _t2 = time.time()
                    chunk = (
                        data[sl_chunk].reshape(sh_map[::-1] + (-1,)).copy()
                    )  # x,y,detx*dety
                    t2 += time.time() - _t2

                    # if shifts are non-zero within tolerance
                    if not np.allclose(shift, 0, atol=1e-3):
                        # shift each data point in the chunk
                        for i in range(chunk.shape[-1]):
                            chunk[..., i] = ndi.shift(chunk[..., i], shift)

                    # write the shifted chunks to the shift file
                    _t2 = time.time()
                    sh_chunk = (
                        ir1 - ir0,
                        ic1 - ic0,
                    )  # need it because last chunk may be different
                    chunk.resize((np.prod(sh_map),) + sh_chunk)

                    irs, ics = idx0[0][0], idx1[0][0]
                    sl_chunk_roi = np.s_[:,ir0-irs:ir1-irs, ic0-ics:ic1-ics]
                    data_shift[sl_chunk_roi] = chunk
                    t2 += time.time() - _t2
                    del chunk

    t_tot = time.time() - t_init
    print(
        f"\n{os.path.basename(path_subh5)} finished after "
        f"{t_tot/60:.2f}m. I/O time: {t2/60:.2f}m",
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
            ftolink = f"{xsocs_dset_name[:-7]}_{s}_shifted.h5"
            del h5f[s]
            h5f[s] = h5py.ExternalLink(ftolink, f"/{s}")


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

    pf = partial(
        _shift_write_data, path_master, shifts, n_chunks, roi, overwrite=overwrite
    )

    with concurrent.futures.ProcessPoolExecutor() as exec:
        try:
            for result in exec.map(pf, subh5_list):
                pass
        except concurrent.futures.process.BrokenProcessPool:
            print(
                "\n >> You are probably out of memory! Try running the function "
                "again with n_chunks=N with N greater than what was used here.\n"
            )

    _make_shift_master(path_master, path_out)
