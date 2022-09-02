import collections
import os
import numpy as np
import h5py
import xrayutilities as xu
import re

from xsocs.io import XsocsH5
from id01lib.io.bliss import get_detector_aliases

__all__ = ["get_SXDM_info", "parse_scan_commands", "make_xsocs_links"]

ScanRange = collections.namedtuple("ScanRange", ["name", "start", "stop", "numpoints"])


def get_SXDM_info(path_dset, scan_range=(1, None)):
    """
    Return scan parameters from one SXDM scan, or from several SXDM scans
    composing a 3D-SXDM dataset.

    Parameters
    ----------
    path_dset : str
        Path to the .h5 dataset file, with links to individual scan .h5 files.
    scan_range : tuple
        Range of scan numbers to process. Default: all available scans in the file.

    Returns
    -------
    info : dict
        Dictionary of parameters and their values.
    """

    info = None
    motor_stop = False
    positions = collections.defaultdict(list)

    with h5py.File(path_dset, "r") as h5f:
        first_scan = scan_range[0] if scan_range[0] is not None else 1
        last_scan = scan_range[-1] if scan_range[-1] is not None else len(h5f) - 1

        for scanno in range(first_scan, last_scan):
            scan = h5f[f"{scanno}.1"]
            instrument = scan["instrument"]
            positioners = instrument["positioners"]

            command = scan["title"][()].decode()

            try:
                info_tmp = parse_scan_command(command)

            except ValueError as err:
                print(f"Scan {scanno}: {err} Skipping...")
                break

            if "sxdm" not in info_tmp["command"]:
                print(f"Scan {scanno} is not an sxdm command, skipping...")
                break

            if info is None:  # first iter
                info = info_tmp.copy()
                info["cen_pix_0"] = instrument["mpx1x4/beam_center_y"][()]
                info["cen_pix_1"] = instrument["mpx1x4/beam_center_x"][()]
                info["detdistance"] = instrument["mpx1x4/distance"][()]
                info["wavelength"] = instrument["monochromator/WaveLength"][()]
                info["beamenergy"] = 12.398e-10 / info["wavelength"]
            else:
                for key in ["motor_0", "motor_0_steps", "motor_1", "motor_1_steps"]:
                    motor_stop += info[key] != info_tmp[key]

            if motor_stop:
                break

            for motor_name in positioners:
                if not positioners[motor_name].shape:
                    positions[motor_name].append(positioners[motor_name][()])

    for i in (0, 1):
        info[f"motor_{i}"] = ScanRange(
            info[f"motor_{i}"],
            float(info.pop(f"motor_{i}_start")),
            float(info.pop(f"motor_{i}_end")),
            int(info.pop(f"motor_{i}_steps")),
        )

    slo_mot_sh = len(positions[motor_name])
    slowest_motors = []
    for motor_name in positions:
        if motor_name == info["motor_0"].name or motor_name == info["motor_1"].name:
            continue
        pos = positions[motor_name]
        if len(np.unique(pos)) == slo_mot_sh:
            slowest_motors.append(
                ScanRange(motor_name, float(pos[0]), float(pos[-1]), int(slo_mot_sh))
            )

    info["motor_2"] = slowest_motors
    info["shape"] = slo_mot_sh, info["motor_1"].numpoints, info["motor_0"].numpoints

    return info


def parse_scan_command(command):
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


def make_xsocs_links(
    path_dset, path_out, scan_nums, detector=None, name_outh5=None
):
    """
    Generates a set of .h5 files to be fed to XSOCS from a 3D-SXDM dataset.
    The files contain *links* to the original data, not the data itself.

    Parameters
    ----------
    path_dset : str
        Path to the .h5 dataset file, with links to individual scan .h5 files.
    path_out:
        Path to the folder where the XSOCS-compatible .h5 files will be saved.
    scan_nums : list, tuple or range of int
        Scan numbers to be processed.
    detector : str, default `None`
        The name of the detector used to collect the data.
    name_outh5 : str, default `None`
        Prefix of the XSOCS-compatible .h5 files generated. Defaults to the suffix of
        `path_dset`.

    Returns
    -------
        Nothing.

    """

    if not os.path.isdir(path_out):
        os.mkdir(path_out)

    pi_motor_names = {
        "pix_position": "adcY",
        "piy_position": "adcX",
        "piz_position": "adcZ",
    }

    # open the dataset file
    with h5py.File(path_dset, "r") as h5f:
        _name_dset = os.path.basename(path_dset).split(".")[0]

        # using all scan numbers in file?
        if scan_nums is None:
            print(f"> Using all scan numbers in {_name_dset}")
            _scan_idxs = range(1, len(list(h5f.keys())) + 1)
            _commands = [h5f[f"{s}.1/title"][()].decode() for s in _scan_idxs]
            _scan_nums = [
                f"{s}.1"
                for s, c in zip(_scan_idxs, _commands)
                if any([s in c for s in ("sxdm", "kmap")])
            ]
        else:
            try:
                _scan_nums = [f"{int(x)}.1" for x in scan_nums]
            except ValueError:  # not a list of int
                _scan_nums = scan_nums
            print(
                f"> Selecting scans {_scan_nums[0]} --> {_scan_nums[-1]} in {_name_dset}"
            )
            _commands = [h5f[f"{s}/title"][()].decode() for s in _scan_nums]

        # name the output files
        if name_outh5 is None:
            name_outh5 = _name_dset

        # detector?
        if detector is None:
            detector = get_detector_aliases(path_dset, _scan_nums[0])
            if len(detector) > 1:
                msg = f"Found multiple detector groups: {detector}, select"
                msg += "one by explicitly setting the `det` keyword argument"
                raise Exception(msg)
            else:
                detector = detector[0]
        else:
            detector = detector
        print(f'> Selecting detector {detector}')

        # generate output master file
        out_h5f_master = f"{path_out}/{name_outh5}_master.h5"
        with XsocsH5.XsocsH5MasterWriter(out_h5f_master, "w") as master:
            pass  # overwrite master file

        # load counters, positioners, and other params for each scan
        for scan_num, command in zip(_scan_nums, _commands):

            _entry = h5f[scan_num]
            _instr = _entry["instrument/"]

            # get some metadata
            start_time = _entry["start_time"][()].decode()
            direct_beam = [_instr[f"{detector}/beam_center_{x}"] for x in ("y", "x")]
            det_distance = _instr[f"{detector}/distance"]

            _pixsizes = [_instr[f"{detector}/{m}_pixel_size"][()] for m in ("y", "x")]
            chan_per_deg = [
                np.tan(np.radians(1)) * det_distance / pxs for pxs in _pixsizes
            ]
            energy = xu.lam2en(_instr["monochromator/WaveLength"][()] * 1e10)

            # get counters
            counters = [
                x for x in _instr if _instr[x].attrs.get("NX_class") == "NXdetector"
            ]

            # Why am I removing this? I forgot.
            # In the new bliss files it does not seem to be there,
            # hence the try / except
            try:
                counters.remove(f"{detector}_beam")
            except ValueError:
                pass

            # get piezo coordinates
            pi_positioners = [
                x for x in _instr if _instr[x].attrs.get("NX_class") == "NXpositioner"
            ]
            positioners = [x for x in _instr["positioners"]]

            # more parameters
            _entry_name = scan_num  # <-- ends up in output h5 fname
            _command_params = parse_scan_command(command)

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
                            f"{_entry_name}/measurement/{new_c}",
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
                master.add_entry_file(_entry_name, os.path.basename(out_h5f))

            # print
            print(f"\r> Linking # {scan_num}/{_scan_nums[-1]}", flush=True, end=" ")

        print("\n> Done!\n")
