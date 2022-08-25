import h5py
import os
import numpy as np

from id01lib.io.utils import ioh5


@ioh5
def list_available_counters(h5f, scan_no):
    return list(h5f[f"{scan_no}/measurement/"].keys())


def _get_chunk_indexes(path_h5, path_in_h5, n_threads=None, real_space_mask=None):
    """
    Return a list of indexes. Each range is a range of integer indexes
    corresponding to a portion of the first dimension of `Data/qspace`
    in `path_h5`. Such portion computed based on `n_threads` for
    efficient parallel computation.
    """

    with h5py.File(path_h5, "r") as h5f:
        map_shape_flat = h5f[path_in_h5].shape[0]
    
    if n_threads is None:
        ncpu = os.cpu_count()
    elif n_threads == 1:
        return [(0, map_shape_flat)]
    else:
        ncpu = n_threads

    if real_space_mask is not None:
        all_masked_indexes=np.arange(0,map_shape_flat)[np.invert(np.array(real_space_mask).flatten())]
        map_shape_flat = map_shape_flat - np.sum(real_space_mask)
    else:
        all_masked_indexes=np.arange(0,map_shape_flat)

    chunk_size = map_shape_flat // ncpu
    last_chunk = chunk_size + map_shape_flat % chunk_size

    c0 = [x for x in range(0, map_shape_flat - chunk_size + 1, chunk_size)]
    c1 = [x for x in c0.copy()[1:]]
    c1.append(c1[-1] + last_chunk)

    indexes = list(zip(c0, c1))

    return (indexes, all_masked_indexes)


def _get_qspace_avg_chunk(path_h5, path_in_h5, all_masked_indexes, indexes):
    """
    Return the q-space intensity array summed over the (flattened) sample positons
    given by `indexes`, which is a list of tuples.
    """

    i0, i1 = indexes
    with h5py.File(path_h5, "r") as h5f:
        chunk = h5f["Data/qspace"][all_masked_indexes[i0:i1], ...].sum(0)

    return chunk
