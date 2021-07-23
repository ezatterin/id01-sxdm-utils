import numpy as np

def com2d(row, col, arr, N=100):
    
    idxs = arr.ravel().argsort()[::-1][:N]
    idxs_int = arr.ravel()[idxs]
    
    comx, comy = [(pos.ravel()[idxs] * idxs_int).sum() / idxs_int.sum() for pos in (row, col)]
     
    return comx, comy

def ni(arr, val):
    """
    Find the index such that arr[index] is closest to val.
    """
    diff = np.abs(arr-val)
    idx = np.argsort(diff)[0]
    return idx