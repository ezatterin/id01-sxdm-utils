"""
Various functions to aid the analysis of SXDM data.
"""

import numpy as np
import pandas as pd
import os

from skimage import registration
from scipy.ndimage import median_filter, shift
from tqdm.auto import tqdm

from ..io.spec import FastSpecFile
from ..io.bliss import ioh5, get_roidata


@ioh5
def get_qspace_coords(h5f):
    return [h5f[f"Data/{x}"][...] for x in "qx,qy,qz".split(",")]


def get_filelist(sample_dir):
    """
    SPEC.
    """
    data = {"path": [], "filename": [], "nscans": []}

    for root, _, files in os.walk(sample_dir):
        files = [x for x in files if all(s in x for s in "spec,fast".split(","))]
        if len(files) != 0:
            for i, f in enumerate(files):
                path = os.path.abspath("{}/{}".format(root, f))

                fsf = FastSpecFile(path)

                data["path"].append(path)
                data["filename"].append(f)
                data["nscans"].append(len(fsf.keys()))

    data = pd.DataFrame(data, columns=["path", "filename", "nscans"])
    data = data.sort_values("filename").reset_index(drop=True)

    return data


def get_pi_extents(m0, m1, winidx):
    return [m0[winidx].min(), m0[winidx].max(), m1[winidx].min(), m1[winidx].max()]


def get_q_extents(qx, qy, qz):
    m = [u.min() for u in (qx, qy, qz)]
    M = [u.max() for u in (qx, qy, qz)]
    extents = (
        [m[1], M[1], m[2], M[2]],  # yz
        [m[0], M[0], m[2], M[2]],  # xz
        [m[0], M[0], m[1], M[1]],
    )  # xy

    return extents


def get_detector_roilist(pscan, detector):
    """
    SPEC. Return the list of user-defined ROIs for a given `detector`.

    Parameters
    ----------
    pscan : sxdm.io.spec.PiezoScan
        PiezoScan to load the ROI list from.
    detector : str
        Name of the detector used.

    Returns
    -------
    rois : list of str
        List of ROI names.
    roi_init : str
        Name of an arbitrarily defined ROI which should always be present.
    """

    if detector == "maxipix":
        rois = [roi for roi, roipos in pscan.get_roipos().items() if max(roipos) <= 516]
        rois = [roi for roi in rois if "mpx22" not in roi]
        roi_init = "mpx4int"
    elif detector == "eiger":
        rois = [roi for roi in pscan.get_roipos().keys() if "mpx4" not in roi]
        roi_init = "ei2mint"
    else:
        raise ValueError('Only "maxipix" and "eiger" are supported as detectors.')

    return rois, roi_init


def get_shift(
    path_dset,
    roi,
    scan_nums,
    log=False,
    med_filt=None,
    return_maps=False,
    **xcorr_kwargs,
):
    """ "
    Estimate shift in a list of scans.

    Parameters
    ----------
    path_dset : str
        Path to dataset.h5 file.
    roi : str
        Name of the ROI (e.g. "mpx1x4_roi2").
    scan_nums : list of str
        List of scan numbers in x.1 form (e.g., ['1.1', '2.1'])
    log : bool, default=False
        Transform the raw data to log scale before shift estimation.
    med_filt : list, optional
        Size of the median filter kernel in pixels. Default: None (no filter).
    return_maps : bool, default=False
        If set to True, return the list of raw and shifted maps as well.
    **xcorr_kwargs : dict, optional
        Extra arguments to `skimage.registration.phase_cross_correlation`, refer to
        its documentation for a list of possible arguments.

    Returns
    -------
    shifts : np.ndarray
        2D array giving shifts in pixels along rows (first col)
        and columns (second col).
    raw_maps : list of np.ndarray
        List of *raw* SXDM maps of the specified ROI sorted according to the scan list 
        provided as input.
    shifted_maps : list of np.ndarray
        List of *shifted* SXDM maps of the specified ROI sorted according to the scan 
        list provided as input.

    Example
    -------
    >>> shifts, raw_maps, shited_maps = get_shift('data.h5',
                                                  'mpx1x4_mpx4int',
                                                  [f'{x}.1' for x in range(1,41)],
                                                  med_filt=[2,2],
                                                  return_maps=True)
    """

    # raw ROIs
    sxdm_raw = [get_roidata(path_dset, i, roi) for i in scan_nums]
    if log:
        sxdm_raw = [np.log(map, where=(map > 0)) for map in sxdm_raw]

    # shifts
    shifts = []
    shifts.insert(0, np.array([0, 0]))
    for i in tqdm(range(1, len(sxdm_raw))):
        if med_filt is not None:
            p, n = [median_filter(s, med_filt) for s in (sxdm_raw[i - 1], sxdm_raw[i])]
        else:
            p, n = [s for s in (sxdm_raw[i - 1], sxdm_raw[i])]
        sh = registration.phase_cross_correlation(
            p, n, return_error=False, **xcorr_kwargs
        )
        shifts.append(sh + shifts[i - 1])
    shifts = np.array(shifts)  # col0: y shifts. col1: x shifts

    # shifted ROIs
    sxdm_shifted = []
    for i in range(len(scan_nums)):
        sxdm_sh = shift(sxdm_raw[i], shifts[i])
        sxdm_shifted.append(sxdm_sh)

    if return_maps:
        return shifts, sxdm_raw, sxdm_shifted
    else:
        return shifts

def slice_from_mask():
    pass