import numpy as np
import h5py
import multiprocessing as mp
import os
import functools

from tqdm.auto import tqdm

from .bliss.io import _get_chunk_indexes


def com2d(row, col, arr, N=100):

    idxs = arr.ravel().argsort()[::-1][:N]
    idxs_int = arr.ravel()[idxs]

    comx, comy = [
        (pos.ravel()[idxs] * idxs_int).sum() / idxs_int.sum() for pos in (row, col)
    ]

    return comx, comy


def ni(arr, val):
    """
    Find the index such that arr[index] is closest to val.
    """
    diff = np.abs(arr - val)
    idx = np.argsort(diff)[0]
    return idx


def convert_coms_qspace(coms, qcoords):
    """
    Works only for 2D COMs at the moment.
    coms : [com_y, com_z]
    qcoords : [qy, qz]
    """

    cy, cz = coms
    qy, qz = qcoords

    cy, cz = [np.round(x, 0).astype("int") for x in (cy, cz)]
    cqy, cqz = qy[cy, cz], qz[cy, cz]

    return cqy, cqz


def ang_between(v1, v2):
    """
    Calculate the angle between vectors contained in two 2D (i,j) arrays.

    Parameters
    ----------
    v1 : numpy.ndarray
        First 2D array of vectors, shape (i, j, 3).
    v2 : numpy.ndarray
        Second 2D array of vectors, shape (i, j, 3).

    Returns
    -------
    out : numpy.ndarray
        2D array of angles, shape (i, j).
    """

    v1a, v2a = [np.linalg.norm(v, axis=2) for v in (v1, v2)]

    out = np.empty(v1.shape[:2])
    for i in range(v1.shape[0]):
        for j in range(v1.shape[1]):
            frac = np.dot(v1[i, j], v2[i, j]) / (v1a[i, j] * v2a[i, j])
            out[i, j] = np.degrees(np.arccos(frac))

    return out


def _calc_com_3d(x, y, z, arr, n_pix=None):
    """x,y,z,arr all have the same shape."""
    arr = arr.ravel()

    # indexes of n_pix most intense pixels of array
    if n_pix is not None:
        idxs = arr.argsort()[::-1][:n_pix]
    else:
        idxs = arr.argsort()[::-1]

    # intensity of such pixels
    arr_idxs = arr[idxs]

    # com
    prob = arr_idxs / arr_idxs.sum()
    cx, cy, cz = [np.sum(prob * q.ravel()[idxs]) for q in (x, y, z)]

    return cx, cy, cz


def _calc_com_qspace3d(path_qspace, idx, mask=None, n_pix=None):
    """
    TODO
    """
    with h5py.File(path_qspace, "r") as h5f:

        qspace_sh = h5f["Data/qspace"].shape[1:]
        if mask is None:
            mask = np.ones(qspace_sh).astype("bool")

        # TODO It should be possible to do it like:
        # row, col, depth = np.where(mask)
        # r0, r1 = row.min(), row.max()
        # c0, c1 = col.min(), col.max()
        # d0, d1 = depth.min(), depth.max()
        # arr = h5f['Data/qspace'][i,  r0:r1, np.unique(col), d0:d1].ravel()
        # but it only works for simple masks right?
        arr = h5f["Data/qspace"][idx][mask]

        # coordinates
        qx, qy, qz = [h5f[f"Data/{x}"][...] for x in "qx,qy,qz".split(",")]
        qxm, qym, qzm = [q[mask] for q in np.meshgrid(qx, qy, qz, indexing="ij")]

        # com
        qcom = _calc_com_3d(qxm, qym, qzm, arr, n_pix=n_pix)

        return qcom


def calc_coms_qspace3d(path_qspace, n_pix=None, mask=None):
    """
    TODO
    """
    with h5py.File(path_qspace, "r") as h5f:
        map_shape_flat = h5f["Data/qspace"].shape[0]

    coms = []
    with mp.Pool(processes=os.cpu_count()) as p:
        _partial_fun = functools.partial(
            _calc_com_qspace3d, path_qspace, mask=mask, n_pix=n_pix
        )
        for res in tqdm(
            p.imap(_partial_fun, range(map_shape_flat)), total=map_shape_flat
        ):
            coms.append(res)

    return np.array(coms).reshape(map_shape_flat, 3).T


def _calc_roi_sum_chunk(path_qspace, indexes, mask=None):
    """
    TODO.
    """

    i0, i1 = indexes
    range_sh = i1 - i0

    with h5py.File(path_qspace, "r") as h5f:
        qspace_sh = h5f["Data/qspace"].shape[1:]

        if mask is None:
            mask = np.ones(qspace_sh).astype("bool")
        mask = (mask[None, ...] * np.ones((range_sh, 1, 1, 1))).astype("bool")

        chunk = h5f["Data/qspace"][i0:i1][mask]
        chunk = chunk.reshape(range_sh, chunk.shape[0] // range_sh).sum(1)

    return chunk


def calc_roi_sum(path_qspace, mask=None, n_threads=None):
    """ "
    Return the sum of local q-space intensity falling within `mask` from
    a 3D-SXDM dataset.
    """

    if n_threads is None:
        ncpu = os.cpu_count()
    else:
        ncpu = n_threads

    idxs = _get_chunk_indexes(path_qspace, ncpu)
    roi_sum_list = []

    with mp.Pool(processes=ncpu) as p:
        pfun = functools.partial(_calc_roi_sum_chunk, path_qspace, mask=mask)
        for res in tqdm(p.imap(pfun, idxs), total=len(idxs)):
            roi_sum_list.append(res)

    return np.concatenate(roi_sum_list)
