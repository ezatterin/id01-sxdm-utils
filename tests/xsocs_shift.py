import sxdm
import os
import numpy as np
import time

# weirdly it seems the GL pipeline sees the root dir
path_dset = "doc/source/examples/data/MA1234/id01/20230710/sample/sample_0001/sample_0001.h5"
path_out = "doc/source/examples/data/MA1234/id01/20230710/sample_analysis/"

shifts = np.array([[0.0, 0.0], [4.0, 0.0], [9.0, -1.0], [14.0, -1.0], [17.0, -3.0]])

if not os.path.isdir(path_out):
    os.mkdir(path_out)

sxdm.utils.bliss.make_xsocs_links(path_dset, path_out, None)
path_master = f"{path_out}/sample_0001_master.h5"

t0 = time.time()
sxdm.process.xsocs.shift_xsocs_data(path_master, path_out, shifts, overwrite=True)
t1 = time.time()

print(f"\n\n >> Shifting took {t1-t0:.1f}s")

ls = os.listdir(path_out)
print("Output directory contents:")
_ = [print(f"\t > {l}") for l in ls]
