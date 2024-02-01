import collections
import os
import numpy as np
import h5py
import re

from xsocs.io import XsocsH5

__all__ = ["parse_nanomax_command", "make_xsocs_links_nanomax"]

ScanRange = collections.namedtuple("ScanRange", ["name", "start", "stop", "numpoints"])


def parse_nanomax_command(command):
    """
    Accepts a nanomax npointflyscan command and parses it according to the XSOCS
    file structure.
    """

    _COMMAND_LINE_PATTERN = (
        r"^(?P<command>[^\s]+)"
        r"(?:\s+(?P<motor_0>[^\s]+)\s+(?P<motor_0_start>[^\s]+)\s+"
        r"(?P<motor_0_end>[^\s]+)\s+(?P<motor_0_steps>[^\s]+)\s*"
        r"(?P<motor_1>[^\s]+)\s+(?P<motor_1_start>[^\s]+)\s+"
        r"(?P<motor_1_end>[^\s]+)\s+(?P<motor_1_steps>[^\s]+)\s*"
        r"(?P<delay>[^\s]+)\s+(?P<subscan_delay>[^\s]+))$"
    )
    cmd_rgx = re.compile(_COMMAND_LINE_PATTERN)
    cmd_match = cmd_rgx.match(command)

    if cmd_match is None:
        raise ValueError('Failed to parse command line: "{0}".'.format(command))

    cmd_dict = cmd_match.groupdict()
    cmd_dict.update(full=command)

    return cmd_dict


def make_xsocs_links_nanomax(
    path_exp,
    path_out,
    name_out,
    scan_nums,
    raw_nums=False,
):
    if not os.path.isdir(path_out):
        os.mkdir(path_out)

    pi_motor_names = {
        "x": "adcY",
        "z": "adcX",
        "y": "adcZ",
    }

    path_out_master = f"{path_out}/{name_out}_master.h5"

    for scan_idx, scan_num in enumerate(scan_nums):
        path_dset = f"{path_exp}/{scan_num:06d}.h5"

        with h5py.File(path_dset, "r") as h5f:
            # expt parameters
            direct_beam = [250, 250]
            det_distance = h5f["/entry/snapshots/pre_scan/radius"][()][0] / 1e3
            pix_sizes = [55e-6, 55e-6]
            chan_per_deg = [
                np.round(np.tan(np.radians(1)) * det_distance / pxs, 2)
                for pxs in pix_sizes
            ]
            energy = h5f["/entry/snapshots/pre_scan/energy_raw"][0]

            # positioners
            positioners = [p for p in h5f["/entry/snapshots/pre_scan/"]]
            pi_positioners = [
                p for p in h5f["/entry/measurement/pseudo/"] if len(p) == 1
            ]

            # scan parameters
            command = h5f["/entry/description"][0].decode()
            command_params = parse_nanomax_command(command)
            for x in (0, 1):
                command_params[f"motor_{x}_steps"] = str(
                    int(command_params[f"motor_{x}_steps"]) + 1
                )

            # output parameters
            if raw_nums:
                entry_name = f"{scan_num}.1"
            else:
                entry_name = f"{scan_idx}.1"
            start_time = "unknown"

            # write links to individual XSOCS-compatible files
            path_out_file = f"{path_out}/{name_out}_{entry_name}.h5"
            with XsocsH5.XsocsH5Writer(path_out_file, "w") as xsocsh5f:  # overwrite
                """
                XsocsH5Writer methods
                --> make links to scan parameters
                """
                xsocsh5f.create_entry(entry_name)  # creates NX skeleton
                xsocsh5f.set_scan_params(
                    entry_name, **command_params
                )  # "scan" folder contents

                xsocsh5f.set_beam_energy(energy, entry_name)
                xsocsh5f.set_chan_per_deg(chan_per_deg, entry_name)
                xsocsh5f.set_direct_beam(direct_beam, entry_name)
                xsocsh5f.set_image_roi_offset([0, 0], entry_name)  # hardcoded for now

                """
                XsocsH5Base methods
                --> make links to data and counters
                """
                xsocsh5f._set_scalar_data(f"{entry_name}/title", command)
                xsocsh5f._set_scalar_data(f"{entry_name}/start_time", start_time)

                # data
                xsocsh5f.add_file_link(
                    f"{entry_name}/measurement/image/data",
                    path_dset,
                    "/entry/measurement/merlin/frames",
                )

                nanomax_aliases = {
                    "gontheta": "eta",
                    "gonphi": "phi",
                    "gamma": "nu",
                    "delta": "del",
                }
                for p in positioners:
                    pa = nanomax_aliases.get(p, p)
                    xsocsh5f.add_file_link(
                        f"{entry_name}/instrument/positioners/{pa}",
                        path_dset,
                        f"/entry/snapshots/pre_scan/{p}",
                    )

                for pp in pi_positioners:
                    new_c = pi_motor_names[pp]
                    xsocsh5f.add_file_link(
                        f"{entry_name}/measurement/{new_c}",
                        path_dset,
                        f"/entry/measurement/pseudo/{pp}",
                    )

                imgnr = np.arange(h5f["/entry/measurement/merlin/frames"].shape[0])
                xsocsh5f._set_array_data(f"{entry_name}/measurement/imgnr", imgnr)

                xsocsh5f.add_file_link(
                    f"{entry_name}/technique", path_dset, f"{scan_num}/technique"
                )

            # write links to XSOCS master file
            with XsocsH5.XsocsH5MasterWriter(path_out_master, "a") as master:
                master.add_entry_file(entry_name, os.path.basename(path_out_file))

            # print
            print(f"\r> Linking # {scan_num}/{scan_nums[-1]}", flush=True, end=" ")

    print("\n> Done!\n")
