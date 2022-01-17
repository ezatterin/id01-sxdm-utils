"""
Various functions to aid the analysis of SXDM data.
"""

import pandas as pd
import os

from .io import FastSpecFile


def get_filelist(sample_dir):
    data = {"path": [], "filename": [], "nscans": []}
    flist = []

    for root, dirs, files in os.walk(sample_dir):
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