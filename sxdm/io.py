import re
import numpy as np

from silx.io.specfile import (SpecFile, Scan,
                              SfErrScanNotFound, SfErrColNotFound)


class FastSpecFile(SpecFile):

    def __new__(cls, filename):
        return super(FastSpecFile, cls).__new__(cls, filename)

    def __init__(self, filename):
        if not isinstance(filename, str):
            self.filename = filename.decode()
        else:
            self.filename = filename

    def __getitem__(self, key):
        """
        See docstring of SpecFile.__getitem__
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
            try:
                (number, order) = map(int, key.split("."))
                scan_index = self.index(number, order)
            except (ValueError, SfErrScanNotFound, KeyError):
                # int() can raise a value error
                raise KeyError(msg + "\nValid keys: '" +
                               "', '".join(self.keys()) + "'")
            except AttributeError:
                # e.g. "AttrErr: 'float' object has no attribute 'split'"
                raise TypeError(msg)

        if not 0 <= scan_index < len(self):
            msg = "Scan index must be in range 0-%d" % (len(self) - 1)
            raise IndexError(msg)

        return PiezoScan(self, scan_index)


class PiezoScan(Scan):

    motordef = dict(pix="adcY", piy="adcX", piz="adcZ")

    def __init__(self, fast_specfile, scan_number):
        super().__init__(fast_specfile, scan_number)

        self.command = self.scan_header_dict['S']
        self.shape = int(self.command.split()[9]), int(self.command.split()[5])
        self.datetime = self.scan_header_dict['D']

    def get_roidata(self, counter):
        try:
            return self.data_column_by_name(counter).reshape(self.shape)
        except SfErrColNotFound:
            print('"{0}" is not a valid counter; available counters'
                  'are: {1}'.format(counter, self.labels))

    def get_pis(self):
        motor_names = self.command.split()[2], self.command.split()[6]
        motor1, motor2 = [self.data_column_by_name(
            self.motordef[x]).reshape(self.shape) for x in motor_names]
        return motor1, motor2

    def get_motorpos(self, motor_name):
        return self.motor_position_by_name(motor_name)

    def get_roipos(self):
        roipos = [x for x in self.file_header_dict['Ulima'].split('\n')][1:]
        roipos = np.array([x.split(' ') for x in roipos])
        roipos = {key: [int(x) for x in roipos[i, 2:]]
                  for key, i in zip(roipos[:, 0], range(roipos.shape[0]))}
        return roipos

    def get_edf_file(self):
        # regular expression matching the imageFile comment line
        _imgfile_pattern = ('^#C imageFile '
                            'dir\[(?P<dir>[^\]]*)\] '
                            'prefix\[(?P<prefix>[^\]]*)\] '
                            '(idxFmt\[(?P<idxFmt>[^\]]*)\] ){0,1}'
                            'nextNr\[(?P<nextNr>[^\]]*)\] '
                            'suffix\[(?P<suffix>[^\]]*)\]$')

        # find the image file line
        regx = re.compile(_imgfile_pattern)
        imgfile_match = [m for line in self.scan_header
                         if line.startswith('#C imageFile')
                         for m in [regx.match(line.strip())] if m]
        info = imgfile_match[0].groupdict()

        # return the image path
        nextnr_pattern = '{0:0>5}'
        edf_path = "{}/{}{}{}".format(info['dir'], info['prefix'],
                                      nextnr_pattern.format(info['nextNr']),
                                      info['suffix'])
        return edf_path

    def get_detcalib(self):
        # specify keys to look for
        converters = {
            'cen_pix_x': float,
            'cen_pix_y': float,
            'pixperdeg': float,
            'timestamp': str,
            'det_distance_CC': float,
            'mononrj': lambda nrj: float(nrj[:-3])  # Ends with keV
        }
        calibration = {}

        # Parse spec header to find calibration
        header = self.file_header
        for line in header:
            if line.startswith('#UDETCALIB ') or line.startswith('#UMONO '):
                params = line.split(' ')[1].strip().split(',')
                for item in params:
                    if '=' in item:
                        key, value = item.split('=')
                        if key in converters:
                            calibration[key] = converters[key](value)
        return calibration
