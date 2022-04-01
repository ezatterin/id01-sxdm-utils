"""
Various functions to aid the analysis of SXDM data.
"""

import os
import numpy as np

from .io import FastSpecFile
from pandas import DataFrame


def get_filelist(sample_dir):
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

    data = DataFrame(data, columns=["path", "filename", "nscans"])
    data = data.sort_values("filename").reset_index(drop=True)

    return data


def get_pi_extents(piy, pix, winidx):
    return [piy[winidx].min(), piy[winidx].max(), pix[winidx].min(), pix[winidx].max()]


def get_q_extents(qx, qy, qz):
    m = [u.min() for u in (qx, qy, qz)]
    M = [u.max() for u in (qx, qy, qz)]
    extents = (
        [m[1], M[1], m[2], M[2]],  # yz
        [m[0], M[0], m[2], M[2]],  # xz
        [m[0], M[0], m[1], M[1]],
    )  # xy

    return extents

def load_detector_roilist(pscan, detector):

    if detector == 'maxipix':
        rois = [roi for roi, roipos in pscan.get_roipos().items() if max(roipos) <= 516]
        rois = [roi for roi in rois if 'mpx22' not in roi]
        roi_init = 'mpx4int'
    elif detector == 'eiger':
        rois = [roi for roi in pscan.get_roipos().keys() if 'mpx4' not in roi]
        roi_init = 'ei2mint'
    else:
        raise ValueError('Only "maxipix" and "eiger" are supported as detectors.')
        
    return rois, roi_init 

def convert_coms_qspace(coms, qcoords):
    """
    Converts COMs from detector pixel to q-space coordinates.
    Works only for 2D COMs at the moment.

    Parameters
    ----------
    coms : list
        Detector y (column) and z (row) coordinates of the COMs, in this order. 
        The output of`pscan.calc_coms`. Each coordinate is a `np.array` of shape 
        `pscan.shape`.
    qcoords : list
        Q-space (qy and qz) coordinates, in this order. Each coordinate is a `np.array` 
        of shape `pscan.shape`.

    Returns
    -------
    out : list
        Two-membered list of COMs in q-space coordinates, each of shape `pscan.shape`
    """

    cy, cz = coms
    qx, qy, qz = qcoords

    cy, cz = [np.round(x, 0).astype("int") for x in (cy, cz)]
    cqx, cqy, cqz = qx[cy,cz], qy[cy, cz], qz[cy, cz]

    return cqx, cqy, cqz