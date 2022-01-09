"""
Read SXDM data, i.e. the output of pscan commands on ID01.
"""

import re
import numpy as np
import os
import time
import silx.io

from silx.io.specfile import SpecFile, Scan, SfErrColNotFound  # TODO use silx.io
from tqdm import tqdm


class FastSpecFile(SpecFile):
    """
    Opens a _fast_xxxxx.spec file.

    To select a single ``pscan`` from those contained in the _fast_xxxx.spec file, use
    the syntax `FastSpecFile[key]` where `key` is either an `int` corresponding to a
    scan index or a `str` of the kind `"n.m"`, with `n` being the scan number defined
    in the scan header and `m` the order.

    Parameters
    ----------
    filename : str
        Path to the _fast_xxxxx.spec file to read.

    Attributes
    ----------
    filename : str
        Path to the _fast_xxxx.spec file read.


    Methods
    -------
    keys : list
        Indexes of the scans contained within the _fast_xxxx.spec file. Use one of
        such ``n.m`` indexes to slice the `FastSpecFile` instance obtaining a
        `PiezoScan` instance.

    Returns
    -------
    pscan : `PiezoScan`
        Instance of the selected scan.

    Examples
    --------
    Load scan ``10.2``:

    >>> fsf = FastSpecFile('/path/to/file_fast_xxxxx.spec')
    >>> pscan = fsf['10.2']
    """

    def __new__(cls, filename):
        return super(FastSpecFile, cls).__new__(cls, filename)

    def __init__(self, filename):
        if not isinstance(filename, str):
            self.filename = filename.decode()
        else:
            self.filename = filename

    def __repr__(self):
        fname = os.path.basename(self.filename)

        frepr = "{0} \n\n --> {1}".format(self.__class__, fname)
        frepr += "\n --> {0} scans".format(len(self.keys()))
        frepr += "\n --> {0}".format(self.date())

        return frepr

    def __getitem__(self, key):
        """
        Returns a `PiezoScan` object.
        """
        msg = "The scan identification key can be an integer representing "
        msg += "the unique scan index or a string 'N.M' with N being the scan"
        msg += " number and M the order (eg '2.3')."

        if isinstance(key, int):
            scan_index = key
            # allow negative index, like lists
            if scan_index < 0:
                scan_index = len(self) + scan_index
        else:
            # wrong_scan_type = OSError, EOFError
            try:
                (number, order) = map(int, key.split("."))
                scan_index = self.index(number, order)
            except (ValueError, KeyError):
                # int() can raise a value error
                raise KeyError(msg + "\nValid keys: '" + "', '".join(self.keys()) + "'")
            except AttributeError:
                # e.g. "AttrErr: 'float' object has no attribute 'split'"
                raise TypeError(msg)
            except SfErrColNotFound:
                raise TypeError("this has to be debugged!")

        if not 0 <= scan_index < len(self):
            msg = "Scan index must be in range 0-%d" % (len(self) - 1)
            raise IndexError(msg)

        return PiezoScan(self, scan_index)


class PiezoScan(Scan):
    """
    Exposes a ``pscan`` contained within a `FastSpecFile`.

    Attributes
    ----------
    command : str
        The SPEC pscan command that was launched to produce these data.
    shape: tuple
        The 2D shape of the pscan.
    datetime: 
        The date and time when the scan was launched.

    Methods
    -------
    get_roidata(roi_name)
        Returns roi_name as a 2D `np.array`.
    get_piezo_coordinates()
        Returns the first, second motor (in the same order used when launching the 
        SPEC command) coordinates as a 2D `np.array`.
    get_motorpos(motor_name)
        Returns the position of the SPEC motor `motor_name`.
    get_roipos(roi_name)
        Returns a dictionary as `roi_name`:[x0, x1, y0, y1] where [x0, x1, y0, y1]
        are the ROI edges specified as detector pixels.
    get_edf_filename()
        Returns the full path to the .edf.gz file containing the detector frames
        collected as part of the scan.
    get_detector_frames()
    get_detcalib()
        Returns the output of the SPEC `det_calib` command, i.e. the detector
        distance, central pixel, pixels per degree, and incident beam energy.
    """

    motordef = dict(pix="adcY", piy="adcX", piz="adcZ")

    def __init__(self, fast_specfile, scan_number):
        super().__init__(fast_specfile, scan_number)

        self.command = self.scan_header_dict["S"][3:]
        self.shape = int(self.command.split()[9]), int(self.command.split()[5])
        self.datetime = self.scan_header_dict["D"]

    def __repr__(self):
        rep = "{0} \n\n --> {1}".format(self.__class__, self.command)
        rep += "\n --> {}".format(self.datetime)
        rep += "\n --> {}".format(self.shape)

        return rep

    def _repr_html_(self):

        table = [
            "<div>",
            "<style scoped>",  # why scoped?
            "    .pscan tbody tr th {",
            "        vertical-align: middle;",
            "    }",
            "</style>",
            '<table border="1" class="pscan">',
            "  <tbody>",
            '    <tr style="text-align: right;">',
            "      <th>Command</th>",
            "      <td>{}</td>".format(self.command),
            "    </tr>",
            '    <tr style="text-align: right;">',
            "      <th>Datetime</th>",
            "      <td>{}</td>".format(self.datetime),
            "    </tr>",
            '    <tr style="text-align: right;">',
            "      <th>Shape</th>",
            "      <td>{}</td>".format(self.shape),
            "    </tr>",
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        return "\n".join(table)

    def get_roidata(self, counter):
        try:
            return self.data_column_by_name(counter).reshape(self.shape)
        except SfErrColNotFound:
            print(
                '"{0}" is not a valid counter; available counters'
                "are: {1}".format(counter, self.labels)
            )

    def get_piezo_coordinates(self):
        motor_names = self.command.split()[2], self.command.split()[6]
        motor1, motor2 = [
            self.data_column_by_name(self.motordef[x]).reshape(self.shape)
            for x in motor_names
        ]
        return motor1, motor2

    def get_motorpos(self, motor_name):
        return self.motor_position_by_name(motor_name)

    def get_roipos(self):
        roipos = [x for x in self.file_header_dict["Ulima"].split("\n")][1:]
        roipos = np.array([x.split(" ") for x in roipos])
        roipos = {
            key: [int(x) for x in roipos[i, 2:]]
            for key, i in zip(roipos[:, 0], range(roipos.shape[0]))
        }
        return roipos

    def get_edf_filename(self):
        # regular expression matching the imageFile comment line
        _imgfile_pattern = (
            "^#C imageFile "
            "dir\[(?P<dir>[^\]]*)\] "
            "prefix\[(?P<prefix>[^\]]*)\] "
            "(idxFmt\[(?P<idxFmt>[^\]]*)\] ){0,1}"
            "nextNr\[(?P<nextNr>[^\]]*)\] "
            "suffix\[(?P<suffix>[^\]]*)\]$"
        )

        # find the image file line
        regx = re.compile(_imgfile_pattern)
        imgfile_match = [
            m
            for line in self.scan_header
            if line.startswith("#C imageFile")
            for m in [regx.match(line.strip())]
            if m
        ]
        info = imgfile_match[0].groupdict()

        # return the image path
        nextnr_pattern = "{0:0>5}"
        edf_path = "{}/{}{}{}".format(
            info["dir"],
            info["prefix"],
            nextnr_pattern.format(info["nextNr"]),
            info["suffix"],
        )
        return edf_path

    def get_detector_frames(self):
        edf_filename = self.get_edf_filename()

        t0 = time.time()
        print("Uncompressing data...", end=" ")
        edf_h5 = silx.io.open(edf_filename)
        frames = edf_h5["scan_0/image/data"][...]
        print("Done in {:.2f}s".format(time.time() - t0))

        return frames

    def get_detcalib(self):
        # specify keys to look for
        converters = {
            "cen_pix_x": float,
            "cen_pix_y": float,
            "pixperdeg": float,
            "timestamp": str,
            "det_distance_CC": float,
            "mononrj": lambda nrj: float(nrj[:-3]),  # Ends with keV
        }
        calibration = {}

        # Parse spec header to find calibration
        header = self.file_header
        for line in header:
            if line.startswith("#UDETCALIB ") or line.startswith("#UMONO "):
                params = line.split(" ")[1].strip().split(",")
                for item in params:
                    if "=" in item:
                        key, value = item.split("=")
                        if key in converters:
                            calibration[key] = converters[key](value)
        return calibration
