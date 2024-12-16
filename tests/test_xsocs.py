import sxdm
import os
import numpy as np


def test_xsocs_shift():
    # weirdly it seems the GL pipeline sees the root dir
    path_dset = "doc/source/examples/data/MA1234/id01/20230710/sample/sample_0001/sample_0001.h5"
    path_out = "doc/source/examples/data/MA1234/id01/20230710/sample_analysis/"

    shifts = np.array([[0.0, 0.0], [4.0, 0.0], [9.0, -1.0], [14.0, -1.0], [17.0, -3.0]])

    if not os.path.isdir(path_out):
        os.mkdir(path_out)

    sxdm.utils.bliss.make_xsocs_links(path_dset, path_out, None)

    path_master = f"{path_out}/sample_0001_master.h5"
    ret = sxdm.process.xsocs.shift_xsocs_data(
        path_master, path_out, shifts, overwrite=True
    )
    assert ret is None  # TODO this is baaaaaad


def test_xsocs_qconv():
    path_out = "doc/source/examples/data/MA1234/id01/20230710/sample_analysis"
    path_master = f"{path_out}/sample_0001_master_shifted.h5"
    path_qspace = f"{path_out}/qspace_shift.h5"

    offsets = {"eta": 0, "delta": 0, "phi": 0, "roby": 1, "nu": 0.5}

    sxdm.process.xsocs.grid_qspace_xsocs(
        path_qspace, path_master, (10, 10, 10), overwrite=True, offsets=offsets
    )

    qx, qy, qz = sxdm.utils.get_qspace_coords(path_qspace)

    assert qx.shape == (10,)
    assert qy.shape == (10,)
    assert qz.shape == (10,)
