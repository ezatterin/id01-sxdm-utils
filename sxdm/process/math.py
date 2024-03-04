import numpy as np
import h5py
import multiprocessing as mp
import os
import functools

from tqdm.notebook import tqdm
from xsocs.util import project
from silx.math import fit
from silx.math.fit import fittheories
from numpy.linalg import LinAlgError

from ..io.utils import _get_chunk_indexes
from ..io.bliss import get_detector_aliases


def _gauss_fit_point(path_qspace, roi_slice, rec_axis, qcoords, dir_mask, dir_idx):
    with h5py.File(path_qspace, "r") as h5f:
        local_diffr = h5f["Data/qspace"][dir_idx][roi_slice]

    # load profile
    x, y = qcoords[rec_axis], project(local_diffr)[rec_axis]

    # estimate and subtract background
    bg = fit.snip1d(y, len(y))
    y -= bg

    # guess initial params
    area = y.sum() * (x[-1] - x[0]) / len(x)
    mu = x[y.argmax()]
    fwhm = 2.3 * area / (y.max() * np.sqrt(2 * np.pi))

    # area, centroid, fwhm
    if dir_idx not in np.where(dir_mask.flatten())[0]:
        try:
            params, cov, info = fit.leastsq(
                fit.sum_agauss, x, y, p0=[area, mu, fwhm], full_output=True
            )
        except LinAlgError:
            raise Exception
    else:
        return [0, 0, 0]

    return params


def _gauss_fit_multi_point(path_qspace, roi_slice, rec_axis, qcoords, mask, dir_idx):
    with h5py.File(path_qspace, "r") as h5f:
        local_diffr = h5f["Data/qspace"][dir_idx][roi_slice]

    # load profile
    x, y = qcoords[rec_axis], project(local_diffr)[rec_axis]

    fm = fit.FitManager(x=x, y=y, weight_flag=True)
    fm.loadtheories(fittheories)
    fm.settheory("Area Gaussians")
    fm.setbackground("Strip")

    try:
        fm.estimate()
        fm.runfit()
    except (TypeError, LinAlgError):
        return [0, 0, 0]

    params = []
    for p in fm.fit_results:
        if any([s in p["name"] for s in ("Area", "Position", "FWHM")]):
            params.append(p["fitresult"])

    return params


def gauss_fit(path_qspace, rec_mask, dir_mask=None, multi=False):
    with h5py.File(path_qspace, "r") as h5f:
        dir_idxs = range(h5f["Data/qspace"].shape[0])
        qx, qy, qz = [h5f[f"Data/{x}"][...] for x in "qx,qy,qz".split(",")]

    roi_slice = tuple([slice(x.min(), x.max() + 1) for x in np.where(~rec_mask)])
    roi_qcoords = [q[roi_slice] for q in np.meshgrid(qx, qy, qz, indexing="ij")]
    qcoords = roi_qcoords[0][:, 0, 0], roi_qcoords[1][0, :, 0], roi_qcoords[2][0, 0, :]

    dir_mask = dir_mask if dir_mask is not None else np.zeros((dir_idxs.stop,))

    fits_free = {key: None for key in ("qx", "qy", "qz")}
    axidx = {0: "qx", 1: "qy", 2: "qz"}

    with mp.Pool(os.cpu_count()) as pool:
        for rec_axis in (0, 1, 2):
            fitls = []
            fun = _gauss_fit_point if not multi else _gauss_fit_multi_point

            pfun = functools.partial(
                fun, path_qspace, roi_slice, rec_axis, qcoords, dir_mask
            )

            for i, res in zip(dir_idxs, pool.imap(pfun, dir_idxs)):
                fitls.append(res)
                if i % 500 == 0:
                    print(
                        f"\r{axidx[rec_axis]}: {i}/{dir_idxs.stop}", end="", flush=True
                    )
            print("\n")
            fits_free[axidx[rec_axis]] = fitls

    return fits_free


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


def calc_com_2d(arr, x, y, n_pix=None, std=False):
    """
    Compute the centre of mass (COM) of an indexed 2D array.

    Parameters
    ----------
    arr : numpy.ndarray
        2D array of intensity values.
    x, y : numpy.ndarray
        2D arrays whose entries correspond to the coordinates of `arr` along each
        axis.
    n_pix: int, optional
        Restrict the computation of the COM for the `n_pix` strongest (most intense)
        pixels in the 2D q-space array.
    std: bool, optional
        Calculates the standard deviation of COMx, COMy.

    Returns
    -------
    out : tuple
        Coordinates of the COM of `arr` expressed within `x`, `y`, coordinates
        If std=True returns COM and stderr of `arr` expressed as `x`, `y`,`stdx`,
        `stdy
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
    cx, cy = [np.sum(prob * q.ravel()[idxs]) for q in (x, y)]
    if std is True:
        stdx, stdy = [
            np.sqrt(np.sum(prob * (q.ravel()[idxs] - com) ** 2))
            for q, com in zip((x, y), (cx, cy))
        ]
        return cx, cy, stdx, stdy
    else:
        return cx, cy


def calc_com_3d(arr, x, y, z, n_pix=None, std=False):
    """
    Compute the centre of mass (COM) of an indexed 3D or 2D array.

    Parameters
    ----------
    arr : numpy.ndarray
        3D or 2D array of intensity values.
    x, y, z : numpy.ndarray
        3D or 2D arrays whose entries correspond to the coordinates of `arr` along each
        axis.
    n_pix: int, optional
        Restrict the computation of the COM for the `n_pix` strongest (most intense)
        pixels in the 3D q-space array.
    std: bool, optional
        Calculates the standard deviation of COMx, COMy, COMz. Useful to check in
        2D d-spacing distribution maps whether or not you might have strained less
        strained areas in x, y, z

    Returns
    -------
    out : tuple
        Coordinates of the COM of `arr` expressed within `x`, `y`, `z` coordinates
        If std=True returns COM and stderr of `arr` expressed as `x`, `y`, `z`,`stdx`,
        `stdy`, `stdz`.
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
    if std is True:
        stdx, stdy, stdz = [
            np.sqrt(np.sum(prob * (q.ravel()[idxs] - com) ** 2))
            for q, com in zip((x, y, z), (cx, cy, cz))
        ]
        return cx, cy, cz, stdx, stdy, stdz
    else:
        return cx, cy, cz


def _calc_com_qspace3d(path_qspace, mask_reciprocal, idx, n_pix=None, std=False):
    """
    Compute the center of mass (COM) of an XSOCS 4D q-space array in q-space
    coordinates at position `idx`.

    Parameters
    ----------
    path_qspace : str
        Path to the XSOCS q-space file.
    mask_reciprocal : numpy.ndarray
        3D boolean array. True for portions *not* to be considered.
    idx : int
        Index of the first dimension of the 4D q-space array, i.e. the index of
        the sample position at which the 3D q-space volume was measured.
    n_pix : int, optional
        Restrict the computation of the COM for the `n_pix` strongest pixels in the 3D
        q-space array.
    std : bool, optional
        Calculates the standard deviation of COMx, COMy, COMz. Useful to check in 2D
                d-spacing distribution maps
        whether or not you might have strained/less strained areas in x, y, z
    Returns
    -------
    out : tuple
        Coordinates of the q-space COM at position `idx`.
    """

    # indexes of saught data
    roi_rec = np.where(np.invert(mask_reciprocal))

    # check if mask is cube-like or more complicated,
    # will determine how array is retrieved from hdf5 file
    mask_size_cube = np.prod([x.max() + 1 - x.min() for x in roi_rec])
    mask_size_real = np.count_nonzero(np.invert(mask_reciprocal))

    # if mask is cube-like use these
    roi_rec_sl = tuple([slice(x.min(), x.max() + 1) for x in roi_rec])
    roi = (idx, *roi_rec_sl)

    with h5py.File(path_qspace, "r") as h5f:
        # data sliced straight from hdf5 OR,
        # data loaded to mem at idx and then fancy sliced
        if mask_size_cube == mask_size_real:
            arr = h5f["Data/qspace"][roi]
        # NOTE this will fail if the smallest rec space dimensions is not the 
        # first one!
        else: 
            arr = h5f["Data/qspace"][idx][roi_rec]

        # retrieve q-space coordinates
        qx, qy, qz = [h5f[f"Data/{x}"][...] for x in "qx,qy,qz".split(",")]
        qxm, qym, qzm = [q[roi_rec] for q in np.meshgrid(qx, qy, qz, indexing="ij")]

        # compute COM and standard deviation
        if std is True: 
            cx, cy, cz, stdx, stdy, stdz = calc_com_3d(
                arr, qxm, qym, qzm, n_pix=n_pix, std=True
            )
            return cx, cy, cz, stdx, stdy, stdz
        else:
            cx, cy, cz = calc_com_3d(arr, qxm, qym, qzm, n_pix=n_pix, std=False)
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
    If std=True
    cx, cy, cz, stdx, stdy, stdz: numpy.ndarray
        Coordinates of the q-space COM plus their relative standard deviation.
    """
    if type(mask_reciprocal) is not np.ndarray or len(mask_reciprocal.shape) < 3:
        raise TypeError("mask_reciprocal has to be a 3D numpy array")

    with h5py.File(path_qspace, "r") as h5f:
        map_shape_flat = h5f["Data/qspace"].shape[0]

    if std is True:
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


def _calc_roi_sum_chunk(path_qspace, mask_reciprocal, mask_direct, idx_range):
    """
    Calculate the intensity of a 5D qspace dataset:
    * for the direct space indexes in the range `idx_range`;
    * within the reciprocal space slice `roi_rec_sl`;
    * masked in direct space where `mask_direct` is True.

    Returns a `numpy.masked_array`.
    """
    i0, i1 = idx_range
    sh0 = i1 - i0
    
    # indexes of saught data 
    roi_rec_idxs = np.where(np.invert(mask_reciprocal))
    roi_idxs = np.where(np.invert(np.stack([mask_reciprocal.flatten()]*sh0, axis=0)))

    # slices of saught data
    roi_rec_sl = tuple([slice(x.min(), x.max() + 1) for x in roi_rec_idxs])
    roi_sl = (slice(i0, i1, None), *roi_rec_sl)
    
    # check if mask is cube-like or more complicated,
    # will determine how array is retrieved from hdf5 file
    mask_size_cube = np.prod([x.max() + 1 - x.min() for x in roi_rec_idxs])
    mask_size_real = np.count_nonzero(np.invert(mask_reciprocal))
    
    with h5py.File(path_qspace, "r") as h5f:
        # slice full 4D array directly
        if mask_size_cube == mask_size_real:
            arr = h5f["Data/qspace"][roi_sl].sum(axis=(1, 2, 3))
        # first send sub array to memory, then index flattened 3D
        else:
            arr = h5f["Data/qspace"][i0:i1,...]
            arr = arr.reshape(sh0, mask_reciprocal.size)[roi_idxs]
            arr = arr.reshape(sh0, roi_rec_idxs[0].shape[0]).sum(1)

    return np.ma.masked_where(mask_direct[i0:i1], arr)


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

    # direct space mask
    mask_dir = mask_direct.flatten() if mask_direct is not None else np.zeros(sh)

    pfun = functools.partial(
        _calc_roi_sum_chunk, path_qspace, mask_reciprocal, mask_dir
    )
    roi_sum_list = []
    with mp.Pool(processes=n_proc) as p:
        for res in tqdm(p.imap(pfun, idxs_list), total=len(idxs_list)):
            roi_sum_list.append(res)

    return np.ma.concatenate(roi_sum_list)


def _calc_com_idx(path_h5, path_in_h5, mask_idxs, qx, qy, qz, idx_list, **kwargs):
    with h5py.File(path_h5, "r") as h5f:
        i0, i1 = idx_list

        roi = (slice(i0, i1, None), *mask_idxs)
        frames = h5f[path_in_h5][roi]

        coms = [calc_com_3d(frame, qx, qy, qz, **kwargs) for frame in frames]

    return coms


def calc_coms_qspace2d(
    path_dset,
    scan_no,
    qx,
    qy,
    qz,
    mask_rec=None,
    n_threads=None,
    detector="mpx1x4",
    n_pix=None,
    std=None,
):
    
    """
    Calculate center of masses (COMs) in reciprocal space for a 4D SXDM scan.
    """
 
    detlist = get_detector_aliases(path_dset, scan_no)
    if detector not in detlist:
        raise ValueError(
            f"Detector {detector} not in data file. Available detectors are: {detlist}."
        )
    else:
        path_data_h5 = f"/{scan_no}/instrument/{detector}/data"

        if n_threads is None:
            ncpu = os.cpu_count()
        else:
            ncpu = n_threads

        with h5py.File(path_dset, "r") as h5f:
            mask_sh = h5f[path_data_h5].shape[1:]

        idx_list = _get_chunk_indexes(path_dset, path_data_h5, n_threads=n_threads)

        mask = np.invert(mask_rec) if mask_rec is not None else np.ones(mask_sh)
        mask_idxs = tuple([slice(x.min(), x.max() + 1) for x in np.where(mask)])

        coms = []
        pfun = functools.partial(
            _calc_com_idx,
            path_dset,
            path_data_h5,
            mask_idxs,
            qx,
            qy,
            qz,
            n_pix=n_pix,
            std=std,
        )
        with mp.Pool(processes=ncpu) as p:
            for res in tqdm(p.imap(pfun, idx_list), total=len(idx_list)):
                coms.append(res)

        coms = [x for y in coms for x in y]
        comsarr = np.stack(coms)

        return comsarr
