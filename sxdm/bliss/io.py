import numpy as np
import h5py
import os
import multiprocessing as mp

from tqdm.auto import tqdm
from datetime import datetime
from functools import wraps, partial


def ioh5(func):
    @wraps(func)  # to get docstring of dectorated func
    def wrapper(filename, *args, **kwargs):
        with h5py.File(filename, "r") as h5f:
            return func(h5f, *args, **kwargs)

    return wrapper


@ioh5
def get_roidata(h5f, scan_no, roi_name, return_pi_motors=False):
    _entry = scan_no
    _sh = [h5f[_entry][f"technique/{x}"][()] for x in ("dim0", "dim1")]
    _sh = _sh[::-1]
    _command = h5f[f"{_entry}/title"][()].decode()

    data = h5f[_entry][f"measurement/{roi_name}"][()]

    if data.size == _sh[0] * _sh[1]:
        data = data.reshape(*_sh)
    else:
        empty = np.zeros(_sh).flatten()
        empty[: data.size] = data
        data = empty.reshape(*_sh)

    if return_pi_motors:
        m1, m2 = [_command.split(" ")[x][:-1] for x in (1, 5)]
        m1, m2 = [h5f[f"{_entry}/measurement/{m}_position"][()] for m in (m1, m2)]
        m1, m2 = [m.reshape(*_sh) for m in (m1, m2)]

        return data, m1, m2
    else:
        return data


@ioh5
def get_motorpos(h5f, scan_no, motor_name):
    return h5f[f"/{scan_no}/instrument/positioners/{motor_name}"][()]


@ioh5
def get_datetime(h5f, scan_no):
    _entry = scan_no
    _datetime = h5f[f"{_entry}/start_time"][()].decode()
    _datetime = datetime.fromisoformat(_datetime).strftime("%b %d | %H:%M:%S")

    return _datetime


@ioh5
def get_command(h5f, scan_no):
    return h5f[f"/{scan_no}/title"][()].decode()


def _get_qspace_avg_chunk(path_qspace, rang):
    """
    Returns the q-space intensity array summed over the (flattened) sample positons
    given by `rang`.
    """

    i0, i1 = rang
    with h5py.File(path_qspace, "r") as h5f:
        chunk = h5f["Data/qspace"][i0:i1, ...].sum(0)

    return chunk


def get_qspace_avg(path_qspace, n_threads=None):
    """
    Returns the average q-space intensity from a 3D-SXDM measurement.
    The data file `path_qspace` is a q-space file produced by XSOCS.
    """

    if n_threads is None:
        ncpu = os.cpu_count()
    else:
        ncpu = n_threads

    with h5py.File(path_qspace, "r") as h5f:
        map_shape_flat = h5f["Data/qspace"].shape[0]

    chunk_size = map_shape_flat // ncpu
    last_chunk = chunk_size + map_shape_flat % chunk_size

    c0 = [x + 1 for x in range(0, map_shape_flat - chunk_size, chunk_size)]
    c1 = [x for x in range(chunk_size, map_shape_flat - chunk_size, chunk_size)]

    c0[0] = 0
    c0.append(c1[-1] + 1)
    c1.append(c1[-1] + last_chunk)

    ranges = list(zip(c0, c1))
    qspace_avg_list = []

    with mp.Pool(processes=ncpu) as p:
        pfun = partial(_get_qspace_avg_chunk, path_qspace)
        for res in tqdm(p.imap(pfun, ranges), total=len(ranges)):
            qspace_avg_list.append(res)

    qspace_avg = np.stack(qspace_avg_list).sum(0)

    return qspace_avg
