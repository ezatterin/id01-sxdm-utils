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


def _calc_com_3d(arr, x, y, z, n_pix=None, std=False):
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
    if std == True:
        stdx, stdy, stdz = [np.sqrt(np.sum(prob ** 2))*np.std(prob * q.ravel()[idxs]) for q in (x, y, z)]
        return cx, cy, cz, stdx, stdy, stdz
    else:
        return cx, cy, cz

def _calc_com_qspace3d(path_qspace, mask_reciprocal, idx, n_pix=None,std=False):
    """
    Compute the center of mass (COM) of an XSOCS 4D q-space array in q-space
    coordinates at position `idx`.

    Parameters
    ----------
    path_qspace : str
        Path to the XSOCS q-space file.
    mask_reciprocal : numpy.ndarray
        3D boolean array. True for portions *not* to be considered. NOTE: for the
        moment this works only for contiguous subarrays of the reciprocal space
        volume; that is, only "cube-like" masks are supported.
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

    # recipocal space slice from mask
    roi_rec = np.where(np.invert(mask_reciprocal))
    roi_rec_sl = tuple([slice(x.min(), x.max() + 1) for x in roi_rec])

    with h5py.File(path_qspace, "r") as h5f:

        roi = (idx, *roi_rec_sl)
        arr = h5f["Data/qspace"][roi]

        # coordinates
        qx, qy, qz = [h5f[f"Data/{x}"][...] for x in "qx,qy,qz".split(",")]
        qxm, qym, qzm = [q[roi_rec_sl] for q in np.meshgrid(qx, qy, qz, indexing="ij")]

        # com
        if std == True:
            cx, cy, cz, stdx, stdy, stdz = _calc_com_3d(arr, qxm, qym, qzm, n_pix=n_pix, std=True)
            return cx, cy, cz, stdx, stdy, stdz              
        else:
            cx, cy, cz = _calc_com_3d(arr, qxm, qym, qzm, n_pix=n_pix, std=False)
            return cx, cy, cz

def calc_coms_qspace3d(path_qspace, mask_reciprocal, n_pix=None, std=False):
    """
    Compute the center of mass (COM) of an XSOCS 4D array for each direct space
    position. The 4D array is Intensity(direct_space_position, qx, qy, qz).

    Parameters
    ----------
    path_qspace : str
        Path to the XSOCS q-space file.
    mask_reciprocal : numpy.ndarray
        3D boolean array. True for portions *not* to be considered. NOTE: for the
        moment this works only for contiguous subarrays of the reciprocal space
        volume; that is, only "cube-like" masks are supported.
    n_pix : int, optional
        Restrict the computation of the COM for the `n_pix` strongest pixels in the
        3D q-space array.

    Returns
    -------
    cx, cy, cz : numpy.ndarray
        Coordinates of the q-space COM for each direct space position.
    """
    if type(mask_reciprocal) is not np.ndarray or len(mask_reciprocal.shape) < 3:
        raise TypeError('mask_reciprocal has to be a 3D numpy array')

    with h5py.File(path_qspace, "r") as h5f:
        map_shape_flat = h5f["Data/qspace"].shape[0]

    if std == True:
        coms = []
        with mp.Pool(processes=os.cpu_count()) as p:
            _partial_fun = functools.partial(
                _calc_com_qspace3d, path_qspace, mask_reciprocal, n_pix=n_pix, std=True
            )
            for res in tqdm(
                p.imap(_partial_fun, range(map_shape_flat)), total=map_shape_flat
            ):
                coms.append(res)
        cx, cy, cz, stdx, stdy, stdz = np.array(coms).reshape(map_shape_flat, 6).T
        return cx, cy, cz, stdx, stdy, stdz
    else:
        coms = []
        with mp.Pool(processes=os.cpu_count()) as p:
            _partial_fun = functools.partial(
                _calc_com_qspace3d, path_qspace, mask_reciprocal, n_pix=n_pix
            )
            for res in tqdm(
                p.imap(_partial_fun, range(map_shape_flat)), total=map_shape_flat
            ):
                coms.append(res)
        cx, cy, cz = np.array(coms).reshape(map_shape_flat, 3).T
        return cx, cy, cz


def _calc_roi_sum_chunk(path_qspace, roi_rec_sl, mask_direct, idx_range):
    """
    Calculate the intensity of a 5D qspace dataset:
    * for the direct space indexes in the range `idx_range`;
    * within the reciprocal space slice `roi_rec_sl`;
    * masked in direct space where `mask_direct` is True.

    Returns a `numpy.masked_array`.
    """
    i0, i1 = idx_range

    roi_slice = (slice(i0, i1, None), *roi_rec_sl)
    mask_dir_range = mask_direct[i0:i1]

    with h5py.File(path_qspace, "r") as h5f:
        arr = h5f["Data/qspace"][roi_slice].sum(axis=(1, 2, 3))

    return np.ma.masked_where(mask_dir_range, arr)


def calc_roi_sum(path_qspace, mask_reciprocal, mask_direct=None, n_proc=None):
    """
    Calculate the intensity in direct space integrated within `mask_reciprocal`
    for the 5D SXDM dataset contained in `path_qspace` (as "Data/qspace").

    Parameters
    ----------
    path_qspace : str
        Path to the XSOCS q-space file.
    mask_reciprocal : numpy.ndarray
        3D boolean array. True for portions *not* to be considered. NOTE: for the
        moment this works only for contiguous subarrays of the reciprocal space
        volume; that is, only "cube-like" masks are supported.
    mask_direct : numpy.ndarray
        2D boolean array. True for portions *not* to be considered. 
    n_proc : int, optional
        Number of processes to spawn. Defaults to the number of logical machine cores.

    Returns
    -------
    roi_sum : numpy.ma.core.MaskedArray
    """

    if n_proc is None:
        n_proc = os.cpu_count()

    # direct space shape (1D)
    with h5py.File(path_qspace, "r") as h5f:
        sh = h5f["Data/qspace"].shape[:1]

    # list of idx ranges [(i0, i1), (i0, i1), ...]
    idxs_list = _get_chunk_indexes(path_qspace, "Data/qspace", n_threads=n_proc)

    # recipocal space slice from mask
    roi_rec = np.where(np.invert(mask_reciprocal))
    roi_rec_sl = tuple([slice(x.min(), x.max() + 1) for x in roi_rec])

    # direct space mask
    mask_dir = mask_direct.flatten() if mask_direct is not None else np.zeros(sh)

    pfun = functools.partial(_calc_roi_sum_chunk, path_qspace, roi_rec_sl, mask_dir)
    roi_sum_list = []
    with mp.Pool(processes=n_proc) as p:
        for res in tqdm(p.imap(pfun, idxs_list), total=len(idxs_list)):
            roi_sum_list.append(res)

    return np.ma.concatenate(roi_sum_list)
