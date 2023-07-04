import numpy as np
import multiprocessing as mp
import os
import h5py

from tqdm.notebook import tqdm
from functools import partial
from datetime import datetime

from id01lib.io.utils import ioh5
from id01lib.io.bliss import (
    get_command,
    get_counter,
    get_positioner,
    get_detector_aliases,
)

from .utils import _get_chunk_indexes

@ioh5
def get_sxdm_scan_numbers(h5f, interrupted_scans=False):
    scan_nos = []
    for entry in list(h5f.keys()):
        command = h5f[f'{entry}/title'][()].decode()
        if any([s in command for s in ("sxdm", "mesh", "kmap")]):
            if not interrupted_scans:
                try:
                    h5f[entry]["measurement"]
                    scan_nos.append(entry)
                except KeyError:
                    pass
            else:
                scan_nos.append(entry)

    scan_nos.sort(key=lambda s: int(s.split('.')[0]))

    return scan_nos


@ioh5
def get_scan_shape(h5f, scan_no):
    command_list = h5f[f"{scan_no}/title"][()].decode().split(" ")
    try:
        sh = [h5f[f"{scan_no}/technique/{x}"][()] for x in ("dim0", "dim1")][::-1]
    except KeyError:  # must be a mesh or a scan
        try:  # mesh
            sh = [int(command_list[x]) + 1 for x in (4, 8)][::-1]
        except IndexError:  # scan
            sh = int(command_list[4])

    return sh


@ioh5
def get_datetime(h5f, scan_no):
    scan_no = scan_no
    dtime = h5f[f"{scan_no}/start_time"][()].decode()
    dtime = datetime.fromisoformat(dtime).strftime("%b %d | %H:%M:%S")

    return dtime


@ioh5
def get_detcalib(h5f, scan_no):
    params = dict(beam_energy=0, center_chan=[], chan_per_deg=[])
    calib = h5f[f"{scan_no}/instrument/detector"]

    for key in params.keys():
        if key == "beam_energy":
            params[key] = calib[key][()]
        else:
            params[key] = [calib[f"{key}_dim{i}"][()] for i in (0, 1)]

    return params


def get_piezo_motor_names(h5f, scan_no):
    command = get_command(h5f, scan_no)
    if any([x in command for x in ("sxdm", "kmap", "mesh")]): 
        m1_name, m2_name = [command.split(" ")[x] for x in (1, 5)]
        if ',' in m1_name:
            m1_name, m2_name = m1_name[:-1], m2_name[:-1]
    else:
        fname = os.path.basename(h5f)
        msg = f"Scan {scan_no} in {fname} is not a mesh or an sxdm scan!"
        raise Exception(msg)

    return m1_name, m2_name


def get_piezo_motor_positions(h5f, scan_no):
    sh = get_scan_shape(h5f, scan_no)
    m1n, m2n = get_piezo_motor_names(h5f, scan_no)

    try:  # sxdm
        m1, m2 = [get_positioner(h5f, scan_no, f"{m}_position") for m in (m1n, m2n)]
    except KeyError:  # mesh
        m1, m2 = [get_positioner(h5f, scan_no, m) for m in (m1n, m2n)]
    m1, m2 = [m.reshape(*sh) for m in (m1, m2)]

    return m1, m2


def get_roidata(h5f, scan_no, roi_name, return_pi_motors=False):
    sh = get_scan_shape(h5f, scan_no)
    data = get_counter(h5f, scan_no, roi_name)

    if data.size == sh[0] * sh[1]:
        data = data.reshape(*sh)
    else:
        empty = np.zeros(sh).flatten()
        empty[: data.size] = data
        data = empty.reshape(*sh)

    if return_pi_motors:
        m1, m2 = get_piezo_motor_positions(h5f, scan_no)
        return data, m1, m2
    else:
        return data


def _get_frames_chunk(path_dset, path_in_h5, roi_dir_idxs, idx_range):
    """
    Return the q-space intensity array summed over the (flattened) sample positons
    given by `idx_range`, which is a list of tuples.
    """
    idx_list = [x for x in range(*idx_range, 1) if x in roi_dir_idxs]
    with h5py.File(path_dset, "r") as h5f:
        arr = h5f[path_in_h5][idx_list, ...].sum(0)

    return arr


def get_sxdm_frame_sum(
    path_dset,
    scan_no,
    mask_direct=None,
    detector="mpx1x4",
    n_proc=None,
):
    """
    Return the sum of all detector frames collected within an SXDM scan.
    """
    detlist = get_detector_aliases(path_dset, scan_no)
    if detector not in detlist:
        raise ValueError(
            f"Detector {detector} not in data file. Available detectors are: {detlist}."
        )
    else:
        path_data_h5 = f"/{scan_no}/instrument/{detector}/data"

        if n_proc is None:
            n_proc = os.cpu_count()

        # list of idx ranges [(i0, i1), (i0, i1), ...]
        indexes = _get_chunk_indexes(path_dset, path_data_h5, n_proc)

        # direct space shape (1D)
        with h5py.File(path_dset, "r") as h5f:
            sh = h5f[path_data_h5].shape[0]

        # direct space slice from mask
        if mask_direct is not None:
            roi_dir_idxs = np.where(np.invert(mask_direct).flatten())[0]
        else:
            roi_dir_idxs = np.indices((sh,))[0]

        pfun = partial(_get_frames_chunk, path_dset, path_data_h5, roi_dir_idxs)
        frame_sum_list = []
        with mp.Pool(processes=n_proc) as p:
            for res in tqdm(p.imap(pfun, indexes), total=len(indexes)):
                frame_sum_list.append(res)

        return np.stack(frame_sum_list).sum(0)


def _calc_pos_sum_chunk(path_dset, path_in_h5, roi_rec_sl, idx_range):
    """
    Calculate the direct space intensity of a 4D SXDM dataset:
    * for the direct space indexes in the range `idx_range`;
    * within the reciprocal space slice `roi_rec_sl`;
    * masked in direct space where `mask_direct` is True.

    Returns a `numpy.masked_array`.
    """
    i0, i1 = idx_range

    roi_slice = (slice(i0, i1, None), *roi_rec_sl)  # 3D
    with h5py.File(path_dset, "r") as h5f:
        arr = h5f[path_in_h5][roi_slice].sum(axis=(1, 2))

    return arr


def get_sxdm_pos_sum(
    path_dset,
    scan_no,
    mask_reciprocal=None,
    detector="mpx1x4",
    n_proc=None,
):

    detlist = get_detector_aliases(path_dset, scan_no)
    if detector not in detlist:
        raise ValueError(
            f"Detector {detector} not in data file. Available detectors are: {detlist}."
        )
    else:
        path_h5_data = f"{scan_no}/measurement/{detector}"

    if n_proc is None:
        n_proc = os.cpu_count()

    # list of idx ranges [(i0, i1), (i0, i1), ...]
    idxs_list = _get_chunk_indexes(path_dset, path_h5_data, n_threads=n_proc)

    # recipocal space slice from mask
    if mask_reciprocal is not None:
        roi_rec = np.where(np.invert(mask_reciprocal))
        roi_rec_sl = tuple([slice(x.min(), x.max() + 1) for x in roi_rec])
    else:
        roi_rec_sl = np.s_[:, :]

    # call function with everything except the index ranges
    # the function returns a direct space map
    pfun = partial(_calc_pos_sum_chunk, path_dset, path_h5_data, roi_rec_sl)

    # apply partial function multi process, with an index range per process
    roi_sum_list = []
    with mp.Pool(processes=n_proc) as p:
        for res in tqdm(p.imap(pfun, idxs_list), total=len(idxs_list)):
            roi_sum_list.append(res)

    return np.ma.concatenate(roi_sum_list)


@ioh5
def get_roi_pos(h5f, scan_no, roi_names_list, detector="mpx1x4"):
    """
    Only works for ROIs starting with `detector_`
    x,y,width,height
    """

    roi_params = {key: None for key in roi_names_list}
    for r in roi_params.keys():
        roi_params[r] = [
            h5f[f"/{scan_no}/instrument/{detector}_{r}/selection/{m}"][()]
            for m in "x,y,width,height".split(",")
        ]

    return roi_params
