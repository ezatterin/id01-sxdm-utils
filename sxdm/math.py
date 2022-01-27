import numpy as np


def com2d(row, col, arr, N=100):

    idxs = arr.ravel().argsort()[::-1][:N]
    idxs_int = arr.ravel()[idxs]

    comx, comy = [
        (pos.ravel()[idxs] * idxs_int).sum() / idxs_int.sum() for pos in (row, col)
    ]

    return comx, comy


def com3d(x, y, z, arr, N=None):
    """x,y,z,arr all have the same shape."""

    # indexes of N most intense pixels of array
    if N is not None:
        idxs = arr.ravel().argsort()[::-1][:N]
    else:
        idxs = arr.ravel().argsort()[::-1]

    # intensity of such pixels
    idxs_int = arr.ravel()[idxs]

    # calculate com
    cx, cy, cz = [
        (arr.ravel()[idxs] * idxs_int).sum() / idxs_int.sum() for arr in (x, y, z)
    ]

    return cx, cy, cz


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

    v1a, v2a = [np.linalg.norm(v, axis=2) for v in (v1,v2)]

    out = np.empty(v1.shape[:2])
    for i in range(v1.shape[0]):
        for j in range(v1.shape[1]):
            frac = np.dot(v1[i,j], v2[i,j]) / (v1a[i,j]*v2a[i,j])
            out[i, j] = np.degrees(np.arccos(frac))
            
    return out
