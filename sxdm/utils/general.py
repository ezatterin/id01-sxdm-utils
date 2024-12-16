"""
Various functions to aid the analysis of SXDM data.
"""

import numpy as np
import pandas as pd
import os
import xrayutilities as xu

from skimage import registration
from scipy.ndimage import median_filter, shift
from tqdm.notebook import tqdm

from ..io.spec import FastSpecFile
from ..io.bliss import ioh5, get_roidata

from id01lib.xrd.geometries import ID01psic


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


def get_shift_dset(
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
    >>> shifts, raw_maps, shited_maps = sxdm.utils.get_shift(
            path_dset,
            roi="mpx1x4_roi1",
            scan_nums=[f"{x}.1" for x in range(1, 61)],
            return_maps=True,
            med_filt=(2,2),
            reference_mask=mask
        )
    """

    # raw ROIs
    sxdm_raw = [get_roidata(path_dset, i, roi) for i in scan_nums]
    if log:
        sxdm_raw = [np.log(map, where=(map > 0)) for map in sxdm_raw]

    # shifts
    shifts = get_shift(sxdm_raw, med_filt=med_filt, **xcorr_kwargs)

    # shifted ROIs
    sxdm_shifted = []
    for i in range(len(scan_nums)):
        sxdm_sh = shift(sxdm_raw[i], shifts[i])
        sxdm_shifted.append(sxdm_sh)

    if return_maps:
        return shifts, sxdm_raw, sxdm_shifted
    else:
        return shifts


def get_shift(images, med_filt=None, **xcorr_kwargs):
    """
    Calculate the cumulative shifts between consecutive images in a sequence.

    Parameters
    ----------
    images : List[np.ndarray]
        A list of 2D arrays representing consecutive images.
    med_filt : int, optional
        The size of the median filter to be applied to each image before
        cross-correlation. If None, no median filter is applied. Default is None.
    **xcorr_kwargs : dict
        Additional keyword arguments to be passed to
        `registration.phase_cross_correlation`.

    Returns
    -------
    np.ndarray
        A 2D array where each row corresponds to the cumulative shift (y, x) for
        each image. The first row represents the base case with no shift.
        Column 0 corresponds to y-shifts, and column 1 corresponds to x-shifts.
    """

    shifts = []
    shifts.insert(0, np.array([0, 0]))
    for i in tqdm(range(1, len(images))):
        if med_filt is not None:
            p, n = [median_filter(s, med_filt) for s in (images[i - 1], images[i])]
        else:
            p, n = [s for s in (images[i - 1], images[i])]
        sh, _, _ = registration.phase_cross_correlation(p, n, **xcorr_kwargs)
        shifts.append(sh + shifts[i - 1])
    shifts = np.array(shifts)  # col0: y shifts. col1: x shifts

    return shifts


def calc_refl_id01(
    hkl,
    material,
    ip_dir,
    oop_dir,
    nrj,
    bounds={"eta": (-2, 120), "phi": (-180, 180), "nu": 0, "delta": (-2, 130)},
    return_q_com=False,
):
    """
    Calculate the ID01 diffractometer angles for a given reflection hkl.

    Parameters
    ----------
    hkl : array_like
        Miller indices of the reflection.
    material : xu.materials.material.Crystal or str
        Crystal object from xrayutilities.materials or path to a CIF file.
    ip_dir : array_like
        Crystal direction parallel to the incident beam, expressed as a list or array
        of length 3.
    oop_dir : array_like
        Crystal direction parallel to the z laboratory axis and perpedincular to the
        incident beam expressed, as a list or array of length 3.
    nrj : float
        X-ray energy in keV.
    bounds : dict, optional
        Dictionary specifying the bounds for diffractometer angles. A single value
        denotes a fixed angle. A maximum of three non-fixed angles is allowed.
        Default is {"eta": (-2, 120), "phi": (-180, 180), "nu": 0, "delta": (-2, 130)}.

    Returns
    -------
    dict
        A dictionary containing the diffractometer angles.

    Raises
    ------
    ValueError
        If the material is not a valid xrayutilities.materials instance nor a valid
        CIF file, if ip_dir or oop_dir is not a list or array of length 3,
        or if the reflection hkl is not a list or array of length 3.
    """

    # check material is xu.materials instance or CIF file
    if not isinstance(material, xu.materials.material.Crystal):
        if ".cif" in os.path.splitext(material):
            mat = xu.materials.Crystal.fromCIF(material)
        else:
            msg = f"{material} is not a valid xrayutilities.materials instance"
            msg += "nor a valid CIF file."
            raise ValueError(msg)
    else:
        mat = material

    # check directions are expressed correctly
    for d, dn in zip([ip_dir, oop_dir], ["ip_dir", "oop_dir"]):
        if len(d) != 3:
            raise ValueError(f"{dn} must be a list or array of lenght 3.")

    # angles to lab
    qconv = xu.QConversion(
        (ID01psic.sample_rot["eta"], ID01psic.sample_rot["phi"]),
        (ID01psic.detector_rot["nu"], ID01psic.detector_rot["delta"]),
        (1, 0, 0),
    )

    # crystal to lab
    hxrd = xu.FourC(mat.Q(ip_dir), mat.Q(oop_dir), en=nrj, qconv=qconv)

    # q-space lab coordinates of hkl
    if len(hkl) != 3:
        raise ValueError("Reflection hkl must be a list or array of lenght 3.")
    q_cryst = mat.Q(hkl)
    q_lab = hxrd.Transform(q_cryst)

    # compute diffractometer angles from q-space coords
    ang, qerror, errcode = xu.Q2AngFit(q_lab, hxrd, bounds.values())

    ang_dict = {key: np.round(val, 4) for key, val in zip(bounds.keys(), ang)}

    if return_q_com:
        return ang_dict, hxrd.Transform(q_cryst)
    else:
        return ang_dict


def slice_from_mask():
    pass
