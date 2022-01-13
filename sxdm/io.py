"""
Read SXDM data, i.e. the output of pscan commands on ID01.
"""

import re
import os
import time
import multiprocessing as mp
import h5py

import numpy as np
import silx.io
import id01lib.xrd as xrd
import xrayutilities as xu

from silx.io.specfile import SpecFile, Scan, SfErrColNotFound  # TODO use silx.io
from tqdm.auto import tqdm

from .math import com2d


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

    def __str__(self):
        fname = os.path.basename(self.filename)

        frepr = "{0} \n\n --> {1}".format(self.__class__, fname)
        frepr += "\n --> {0} scans".format(len(self.keys()))
        frepr += "\n --> {0}".format(self.date())

        return frepr

    def _repr_html_(self):

        fname = os.path.basename(self.filename)

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
            "      <th>Filename</th>",
            "      <td>{}</td>".format(fname),
            "    </tr>",
            '    <tr style="text-align: right;">',
            "      <th>Number of scans</th>",
            "      <td>{}</td>".format(len(self.keys())),
            "    </tr>",
            '    <tr style="text-align: right;">',
            "      <th>Datetime</th>",
            "      <td>{}</td>".format(self.date()),
            "    </tr>",
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        return "\n".join(table)

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
    shape : tuple
        The 2D shape of the pscan.
    datetime : str
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

        self.command = self.scan_header_dict["S"]
        self.shape = int(self.command.split()[9]), int(self.command.split()[5])
        self.datetime = self.scan_header_dict["D"]

        self.geometry = xrd.geometries.ID01psic()

        self._angles = self.geometry.sample_rot.copy()
        self._angles.update(self.geometry.detector_rot)  # order should be maintained

        self.qconversion_motors_use = ["eta", "phi", "nu", "del"]
        self.qconversion_motors_offsets = {a: 0 for a in self._angles}

    def __str__(self):
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
            data = self.data_column_by_name(counter)
        except SfErrColNotFound as err:
            msg = '"{0}" is not a valid counter; available '.format(counter)
            msg += "counters are: {0}".format(self.labels)

            raise ValueError(msg) from err

        if data.size == self.shape[0] * self.shape[1]:
            return data.reshape(self.shape)
        else:
            empty = np.zeros(self.shape).flatten()
            empty[: data.size] = data
            return empty.reshape(self.shape)

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

        # decompress edf file and load to memory
        t0 = time.time()
        print("Uncompressing data...", end=" ")
        edf_h5 = silx.io.open(edf_filename)
        self.frames = edf_h5["scan_0/image/data"][...]
        print("Done in {:.2f}s".format(time.time() - t0))

        # write to hdf5
        # try:
        #     os.remove('temp_frames.h5')
        # except FileNotFoundError:
        #     pass
        # with h5py.File('temp_frames.h5', 'a') as h5f:
        #     h5f.create_dataset('frames', data=self.frames)

        return self.frames

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

    def calc_qspace_coordinates(
        self,
        cen_pix=None,
        detector_distance=None,
        energy=None,
        detector="maxipix",
        ipdir=[1, 0, 0],
        ndir=[0, 0, 1],
        ignore_mpx_motors=True,
    ):

        """

        Parameters
        ----------
        cen_pix : list
            y, x
        detector_distance : float
        energy : float
            in keV
        """

        names = "cen_pix_y,cen_pix_x,det_distance_CC,mononrj".split(",")
        try:
            cpx, cpy, detdist, nrj = [self.get_detcalib()[x] for x in names]
            nrj *= 1e3
            _calib = True
        except KeyError as kerr:
            _calib = False
            msg = "Incomplete det_calib found in the spec file! Using user specified values..."
            raise ValueError(msg) from kerr

        # central pixel
        if cen_pix is not None:
            _type = type(cen_pix)
            if _type != list and _type != tuple:
                raise ValueError(
                    "cen_pix must be a two-membered list or tuple, not {}".format(_type)
                )
            cpy, cpx = cen_pix
        if cen_pix is None:
            if _calib:
                if detector == "maxipix" and not ignore_mpx_motors:
                    mpxy, mpxz = [self.get_motorpos(m) for m in ("mpxy", "mpxz")]
                    cpy += mpxz / 1000.0 / detector.pixsize[0]  # row
                    cpx -= mpxy / 1000.0 / detector.pixsize[1]  # col

                    _msg = "Correcting mpxy={:.2f}, mpxz={:.2f}".format(mpxy, mpxz)
                    _msg += "cen_pix = ({:.1f},{:.1f})".format(cpy, cpx)
                    print(_msg)
                else:
                    pass
            else:
                raise ValueError(
                    "cen_pix not found in scan header and set to None, please specify"
                )

        # detector distance
        if detector_distance is not None:
            detdist = detector_distance
        elif detector_distance is not None and not _calib:
            raise ValueError(
                "detector_distance not found in scan header and set to None, please specify"
            )
        elif detector_distance is None and _calib:
            pass

        # energy
        if energy is not None:
            nrj = energy
        elif energy is not None and not _calib:
            raise ValueError(
                "energy not found in scan header and set to None, please specify"
            )
        elif energy is None and _calib:
            pass

        for a in self._angles:
            if a in self.qconversion_motors_use:
                pos = self.get_motorpos(a)
            else:
                pos = 0.0
            self._angles[a] = pos - self.qconversion_motors_offsets[a]

        # Init the experiment class feeding it the geometry
        hxrd = xu.HXRD(ipdir, ndir, en=nrj, qconv=self.geometry.getQconversion())

        # init detector
        if detector == "maxipix":
            det = xrd.detectors.MaxiPix()
        elif detector == "eiger":
            det = xrd.detectors.Eiger2M()
        else:
            raise ValueError('Only "maxipix" and "eiger" are supported as detectors.')

        # init XU detector class
        hxrd.Ang2Q.init_area(
            *det.directions,
            cch1=cpy,
            cch2=cpx,
            Nch1=det.pixnum[0],
            Nch2=det.pixnum[1],
            pwidth1=det.pixsize[0],
            pwidth2=det.pixsize[1],
            distance=detdist
        )

        # Calculate q space values
        qx, qy, qz = hxrd.Ang2Q.area(*self._angles.values())

        # grid
        # gridder = xu.gridder2d.Gridder2D(*mpx.pixnum)
        # gridder(qy, qz, np.empty(mpx.pixnum))
        # qyy, qzz = gridder.xaxis, gridder.yaxis

        return qx, qy, qz

    def calc_coms(self, roi=None):
        """
        roi : [x0,x1,y0,y1]
        """

        try:
            frames = self.frames[roi]
        except:
            frames = self.get_detector_frames()[roi]

        coms = np.zeros((frames.shape[0], 2))
        y, z = np.indices(frames.shape[1:])
        for index in tqdm(range(frames.shape[0])):
            cy, cz = [
                (
                    np.sum(frames[index] * pos, axis=(0, 1))
                    / frames[index].sum(axis=(0, 1))
                )
                for pos in (y, z)
            ]
            coms[index, :] = cy, cz

        cy, cz = coms.reshape(*self.shape, 2).T

        return cy, cz
