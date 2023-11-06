import h5py
import os

from id01lib.io.bliss import ioh5


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

    with h5py.File(path_h5, "r") as h5f:
        map_shape_flat = h5f[path_in_h5].shape[0]

    if n_threads is None:
        ncpu = os.cpu_count()
    elif n_threads == 1:
        return [(0, map_shape_flat)]
    else:
        ncpu = n_threads

    chunk_size = map_shape_flat // ncpu
    last_chunk = chunk_size + map_shape_flat % chunk_size

    c0 = [x for x in range(0, map_shape_flat - chunk_size + 1, chunk_size)]
    c1 = [x for x in c0.copy()[1:]]
    c1.append(c1[-1] + last_chunk)

    indexes = list(zip(c0, c1))

    return indexes


def _get_chunk_indexes_detector(path_h5, path_in_h5, n_chunks=3, roi=None):
    """
    Return a list of indexes. Each range is a range of integer indexes
    corresponding to a portion of the first dimension of `Data/qspace`
    in `path_h5`. Such portion computed based on `n_threads` for
    efficient parallel computation.
    """

    with h5py.File(path_h5, "r") as h5f:
        if roi is None:
            det_shape = h5f[path_in_h5].shape[1:]
            roi = [0, det_shape[0], 0, det_shape[1]]
        else:
            det_shape = (roi[1] - roi[0], roi[3] - roi[2])

    if n_chunks is None:
        n_chunks = os.cpu_count()
    elif n_chunks == 1:
        return [(0, det_shape[0], det_shape[1])]

    chunk_size = [d // n_chunks for d in det_shape]

    idxs = []
    for c, d, r in zip(chunk_size, det_shape, [roi[:2], roi[2:]]):
        c0 = [x for x in range(r[0], r[1] - c + 1, c)]
        c1 = [x for x in c0.copy()[1:]]
        c1.append(c1[-1] + (c + d % c))

        indexes = list(zip(c0, c1))
        idxs.append(indexes)

    return idxs


def _get_qspace_avg_chunk(path_h5, path_in_h5, idx_mask, idx_range):
    """
    Return the q-space intensity array summed over the (flattened) sample positons
    given by `idx_range`, which is a list of tuples.
    """

    idx_list = [x for x in range(*idx_range, 1) if idx_mask[x].astype("bool") == True]
    with h5py.File(path_h5, "r") as h5f:
        chunk = h5f[path_in_h5][idx_list, ...].sum(0)

    return chunk
