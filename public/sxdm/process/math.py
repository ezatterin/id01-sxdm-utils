import numpy as np
import h5py
import multiprocessing as mp
import os
import functools

from tqdm.auto import tqdm

from ..io.utils import _get_chunk_indexes


def get_nearest_index(arr, val):
    """
    Find the `index` such that `arr[index]` is closest to `val`.
    """
    diff = np.abs(arr - val)
    idx = np.argsort(diff)[0]
    return idx


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


def _calc_com_3d(arr, x, y, z, n_pix=None):
    """
    Compute the centre of mass (COM) of an indexed 3D array.

    Parameters
    ----------
    arr : numpy.ndarray
        3D array of intensity values.
    x, y, z : numpy.ndarray
        3D arrays whose entries correspond to the coordinates of `arr` along each
        axis.

    Returns
    -------
    out : tuple
        Coordinates of the COM of `arr` expressed within `x`, `y`, `z` coordinates.
    """
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


def _calc_com_qspace3d(path_qspace, roi_slice, idx, n_pix=None):
    """
    Compute the center of mass (COM) of an XSOCS 4D q-space array in q-space
    coordinates at position `idx`.

    Parameters
    ----------
    path_qspace : str
        Path to the XSOCS q-space file.
    roi_slice :
    idx : int
        Index of the first dimension of the 4D q-space array, i.e. the index of
        the sample position at which the 3D q-space volume was measured.
    n_pix : int, optional
        Restrict the computation of the COM for the `n_pix` strongest pixels in the
        3D q-space array.

    Returns
    -------
    out : tuple
        Coordinates of the q-space COM at position `idx`.
    """
    with h5py.File(path_qspace, "r") as h5f:

        roi = (idx, *roi_slice)
        arr = h5f["Data/qspace"][roi]

        # coordinates
        qx, qy, qz = [h5f[f"Data/{x}"][...] for x in "qx,qy,qz".split(",")]
        qxm, qym, qzm = [q[roi_slice] for q in np.meshgrid(qx, qy, qz, indexing="ij")]

        # com
        cx, cy, cz = _calc_com_3d(arr, qxm, qym, qzm, n_pix=n_pix)

        return cx, cy, cz


def calc_coms_qspace3d(path_qspace, roi_slice, n_pix=None):
    """
    Compute the center of mass (COM) of an XSOCS 4D array for each direct space
    position. The 4D array is Intensity(direct_space_position, qx, qy, qz).

    Parameters
    ----------
    path_qspace : str
        Path to the XSOCS q-space file.
    roi_slice : 
    n_pix : int, optional
        Restrict the computation of the COM for the `n_pix` strongest pixels in the
        3D q-space array.

    Returns
    -------
    cx, cy, cz : numpy.ndarray
        Coordinates of the q-space COM for each direct space position.
    """
    with h5py.File(path_qspace, "r") as h5f:
        map_shape_flat = h5f["Data/qspace"].shape[0]

    coms = []
    with mp.Pool(processes=os.cpu_count()) as p:
        _partial_fun = functools.partial(
            _calc_com_qspace3d, path_qspace, roi_slice, n_pix=n_pix
        )
        for res in tqdm(
            p.imap(_partial_fun, range(map_shape_flat)), total=map_shape_flat
        ):
            coms.append(res)

    cx, cy, cz = np.array(coms).reshape(map_shape_flat, 3).T

    return cx, cy, cz


def _calc_roi_sum_chunk(path_qspace, roi_slice, idx_range):
    """
    TODO
    """
    roi_mask = (slice(idx_range[0], idx_range[1], None) , *roi_slice)
    with h5py.File(path_qspace, 'r') as h5f:
        return h5f['Data/qspace'][roi_mask].sum(axis=(1,2,3))


def calc_roi_sum(path_qspace, roi_slice, n_proc=None):
    """
    TODO
    """

    if n_proc is None:
        n_proc = os.cpu_count()

    idxs = _get_chunk_indexes(path_qspace, "Data/qspace", n_threads=n_proc)
    pfun = functools.partial(_calc_roi_sum_chunk, path_qspace, roi_slice)
    
    roi_sum_list = []
    with mp.Pool(processes=n_proc) as p:
        for res in tqdm(p.imap(pfun, idxs), total=len(idxs)):
            roi_sum_list.append(res)

    return np.concatenate(roi_sum_list)
