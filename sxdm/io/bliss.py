import numpy as np
import multiprocessing as mp
import os
import h5py
import ipywidgets as ipw

from tqdm.notebook import tqdm
from functools import partial
from datetime import datetime

from id01lib.io.bliss import ioh5
from id01lib.io.bliss import (
    get_command,
    get_counter,
    get_positioner,
    get_detector_aliases,
    get_scan_shape,
    get_roi_names,
    _check_detector,
)

from .utils import _get_chunk_indexes


@ioh5
def get_sxdm_scan_numbers(h5f, interrupted_scans=False):
    scan_nos = []
    for entry in list(h5f.keys()):
        command = h5f[f"{entry}/title"][()].decode()
        if any([s in command for s in ("sxdm", "mesh", "kmap")]):
            if not interrupted_scans:
                try:
                    h5f[entry]["measurement"]
                    scan_nos.append(entry)
                except KeyError:
                    pass
            else:
                scan_nos.append(entry)

    scan_nos.sort(key=lambda s: int(s.split(".")[0]))
    scan_nos = [s for s in scan_nos if not s.endswith(".2")]

    return scan_nos


@ioh5
def get_datetime(h5f, scan_no):
    scan_no = scan_no
    dtime = h5f[f"{scan_no}/start_time"][()].decode()
    dtime = datetime.fromisoformat(dtime).strftime("%b %d | %H:%M:%S")

    return dtime


@ioh5
def get_detcalib(h5f, scan_no):
    params = dict(beam_energy=0, center_chan=[], chan_per_deg=[])
    calib = h5f[f"{scan_no}/instrument/detector"]

    for key in params.keys():
        if key == "beam_energy":
            params[key] = calib[key][()]
        else:
            params[key] = [calib[f"{key}_dim{i}"][()] for i in (0, 1)]

    return params


def get_piezo_motor_names(h5f, scan_no):
    command = get_command(h5f, scan_no)
    if any([x in command for x in ("sxdm", "kmap", "mesh")]):
        m1_name, m2_name = [command.split(" ")[x] for x in (1, 5)]
        if "," in m1_name:
            m1_name, m2_name = m1_name[:-1], m2_name[:-1]
    else:
        fname = os.path.basename(h5f)
        msg = f"Scan {scan_no} in {fname} is not a mesh or an sxdm scan!"
        raise Exception(msg)

    return m1_name, m2_name


def get_piezo_motor_positions(h5f, scan_no):
    """Retrieve the sample coordinates of an SXDM scan.

    Parameters
    ----------
    h5f : str
        Path to the .hdf5 BLISS dataset.
    scan_no : str
        Number of the SXDM scan, e.g. 4.1.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        The coordinates of the two motors of the piezoelectric stage as 2D NumPy
        arrays.
    """
    sh = get_scan_shape(h5f, scan_no)
    m1n, m2n = get_piezo_motor_names(h5f, scan_no)

    try:  # sxdm
        m1, m2 = [get_positioner(h5f, scan_no, f"{m}_position") for m in (m1n, m2n)]
    except KeyError:  # mesh
        m1, m2 = [get_positioner(h5f, scan_no, m) for m in (m1n, m2n)]
    m1, m2 = [m.reshape(*sh) for m in (m1, m2)]

    return m1, m2


def get_roidata(h5f, scan_no, roi_name, return_pi_motors=False):
    """
    DEPRECATED. Use get_counter_sxdm instead.
    """
    return get_counter_sxdm(h5f, scan_no, roi_name, return_pi_motors=return_pi_motors)


def get_counter_sxdm(h5f, scan_no, counter, return_pi_motors=False):
    """
    Retrieve counter data for a specific counter from an SXDM scan.

    Parameters
    ----------
    h5f : str
        Path to the HDF5 BLISS dataset containing the SXDM data.
    scan_no : str
        The scan number for the SXDM scan, e.g. 1.1.
    counter : str
        The name of the counter for which the data is retrieved.
    return_pi_motors : bool, optional
        If True, also return the positions of the piezo motors (m1, m2) associated
        with the scan. Default is False.

    Returns
    -------
    np.ndarray or Tuple[np.ndarray, float, float]
        If return_pi_motors is False:
            The counter data for the specified counter, reshaped to match the
            scan shape.
        If return_pi_motors is True:
            A tuple containing:
            - The counter data for the specified counter, reshaped to match the
            scan shape.
            - The position of piezo motor m1.
            - The position of piezo motor m2.
    """

    sh = get_scan_shape(h5f, scan_no)
    data = get_counter(h5f, scan_no, counter)

    if data.size == sh[0] * sh[1]:
        data = data.reshape(*sh)
    else:
        empty = np.zeros(sh).flatten()
        empty[: data.size] = data
        data = empty.reshape(*sh)

    if return_pi_motors:
        m1, m2 = get_piezo_motor_positions(h5f, scan_no)
        return data, m1, m2
    else:
        return data


def _get_frames_chunk(path_dset, path_in_h5, roi_dir_idxs, roi, idx_range):
    """
    Return the q-space intensity array summed over the (flattened) sample positons
    given by `idx_range`, which is a list of tuples.
    """
    idx_list = [x for x in range(*idx_range, 1) if x in roi_dir_idxs]
    if roi is not None:
        roi_sl = np.s_[idx_list, roi[0] : roi[1], roi[2] : roi[3]]
    else:
        roi_sl = np.s_[idx_list, ...]

    with h5py.File(path_dset, "r") as h5f:
        arr = h5f[path_in_h5][roi_sl].sum(0)

    return arr


def get_sxdm_frame_sum(
    path_dset,
    scan_no,
    mask_sample=None,
    detector=None,
    n_proc=None,
    pbar=True,
    path_data_h5="/{scan_no}/instrument/{detector}/data",
    roi=None,
):
    """Return the sum of all detector frames collected within an SXDM scan.


    Parameters
    ----------
    path_dset : str
        Path to the .hdf5 BLISS dataset.
    scan_no : str
        Number of the SXDM scan, e.g. 4.1.
    mask_sample : np.ndarray, optional
        Array of the same shape as the SXDM scan whose True values indicate
        where to perform the frame sum, by default None (all the scanned area is
        considered in the computation)
    detector : str, optional
        The detector used for the SXDM scan, by default None
    n_proc : int, optional
        Number of processes to spawn for parallel computation, by default None
    pbar : bool, optional
        Spawn a process bar, by default True
    path_data_h5 : str, optional
        Path within the .hdf5 BLISS dataset where to look for the raw data,
        by default "/{scan_no}/instrument/{detector}/data"
    roi : list, optional
        List of [row_min, row_max, col_min, col_max], by default None

    Returns
    -------
    np.ndarray
        Sum of all detector frames collected as part of a single SXDM scan.

    Raises
    ------
    ValueError
        The specified detector is not contained in the .hdf5 dataset.
    """

    detlist = get_detector_aliases(path_dset, scan_no)
    if detector is None:
        detector = detlist[0]
    if detector not in detlist:
        raise ValueError(
            f"Detector {detector} not in data file. Available detectors are: {detlist}."
        )
    else:
        path_data_h5 = path_data_h5.format(scan_no=scan_no, detector=detector)

        if n_proc is None:
            n_proc = os.cpu_count()

        # list of idx ranges [(i0, i1), (i0, i1), ...]
        indexes = _get_chunk_indexes(path_dset, path_data_h5, n_proc)

        # direct space shape (1D)
        with h5py.File(path_dset, "r") as h5f:
            sh = h5f[path_data_h5].shape[0]

        # direct space slice from mask
        if mask_sample is not None:
            roi_dir_idxs = np.where(np.invert(mask_sample).flatten())[0]
        else:
            roi_dir_idxs = np.indices((sh,))[0]

        pfun = partial(_get_frames_chunk, path_dset, path_data_h5, roi_dir_idxs, roi)

        # set progress bar
        if pbar is True:
            pbar = tqdm()
        elif isinstance(pbar, tqdm):
            pbar.total = len(indexes)
            pbar.refresh()

        # apply partial function multi process, with an index range per process
        frame_sum_list = []
        try:
            pbar.reset(total=len(indexes))
        except AttributeError:
            pass
        with mp.Pool(processes=n_proc) as p:
            for res in p.imap(pfun, indexes):
                frame_sum_list.append(res)
                try:
                    pbar.update()
                    pbar.refresh()
                except AttributeError:  # pbar=False
                    pass

        if pbar:
            pbar.close()

        return np.stack(frame_sum_list).sum(0)


def _calc_pos_sum_chunk(path_dset, path_in_h5, roi_rec_sl, idx_range):
    """
    Calculate the direct space intensity of a 4D SXDM dataset:
    * for the direct space indexes in the range `idx_range`;
    * within the reciprocal space slice `roi_rec_sl`;
    * masked in direct space where `mask_direct` is True.

    Returns a `numpy.masked_array`.
    """
    i0, i1 = idx_range

    roi_slice = (slice(i0, i1, None), *roi_rec_sl)  # 3D
    with h5py.File(path_dset, "r") as h5f:
        arr = h5f[path_in_h5][roi_slice].sum(axis=(1, 2))

    return arr


def get_sxdm_pos_sum(
    path_dset,
    scan_no,
    mask_detector=None,
    detector="mpx1x4",
    n_proc=None,
    pbar=True,
    path_data_h5="/{scan_no}/instrument/{detector}/data",
):
    """Return the sum of all sample positions.
    """

    detlist = get_detector_aliases(path_dset, scan_no)
    if detector not in detlist:
        raise ValueError(
            f"Detector {detector} not in data file. Available detectors are: {detlist}."
        )
    else:
        path_data_h5 = path_data_h5.format(scan_no=scan_no, detector=detector)

    if n_proc is None:
        n_proc = os.cpu_count()

    # list of idx ranges [(i0, i1), (i0, i1), ...]
    idxs_list = _get_chunk_indexes(path_dset, path_data_h5, n_threads=n_proc)

    # recipocal space slice from mask
    if mask_detector is not None:
        roi_rec = np.where(np.invert(mask_detector.astype("bool")))
        roi_rec_sl = tuple([slice(x.min(), x.max() + 1) for x in roi_rec])
    else:
        roi_rec_sl = np.s_[:, :]

    # call function with everything except the index ranges
    # the function returns a direct space map
    pfun = partial(_calc_pos_sum_chunk, path_dset, path_data_h5, roi_rec_sl)

    # set progress bar
    if pbar is True:
        pbar = tqdm()
    elif isinstance(pbar, tqdm):
        pbar.total = len(idxs_list)
        pbar.refresh()

    # apply partial function multi process, with an index range per process
    roi_sum_list = []
    try:
        pbar.reset(total=len(idxs_list))
    except AttributeError:
        pass
    with mp.Pool(processes=n_proc) as p:
        for res in p.imap(pfun, idxs_list):
            roi_sum_list.append(res)
            try:
                pbar.update()
                pbar.refresh()
            except AttributeError:  # pbar=False
                pass

    if pbar:
        pbar.close()

    return np.ma.concatenate(roi_sum_list)


# TODO
# replace with new funtion
@ioh5
def get_roi_pos(h5f, scan_no, roi_names_list, detector="mpx1x4"):
    """
    Only works for ROIs starting with `detector_`
    x,y,width,height
    """

    roi_params = {key: None for key in roi_names_list}
    badrois = []
    for r in roi_params.keys():
        try:
            roi_params[r] = [
                h5f[f"/{scan_no}/instrument/{detector}_{r}/selection/{m}"][()]
                for m in "x,y,width,height".split(",")
            ]
        except KeyError:
            badrois.append(r)

    for r in badrois:
        del roi_params[r]

    return roi_params


@ioh5
def _get_roi_pos_new(h5f, scan_no, detector=None):
    """
    TBD
    """

    detector = _check_detector(h5f.filename, scan_no, detector)
    roi_names = get_roi_names(h5f.filename, scan_no, only_sum=True)

    roi_params = {key: None for key in roi_names}
    badrois = []
    for r in roi_params.keys():
        try:
            roi_params[r] = [
                h5f[f"/{scan_no}/instrument/{r}/selection/{m}"][()]
                for m in "x,y,width,height".split(",")
            ]
        except KeyError:
            badrois.append(r)

    for r in badrois:
        del roi_params[r]

    return roi_params


def get_scan_table(path_dset):
    """Get an HTML table of scans contained within a BLISS dataset.

    Parameters
    ----------
    path_dset : str
        Path to the .hdf5 BLISS dataset.

    Returns
    -------
    ipywidgets.HTML
        Scan table.
    """

    table = [
        "<div>",
        '<table class="specs rendered_html output_html" style="font-size: small">',
        "  <tbody>",
        "    <tr>",
        "      <th>Scan</th>",
        "      <th>Command</th>",
        "      <th>Date | Time</th>",
        "    </tr>",
    ]

    with h5py.File(path_dset, "r") as h5f:
        for s in sorted(h5f.keys(), key=lambda s: int(s.split(".")[0])):
            title = h5f[f"{s}/title"][()].decode()

            dtime = h5f[f"{s}/start_time"][()].decode()
            dtime = datetime.fromisoformat(dtime).strftime("%b %d | %H:%M:%S")

            row = [
                "    <tr>",
                f"      <th>{s}</th>",
                f"      <td>{title}</td>",
                f"      <td>{dtime}</td>",
                "    </tr>",
            ]
            _ = [table.append(x) for x in row]

    table += ["  </tbody>", "</table>", "</div>"]
    table = "\n".join(table)

    return ipw.HTML(table)
