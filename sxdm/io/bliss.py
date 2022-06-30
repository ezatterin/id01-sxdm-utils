import numpy as np
import multiprocessing as mp
import os

from tqdm.auto import tqdm
from functools import partial
from datetime import datetime
from .utils import _get_chunk_indexes, _get_qspace_avg_chunk, ioh5


@ioh5
def get_roidata(h5f, scan_no, roi_name, return_pi_motors=False):
    entry = scan_no
    sh = [h5f[entry][f"technique/{x}"][()] for x in ("dim0", "dim1")]
    sh = sh[::-1]
    command = h5f[f"{entry}/title"][()].decode()

    data = h5f[entry][f"measurement/{roi_name}"][()]

    if data.size == sh[0] * sh[1]:
        data = data.reshape(*sh)
    else:
        empty = np.zeros(sh).flatten()
        empty[: data.size] = data
        data = empty.reshape(*sh)

    if return_pi_motors:
        m1, m2 = [command.split(" ")[x][:-1] for x in (1, 5)]
        m1, m2 = [h5f[f"{entry}/measurement/{m}_position"][()] for m in (m1, m2)]
        m1, m2 = [m.reshape(*sh) for m in (m1, m2)]

        return data, m1, m2
    else:
        return data


@ioh5
def get_motorpos(h5f, scan_no, motor_name):
    return h5f[f"/{scan_no}/instrument/positioners/{motor_name}"][()]


@ioh5
def get_datetime(h5f, scan_no):
    entry = scan_no
    dtime = h5f[f"{entry}/start_time"][()].decode()
    dtime = datetime.fromisoformat(dtime).strftime("%b %d | %H:%M:%S")

    return dtime


@ioh5
def get_command(h5f, scan_no):
    return h5f[f"/{scan_no}/title"][()].decode()


def get_sxdm_frame_sum(path_dset, scan_no, n_threads=None):
    """
    Return the average q-space intensity from a 3D-SXDM measurement.
    The data file `path_dset` is a q-space file produced by XSOCS.
    """

    if n_threads is None:
        ncpu = os.cpu_count()
    else:
        ncpu = n_threads

    indexes = _get_chunk_indexes(path_dset, f"/{scan_no}/instrument/mpx1x4/data", ncpu)
    frame_sum_list = []

    with mp.Pool(processes=ncpu) as p:
        pfun = partial(
            _get_qspace_avg_chunk, path_dset, f"/{scan_no}/instrument/mpx1x4/data"
        )
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
