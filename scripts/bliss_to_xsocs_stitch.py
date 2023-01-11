"""
Same as bliss_to_xsocs but stitching multiple datasets. 
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
path_exp = "/data/visitor/im88/id01/"

# sample name (folders within path_exp)
name_sample = "HRB22_PO3_E4"

# multiple dataset names (folders within path_exp/name_sample)
names_dsets = [f"{name_sample}_{x}" for x in ("0002", "0003", "0004")]

# path of the output files to be read by XSOCS
path_out = f"{path_exp}/data_analysis/{name_sample}_multi/"

# scans to merge - this is a list of lists
# use None to merge all scans within one dataset
scan_nums = [None, None, range(1, 15)]

# prefix of the merged files to be read by XSOCS
# select at your preference!
name_outh5 = "data"

# detector name
detector = "mpx1x4"

###############
## FUNCTIONS ##
###############

#  this exists in sxdm.bliss.utils, explicitly defining it here in order to avoid
#  the script being dependent on the id01-sxdm-utils package (this package!)
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


# this will eventually end up in sxdm.bliss.utils too
def make_links(path_dset, path_out, scan_nums, detector, name_outh5=None):

    global scan_counter

    # open the dataset file
    with h5py.File(path_dset, "r") as h5f:
        _name_dset = os.path.basename(path_dset)

        # using all scan numbers in file?
        if scan_nums is None:
            print(f"> Using all scan numbers in {_name_dset}")
            _scan_idxs = range(1, len(list(h5f.keys())) + 1)
            _commands = [h5f[f"{s}.1/title"][()].decode() for s in _scan_idxs]
            _scan_nums = [
                f"{s}.1" for s, c in zip(_scan_idxs, _commands) if "sxdm" in c
            ]
        else:
            print(
                f"> Selecting scans {scan_nums[0]} --> {scan_nums[-1]} in {_name_dset}"
            )
            _scan_nums = [f"{x}.1" for x in scan_nums]
            _commands = [h5f[f"{s}/title"][()].decode() for s in _scan_nums]

        # name the output files
        if name_outh5 is None:
            name_outh5 = _name_dset

        # load counters, positioners, and other params for each scan
        for scan_num, command in zip(_scan_nums, _commands):

            _entry = h5f[scan_num]
            _instr = _entry["instrument/"]

            # get some metadata
            start_time = _entry["start_time"][()].decode()
            direct_beam = [
                _instr[f"{detector}/beam_center_{x}"][()] for x in ("y", "x")
            ]
            direct_beam = [x if x != 0 else 258 for x in direct_beam]

            det_distance = _instr[f"{detector}/distance"][()]
            det_distance = det_distance if det_distance != 0 else 0.5

            _pixsizes = [_instr[f"{detector}/{m}_pixel_size"][()] for m in ("y", "x")]
            chan_per_deg = [
                np.tan(np.radians(1)) * det_distance / pxs for pxs in _pixsizes
            ]
            energy = xu.lam2en(_instr["monochromator/WaveLength"][()] * 1e10)

            # get counters
            counters = [
                x for x in _instr if _instr[x].attrs.get("NX_class") == "NXdetector"
            ]
            try:
                counters.remove(f"{detector}_beam")
            except ValueError:
                pass

            # get piezo coordinates
            pi_positioners = [
                x for x in _instr if _instr[x].attrs.get("NX_class") == "NXpositioner"
            ]
            positioners = [x for x in _instr["positioners"]]

            # entry name
            _entry_name = (
                int(scan_num.split(".")[0]) + scan_counter
            )  # <-- ends up in output h5 fname
            _entry_name = f"{_entry_name}.1"

            # command parameters
            _command_params = _parse_scan_command(command)

            out_h5f = f"{path_out}/{name_outh5}_{_entry_name}.h5"

            # write links to individual XSOCS-compatible files
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
                xsocsh5f._set_scalar_data(f"{_entry_name}/title", command)
                xsocsh5f._set_scalar_data(f"{_entry_name}/start_time", start_time)

                for c in counters:
                    if c == detector:
                        xsocsh5f.add_file_link(
                            f"{_entry_name}/measurement/image/data",
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
                    if p == "delta":
                        xsocsh5f.add_file_link(
                            f"{_entry_name}/instrument/positioners/del",
                            path_dset,
                            f"{scan_num}/instrument/positioners/{p}",
                        )
                    else:
                        xsocsh5f.add_file_link(
                            f"{_entry_name}/instrument/positioners/{p}",
                            path_dset,
                            f"{scan_num}/instrument/positioners/{p}",
                        )

                for pp in pi_positioners:
                    try:
                        new_c = pi_motor_names[pp]
                        xsocsh5f.add_file_link(
                            f"{entry_name}/measurement/{new_c}",
                            path_dset,
                            f"{scan_num}/instrument/{pp}/value",
                        )
                    except KeyError:
                        pass

                _imgnr = np.arange(_entry[f"measurement/{detector}"].shape[0])
                xsocsh5f._set_array_data(f"{_entry_name}/measurement/imgnr", _imgnr)

                xsocsh5f.add_file_link(
                    f"{_entry_name}/technique", path_dset, f"{scan_num}/technique"
                )

            # write links to XSOCS master file
            with XsocsH5.XsocsH5MasterWriter(out_h5f_master, "a") as master:
                master.add_entry_file(_entry_name, out_h5f)

            # print
            print(f"\r> Linking # {scan_num}/{_scan_nums[-1]}", flush=True, end=" ")

        scan_counter += int(_scan_nums[-1].split(".")[0])
        print("\n> Done!")


##########
## CODE ##
##########

paths_dsets = [f"{path_exp}/{name_sample}/{nd}/{nd}.h5" for nd in names_dsets]

if not os.path.isdir(path_out):
    os.mkdir(path_out)

pi_motor_names = {
    "pix_position": "adcY",
    "piy_position": "adcX",
    "piz_position": "adcZ",
}

# generate output master file
out_h5f_master = f"{path_out}/{name_outh5}_master.h5"
with XsocsH5.XsocsH5MasterWriter(out_h5f_master, "w") as master:
    pass  # overwrite master file

scan_counter = 0
for dset, scannos in zip(paths_dsets, scan_nums):
    make_links(dset, path_out, scannos, detector, name_outh5=name_outh5)
