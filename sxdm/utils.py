"""
Various functions to aid the analysis of SXDM data.
"""

import pandas as pd
import os

from .io import FastSpecFile
 
def get_filelist(sample_dir):
    data = {'path':[], 'filename':[], 'nscans':[]}
    flist = []
 
    for root, dirs, files in os.walk(sample_dir):
        files = [x for x in files if all(s in x for s in 'spec,fast'.split(','))]
        if len(files) != 0:
            for i, f in enumerate(files):
                path = os.path.abspath('{}/{}'.format(root,f))
                 
                fsf = FastSpecFile(path)
 
                data['path'].append(path)
                data['filename'].append(f)
                data['nscans'].append(len(fsf.keys()))
 
    data = pd.DataFrame(data, columns=['path', 'filename', 'nscans'])
    data = data.sort_values('filename').reset_index(drop=True)
     
    return data

def get_pi_extents(piy, pix, winidx):
    return [piy[winidx].min(), piy[winidx].max(), pix[winidx].min(), pix[winidx].max()]