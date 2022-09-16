import sxdm
import time

from xsocs.process.qspace.helpers import kmap_2_qspace

path_out = "tests/data/test-output"
path_master = f"{path_out}/sample_0001_master_shifted.h5"  
path_qspace = f"{path_out}/qspace_shift.h5"

try:
    print("Using xsocs-edo\n")
    offsets = {"eta": 0, "delta": 0, "phi": 0, "roby": 1, "nu": 0.5}

    t0 = time.time()
    sxdm.process.xsocs.grid_qspace_xsocs(
        path_qspace, path_master, (10, 10, 10), overwrite=True, offsets=offsets
    )
    t1 = time.time()

except (TypeError, ValueError):
    print("Using xsocs-upstream\n")
    t0 = time.time()
    kmap_2_qspace(path_master, path_qspace, (10, 10, 10), overwrite=True)
    t1 = time.time()

qx, qy, qz = sxdm.utils.get_qspace_coords(path_qspace)

print(f"\nQ-conversion took {t1-t0:.1f}s\n")
print(
    f"qx: {qx.min():.2f} --> {qx.max():.2f}\n"
    f"qy: {qy.min():.2f} --> {qy.max():.2f}\n"
    f"qz: {qz.min():.2f} --> {qz.max():.2f}\n"
)
