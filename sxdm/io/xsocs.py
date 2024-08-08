import numpy as np
import multiprocessing as mp
import h5py

from tqdm.notebook import tqdm
from functools import partial

from .utils import _get_chunk_indexes, _get_qspace_avg_chunk, ioh5


def get_qspace_avg(path_qspace, n_proc=None, mask_direct=None):
    """
    Return the average q-space intensity from a 3D-SXDM measurement.
    The data file `path_qspace` is a q-space file produced by XSOCS.
    """

    with h5py.File(path_qspace, "r") as h5f:
        sh = h5f["Data/qspace"].shape[:1]

    indexes = _get_chunk_indexes(path_qspace, "Data/qspace", n_proc)

    mask = mask_direct.flatten() if mask_direct is not None else np.ones(sh)
    idx_mask = {idx: val for idx, val in zip(np.indices(sh)[0], mask.flatten())}

    qspace_avg_list = []
    with mp.Pool(processes=n_proc) as p:
        pfun = partial(_get_qspace_avg_chunk, path_qspace, "Data/qspace", idx_mask)
        for res in tqdm(p.imap(pfun, indexes), total=len(indexes)):
            qspace_avg_list.append(res)

    qspace_avg = np.stack(qspace_avg_list).sum(0)

    return qspace_avg


@ioh5
def get_piezo_motorpos(h5f):
    """
    h5f is xsocs master file
    """

    _entry0 = list(h5f.keys())[0]

    m0name, m1name = [h5f[f"{_entry0}/scan/motor_{x}"][()].decode() for x in (0, 1)]
    shape_kmap = [h5f[f"{_entry0}/technique/dim{x}"][()] for x in (0, 1)]
    print(f"Returning {m0name},{m1name} of shape {shape_kmap}")

    try:
        m0, m1 = [
            h5f[f"{_entry0}/instrument/positioners/{n}_position"][()].reshape(shape_kmap)
            for n in (m0name, m1name)
        ]
    except KeyError: # new hdf5 format
        m0, m1 = [
            h5f[f"{_entry0}/instrument/positioners/{n}"][()].reshape(shape_kmap)
            for n in (m0name, m1name)
        ]

    return m0, m1
