import sxdm
import os
import shutil
import numpy as np
import time

path_dset = (
    "/data/id01/inhouse/edo/tutorial_data/ech_1_night1/ech_1_night1_0010/"
    "ech_1_night1_0010.h5"
)
path_out = "test-data"

shifts = np.array([[0.0, 0.0], [4.0, 0.0], [9.0, -1.0], [14.0, -1.0], [17.0, -3.0]])

if path_out in os.listdir("."):
    shutil.rmtree(path_out)

os.mkdir(path_out)

sxdm.utils.bliss.make_xsocs_links(path_dset, path_out, None)

t0 = time.time()
sxdm.process.xsocs.shift_xsocs_data(path_dset, path_out, shifts)
t1 = time.time()

print(f"\n Shifting took {t1-t0:.1f}s")
