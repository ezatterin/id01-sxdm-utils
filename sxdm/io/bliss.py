import numpy as np
import multiprocessing as mp
import os
import h5py

from tqdm.auto import tqdm
from functools import partial
from datetime import datetime

from id01lib.io.utils import ioh5
from id01lib.io.bliss import (
    get_command,
    get_counter,
    get_positioner,
    get_detector_aliases,
)

from .utils import _get_chunk_indexes, _get_qspace_avg_chunk


@ioh5
def get_scan_shape(h5f, scan_no):
    command_list = h5f[f"{scan_no}/title"][()].decode().split(" ")
    try:
        sh = [h5f[f"{scan_no}/technique/{x}"][()] for x in ("dim0", "dim1")][::-1]
    except KeyError:  # must be a mesh or a scan
        try:  # mesh
            sh = [int(command_list[x][:-1]) + 1 for x in (4, 8)][::-1]
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
    calib = h5f[f'{scan_no}/instrument/detector']

    for key in params.keys():
        if key == 'beam_energy':
            params[key] = calib[key][()]
        else:
            params[key] = [calib[f'{key}_dim{i}'][()] for i in (0,1)]

    return params

def get_piezo_motor_names(h5f, scan_no):
    command = get_command(h5f, scan_no)
    if "mesh" in command:  # this has a spec syntax for now!
        m1_name, m2_name = [command.split(" ")[x] for x in (1, 5)]
    elif any([x in command for x in ("sxdm", "kmap")]):
        m1_name, m2_name = [command.split(" ")[x][:-1] for x in (1, 5)]
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


def get_sxdm_frame_sum(
    path_dset, scan_no, mask_direct=None, n_threads=None, detector="mpx1x4"
):
    """
    Return sum of all frames of an SXDM scan.
    """
    h5_det = get_detector_aliases(path_dset,scan_no)[0]
    
    if detector != h5_det:
        raise ValueError(f'Found \'{h5_det}\' detector name, but defined \'{detector}\' in get_sxdm_frame_sum() function. Please, change it and retry')
    else:
        path_data_h5 = f"/{scan_no}/instrument/{detector}/data"

        if n_threads is None:
            ncpu = os.cpu_count()
        else:
            ncpu = n_threads

        with h5py.File(path_dset, "r") as h5f:
            sh = h5f[path_data_h5].shape[:1]

        indexes = _get_chunk_indexes(path_dset, path_data_h5, ncpu)

        mask = mask_direct if mask_direct is not None else np.ones(sh)
        idx_mask = {idx: val for idx, val in zip(np.indices(sh)[0], mask.flatten())}

        frame_sum_list = []
        with mp.Pool(processes=ncpu) as p:
            pfun = partial(_get_qspace_avg_chunk, path_dset, path_data_h5, idx_mask)
            for res in tqdm(p.imap(pfun, indexes), total=len(indexes)):
                frame_sum_list.append(res)

        frame_sum = np.stack(frame_sum_list).sum(0)

        return frame_sum



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
