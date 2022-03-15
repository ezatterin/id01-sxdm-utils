import numpy as np
import h5py

from datetime import datetime
from functools import wraps

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