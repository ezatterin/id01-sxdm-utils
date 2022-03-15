"""
Run this script to generate a set of HDF5 files compatible with XSOCS, from
data generated via BLISS. Essentially a quick workaround to continue to use
XSOCS.
IMPORTANT: the script generates files with *links* to the original data, it
does not copy it (very fast). DO NOT delete the original data! If you move it,
you will have to re-run this script.
"""

import os
import numpy as np
import h5py
import xrayutilities as xu
import re

from xsocs.io import XsocsH5


###########
## INPUT ##
###########

# base experiment directory
path_exp = "/data/id01/inhouse/data/IHR/blc13626/id01"

# sample name (folder within path_exp)
name_sample = "e17049_macro"

# dataset name (folder withn path_exp/name_sample)
name_dset = f"{name_sample}_0002"

# detector name
detector = "mpx1x4"

# path of the output files to be read by XSOCS
path_out = f"{path_exp}/data_analysis/xsocs_merge/"


##########
## CODE ##
##########

# this exists in sxdm.bliss.utils, explicitly defining it here
# in order to avoid the script being dependent on the
# id01-sxdm-utils package (this package!)
def _parse_scan_command(command):
    """
    Accepts a BLISS SXDM command and parses it according to the XSOCS
    file structure.
    """

    _COMMAND_LINE_PATTERN = (
        "^(?P<command>[^ ]*)\( "
        "(?P<motor_0>[^ ]*), "
        "(?P<motor_0_start>[^ ]*), "
        "(?P<motor_0_end>[^ ]*), "
        "(?P<motor_0_steps>[^ ]*), "
        "(?P<motor_1>[^ ]*), "
        "(?P<motor_1_start>[^ ]*), "
        "(?P<motor_1_end>[^ ]*), "
        "(?P<motor_1_steps>[^ ]*), "
        "(?P<delay>[^ ]*)\s*"
        ".*"
        "$"
    )
    cmd_rgx = re.compile(_COMMAND_LINE_PATTERN)
    cmd_match = cmd_rgx.match(command)
    if cmd_match is None:
        raise ValueError('Failed to parse command line : "{0}".' "".format(command))
    cmd_dict = cmd_match.groupdict()
    cmd_dict.update(full=command)
    return cmd_dict

path_dset = f"{path_exp}/{name_sample}/{name_dset}/{name_dset}.h5"
pi_motor_names = {"raw_pix_adc": "adcY", "raw_piy_adc": "adcX", "raw_piz_adc": "adcZ"}

with h5py.File(path_dset, "r") as h5f:

    _nscans = len(list(h5f.keys()))
    _scan_idxs = range(1, _nscans + 1)

    _commands = [h5f[f"{s}.1/title"][()].decode() for s in _scan_idxs]
    _scan_nums = [f"{s}.1" for s, c in zip(_scan_idxs, _commands) if "sxdm" in c]

    # generate the output file
    out_h5f_master = f"{path_out}/{name_dset}.h5"
    with XsocsH5.XsocsH5MasterWriter(out_h5f_master, "w") as master:
        pass  # overwrite master file

    # load counters, positioners, and other params for each scan
    for idx, scan_num, command in zip(_scan_idxs, _scan_nums, _commands):

        _entry = h5f[scan_num]
        _instr = _entry["instrument/"]

        start_time = _entry["start_time"][()].decode()

        counters = [
            x for x in _instr if _instr[x].attrs.get("NX_class") == "NXdetector"
        ]
        counters.remove(f"{detector}_beam")
        positioners = [x for x in _instr["positioners"]]

        direct_beam = [_instr[f"{detector}/beam_center_{x}"] for x in ("y", "x")]
        det_distance = _instr[f"{detector}/distance"]

        _pixsizes = [_instr[f"{detector}/{m}_pixel_size"][()] for m in ("y", "x")]
        chan_per_deg = [np.tan(np.radians(1)) * det_distance / pxs for pxs in _pixsizes]

        energy = xu.lam2en(_instr["monochromator/WaveLength"][()] * 1e10)

        _bliss_file = (
            f"{path_exp}/{name_sample}/{name_dset}/scan{idx:04d}/{detector}_0000.h5"
        )

        # the bliss scan folder
        _entry_name = os.path.abspath(_bliss_file).split("/")[-2]
        _command_params = _parse_scan_command(command)

        # write links to individual XSOCS-compatible files
        out_h5f = f"{path_out}/{name_dset}_{scan_num}.h5"
        with XsocsH5.XsocsH5Writer(out_h5f, "w") as xsocsh5f:  # overwrite

            """
            XsocsH5Writer methods
            --> make links to scan parameters
            """
            xsocsh5f.create_entry(_entry_name)  # creates NX skeleton
            xsocsh5f.set_scan_params(
                _entry_name, **_command_params
            )  # "scan" folder contents

            xsocsh5f.set_beam_energy(energy, _entry_name)
            xsocsh5f.set_chan_per_deg(chan_per_deg, _entry_name)
            xsocsh5f.set_direct_beam(direct_beam, _entry_name)
            xsocsh5f.set_image_roi_offset([0, 0], _entry_name)  # hardcoded for now

            """
            XsocsH5Base methods
            --> make links to data and counters
            """
            xsocsh5f._set_scalar_data("title", command)
            xsocsh5f._set_scalar_data("start_time", start_time)

            for c in counters:
                if c == detector:
                    xsocsh5f.add_file_link(
                        f"{_entry_name}/measurement/image/data",
                        path_dset,
                        f"{scan_num}/measurement/{c}",
                    )
                elif c in pi_motor_names.keys():
                    new_c = pi_motor_names[c]
                    xsocsh5f.add_file_link(
                        f"{_entry_name}/measurement/{new_c}",
                        path_dset,
                        f"{scan_num}/measurement/{c}",
                    )
                else:
                    xsocsh5f.add_file_link(
                        f"{_entry_name}/measurement/{c}",
                        path_dset,
                        f"{scan_num}/measurement/{c}",
                    )

            for p in positioners:
                xsocsh5f.add_file_link(
                    f"{_entry_name}/instrument/positioners/{p}",
                    path_dset,
                    f"{scan_num}/instrument/positioners/{p}",
                )

        # write links to XSOCS master file
        with XsocsH5.XsocsH5MasterWriter(out_h5f_master, "a") as master:
            master.add_entry_file(_entry_name, out_h5f)
