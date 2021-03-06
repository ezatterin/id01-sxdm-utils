import h5py
import os

from id01lib.io.utils import ioh5


@ioh5
def list_available_counters(h5f, scan_no):
    return list(h5f[f"{scan_no}/measurement/"].keys())


def _get_chunk_indexes(path_h5, path_in_h5, n_threads=None):
    """
    Return a list of indexes. Each range is a range of integer indexes
    corresponding to a portion of the first dimension of `Data/qspace`
    in `path_h5`. Such portion computed based on `n_threads` for
    efficient parallel computation.
    """

    if n_threads is None:
        ncpu = os.cpu_count()
    else:
        ncpu = n_threads

    with h5py.File(path_h5, "r") as h5f:
        map_shape_flat = h5f[path_in_h5].shape[0]

    chunk_size = map_shape_flat // ncpu
    last_chunk = chunk_size + map_shape_flat % chunk_size

    c0 = [x for x in range(0, map_shape_flat - chunk_size + 1, chunk_size)]
    c1 = [x for x in c0.copy()[1:]]
    c1.append(c1[-1] + last_chunk)

    indexes = list(zip(c0, c1))

    return indexes


def _get_qspace_avg_chunk(path_h5, path_in_h5, indexes):
    """
    Return the q-space intensity array summed over the (flattened) sample positons
    given by `indexes`, which is a list of tuples.
    """

    i0, i1 = indexes
    with h5py.File(path_h5, "r") as h5f:
        chunk = h5f[path_in_h5][i0:i1, ...].sum(0)

    return chunk
