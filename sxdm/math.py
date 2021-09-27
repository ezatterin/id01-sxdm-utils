import numpy as np

def com2d(row, col, arr, N=100):

    idxs = arr.ravel().argsort()[::-1][:N]
    idxs_int = arr.ravel()[idxs]

    comx, comy = [(pos.ravel()[idxs] * idxs_int).sum() / idxs_int.sum() for pos in (row, col)]

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
    cx, cy, cz = [(arr.ravel()[idxs] * idxs_int).sum() / idxs_int.sum() for arr in (x,y,z)]

    return cx, cy, cz

def ni(arr, val):
    """
    Find the index such that arr[index] is closest to val.
    """
    diff = np.abs(arr-val)
    idx = np.argsort(diff)[0]
    return idx
