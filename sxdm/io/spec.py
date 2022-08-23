"""
Read SXDM data, i.e. the output of pscan commands on ID01.
"""

import re
import os
import time
import warnings

import numpy as np
import silx.io
import xrayutilities as xu

from silx.io.specfile import SpecFile, Scan, SfErrColNotFound  # TODO use silx.io
from tqdm.auto import tqdm

from id01lib import xrd
from silx.math import fit


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
    get_positioner(motor_name)
        Returns the position of the SPEC motor `motor_name`.
    get_roipos(roi_name)
        Returns a dictionary as `roi_name`:[x0, x1, y0, y1] where [x0, x1, y0, y1]
        are the ROI edges specified as detector pixels.
    get_edf_filename()
        Returns the full path to the .edf.gz file containing the detector frames
        collected as part of the scan.
    get_detector_frames()
        TODO
    get_detcalib()
        Returns the output of the SPEC `det_calib` command, i.e. the detector
        distance, central pixel, pixels per degree, and incident beam energy.
    calc_qspace_coordinates()
        TODO
    calc_coms()
        TODO
    fit_gaussian()
        TODO
    """

    motordef = dict(pix="adcY", piy="adcX", piz="adcZ")

    def __init__(self, fast_specfile, scan_number):
        super().__init__(fast_specfile, scan_number)

        self.command = self.scan_header_dict["S"]
        self.shape = int(self.command.split()[9]), int(self.command.split()[5])
        self.datetime = self.scan_header_dict["D"]

        self.piezo_motor_names = self.command.split()[2], self.command.split()[6]

        self.geometry = xrd.geometries.ID01psic()

        self._angles = self.geometry.sample_rot.copy()
        self._angles.update(self.geometry.detector_rot)  # order should be maintained

        self.qconversion_motors_use = ["eta", "phi", "nu", "delta"]
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
        motor1, motor2 = [
            self.data_column_by_name(self.motordef[x]).reshape(self.shape)
            for x in self.piezo_motor_names
        ]
        return motor1, motor2

    def get_positioner(self, motor_name):
        return self.motor_position_by_name(motor_name)

    # TODO replace with decorator for aliases + warnings
    # https://stackoverflow.com/questions/70213055/
    def get_motorpos(self, motor_name):
        warnings.warn(
            "The get_motorpos method is deprecated. Use get_positioner instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_positioner(motor_name)

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
            r"^#C imageFile "
            r"dir\[(?P<dir>[^\]]*)\] "
            r"prefix\[(?P<prefix>[^\]]*)\] "
            r"(idxFmt\[(?P<idxFmt>[^\]]*)\] ){0,1}"
            r"nextNr\[(?P<nextNr>[^\]]*)\] "
            r"suffix\[(?P<suffix>[^\]]*)\]$"
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

    def get_detector_frames(self, entry_name="scan_0"):
        edf_filename = self.get_edf_filename()

        # decompress edf file and load to memory
        t0 = time.time()
        print("Uncompressing data...", end=" ")
        edf_h5 = silx.io.open(edf_filename)
        try:
            self.frames = edf_h5["entry_0000/measurement/data"][...]
        except KeyError:
            self.frames = edf_h5[f"{entry_name}/image/data"][...]
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
        ipdir=(1, 0, 0),
        ndir=(0, 0, 1),
        ignore_mpx_motors=True,
    ):

        """
        ID01-specific function to calculate reciprocal space coordinates of a scan.

        Parameters
        ----------
        cen_pix : 2-tuple(int)
            ORDER: (first/slow dimension, second/fast dimension)
            the result of det_calib: cen_pix_y, cen_pix_x for maxipix
            Taken from detector calibration if not given

        detector_distance : float
            Sample to detector distance in meters.
            Taken from detector calibration if not given.

        energy : float
            The beam energy in keV. Taken from the scan header if not given.

        detector : str
            The detector used during the experiment. At the moment only "maxipix"
            (default) and "eiger" are supported.

        ipdir : 3-tuple(float)
            vector referring to the inplane-direction of the sample
            (see xrayutilities.experiment)

        ndir : 3-tuple(float)
            vector parallel to the sample normal
            (see xrayutilities.experiment)

        ignore_mpx_motors : Bool
            Wether to correct for mpxy, mpxz (not necessary if loading the detector
            calibration)

        Returns
        -------
        qx, qy, qz : numpy.ndarray
            The q-space coordinates in each orthogonal direction.

        """

        # init detector
        if detector == "maxipix":
            det = xrd.detectors.MaxiPix()
        elif detector == "eiger":
            det = xrd.detectors.Eiger2M()
        else:
            raise ValueError('Only "maxipix" and "eiger" are supported as detectors.')

        # load det_calib if it is complete
        names = "cen_pix_y,cen_pix_x,det_distance_CC,mononrj".split(",")
        try:
            cpx, cpy, detdist, nrj = [self.get_detcalib()[x] for x in names]
            nrj *= 1e3
            _calib = True
        except KeyError:
            _calib = False
            msg = "Incomplete det_calib found in the spec file!"
            msg += "Using user specified values..."
            print(msg)
            # raise ValueError(msg) from kerr

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
                    mpxy, mpxz = [self.get_positioner(m) for m in ("mpxy", "mpxz")]
                    cpy += mpxz / 1000.0 / det.pixsize[0]  # row
                    cpx -= mpxy / 1000.0 / det.pixsize[1]  # col

                    _msg = "Correcting mpxy={:.2f}, mpxz={:.2f} ==>".format(mpxy, mpxz)
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
        elif detector_distance is None:
            if not _calib:
                raise ValueError(
                    "detector_distance not found in scan header and set to None,"
                    "please specify"
                )
            else:
                pass

        # energy
        if energy is not None:
            nrj = energy
        elif energy is None:
            if not _calib:
                raise ValueError(
                    "energy not found in scan header and set to None, please specify"
                )
            else:
                pass

        # subtract offset from used angles
        for a in self._angles:
            if a in self.qconversion_motors_use:
                pos = self.get_positioner(a if a != "delta" else "del")
            else:
                pos = 0.0
            self._angles[a] = pos - self.qconversion_motors_offsets[a]

        # Init the experiment class feeding it the geometry
        hxrd = xu.HXRD(ipdir, ndir, en=nrj, qconv=self.geometry.getQconversion())

        # init XU detector class
        hxrd.Ang2Q.init_area(
            *det.directions,
            cch1=cpy,
            cch2=cpx,
            Nch1=det.pixnum[0],
            Nch2=det.pixnum[1],
            pwidth1=det.pixsize[0],
            pwidth2=det.pixsize[1],
            distance=detdist,
        )

        # Calculate q space values
        qx, qy, qz = hxrd.Ang2Q.area(*self._angles.values())

        self.qx = qx
        self.qy = qy
        self.qz = qz

        # grid
        # gridder = xu.gridder2d.Gridder2D(*mpx.pixnum)
        # gridder(qy, qz, np.empty(mpx.pixnum))
        # qyy, qzz = gridder.xaxis, gridder.yaxis

        return qx, qy, qz

    def calc_coms(self, roi=None, qspace=False, calc_std=False):
        """
        Calculate the centre of mass (COM) of the intensity in a detector frame for
        each scan position.

        Parameters
        ----------
        roi : list, optional
            Detector frame region of interest specified as [x_min, x_max, y_min, y_max].
            Restricts the COM calculation within this region. Default: full detector.
        qspace : bool, optional
            Compute the COMs in q-space coordinates. Requires
            `self.calc_qspace_coordinates` to have been previously run. Default is
            False, i.e. the calculation is done in detector pixel coordinates.
        calc_std : bool, optional
            Compute the peak standard deviations (more or less the peak width).
            if qspace==True, the STDs are calculated in q-space coordinates.

        Returns
        -------
        cx, cy, cz : np.ndarray
            The COM coordinates at each map position. If `qspace=False` only `cy, cz`
            are returned (in detector pixel coordinates).

        cx, cy, cz, stdx, stdy, stdz : np.ndarray
            If calc_std==True, return the COM and the STD at each map position.
            If `qspace=False` only `cy, cz, stdy,stdz` are returned (in detector
            pixel coordinates).
        """

        # Init ROI
        if roi is not None:
            roi = np.s_[roi[2] : roi[3], roi[0] : roi[1]]
        else:
            roi = np.s_[:, :]
        roi = slice(None, None, None), *roi

        # Get frames - shape = (n_points, detX, detY)
        try:
            frames = self.frames
        except AttributeError:
            frames = self.get_detector_frames()
        y, z = np.indices(frames.shape[1:])[roi]
        frames = frames[roi]

        if qspace:
            try:
                qx, qy, qz = [q[roi[1:]] for q in (self.qx, self.qy, self.qz)]

                coms = np.zeros((frames.shape[0], 3))
                if calc_std:
                    stds = np.zeros((frames.shape[0], 3))

                for index in tqdm(range(frames.shape[0])):
                    prob = frames[index] / frames[index].sum()
                    qcoms = [np.sum(prob * q) for q in (qx, qy, qz)]
                    coms[index, :] = qcoms

                    if calc_std:
                        qstds = [
                            np.sqrt(np.sum(prob * (q - qcom) ** 2.0))
                            for q, qcom in zip((qx, qy, qz), qcoms)
                        ]
                        stds[index, :] = qstds

                cqx, cqy, cqz = coms.reshape(*self.shape, 3).T
                if calc_std:
                    stdqx, stdqy, stdqz = stds.reshape(*self.shape, 3).T

                if calc_std:
                    return cqx, cqy, cqz, stdqx, stdqy, stdqz
                else:
                    return cqx, cqy, cqz

            except AttributeError:
                emsg = "Q-space coordinates not found. Please run the"
                emsg += "`calc_qspace_coordinates` method before using"
                emsg += "`qspace=True` in this function."
                print(emsg)
        else:
            coms = np.zeros((frames.shape[0], 2))
            if calc_std:
                stds = np.zeros((frames.shape[0], 2))

            for index in tqdm(range(frames.shape[0])):
                cy, cz = [
                    (
                        np.sum(frames[index] * pos, axis=(0, 1))
                        / frames[index].sum(axis=(0, 1))
                    )
                    for pos in (y, z)
                ]
                coms[index, :] = cy, cz

                if calc_std:
                    prob = frames[index] / frames[index].sum()
                    std = [
                        np.sqrt(np.sum(prob * (pos - com) ** 2.0))
                        for pos, com in zip((y, z), (cy, cz))
                    ]
                    stds[index, :] = std

            cy, cz = coms.reshape(*self.shape, 2).T
            if calc_std:
                stdy, stdz = stds.reshape(*self.shape, 2).T

            if calc_std:
                return cy, cz, stdy, stdz
            else:
                return cy, cz

    # def _calc_projections(self, roi=None, **qspace_kwargs):

    #     '''
    #     see the docstring of calc_qspace_coordinates for **qspace_kwargs
    #     '''

    #     try:
    #         frames = self.frames
    #     except AttributeError:
    #         frames = self.get_detector_frames()

    #     if roi is not None:
    #         roi = np.s_[roi[2]:roi[3], roi[0]:roi[1]]
    #     else:
    #         roi = np.s_[:,:]
    #     roi = slice(None,None,None), *roi

    #     return frames[roi].sum(0), frames[roi].sum(1)

    def fit_gaussian(self, index, roi=None, **qspace_kwargs):

        # roi
        if roi is not None:
            roi = np.s_[roi[2] : roi[3], roi[0] : roi[1]]
        else:
            roi = np.s_[:, :]

        # qcoords
        try:
            qy, qz = self.qy, self.qz
        except AttributeError:
            _, qy, qz = self.calc_qspace_coordinates(**qspace_kwargs)
        qy, qz = qy[roi], qz[roi]

        gridder = xu.gridder2d.Gridder2D(*qy.shape)
        gridder(qy, qz, np.empty(qy.shape))
        qyy, qzz = gridder.xaxis, gridder.yaxis

        # frames
        try:
            frames = self.frames
        except AttributeError:
            frames = self.get_detector_frames()

        roi = slice(None, None, None), *roi
        py, pz = frames[roi].sum(1)[index], frames[roi].sum(2)[index]

        p = {"qy": None, "qz": None}
        for name, ax, proj in zip(["qy", "qz"], [qyy, qzz], [py, pz]):

            # load profile
            x, y = ax, proj.astype("float64")

            # estimate and subtract background
            bg = fit.snip1d(y, len(y))
            y -= bg

            # guess initial params
            area = y.sum() * (x[-1] - x[0]) / len(x)
            mu = x[y.argmax()]
            fwhm = 2.3 * area / (y.max() * np.sqrt(2 * np.pi))

            # area, centroid, fwhm
            params, cov, info = fit.leastsq(
                fit.sum_agauss,
                x,
                y,
                p0=[area, mu, fwhm],
                #                                     sigma=np.sqrt(y),
                full_output=True,
            )
            p[name] = params

        return p
