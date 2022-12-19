import numpy as np
import h5py

from sxdm.widgets import Inspect4DArray
from ...io.bliss import (
    get_detector_aliases,
    get_scan_shape,
    get_sxdm_frame_sum,
    get_sxdm_pos_sum,
)

from id01lib.xrd.detectors import MaxiPix, MaxiPixGaAs, Eiger2M

from tqdm.auto import tqdm
from functools import partialmethod

tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)

_det_aliases = dict(mpx1x4=MaxiPix(), mpxgaas=MaxiPixGaAs(), eiger2M=Eiger2M())


class Inspect4DSXDM(Inspect4DArray):
    def __init__(self, path_dset, scan_no, detector="mpx1x4"):

        detlist = get_detector_aliases(path_dset, scan_no)
        if detector not in detlist:
            raise ValueError(
                f"Detector {detector} not in data file. Available detectors are: {detlist}."
            )

        self.scan_shape = get_scan_shape(path_dset, scan_no)
        self.det_shape = _det_aliases[detector].pixnum

        self.lower_data = get_sxdm_pos_sum(path_dset, scan_no).reshape(self.scan_shape)
        self.higher_data = get_sxdm_frame_sum(path_dset, scan_no)

        self.path_dset = path_dset
        self.scan_no = scan_no
        self.detector = detector

        with h5py.File(self.path_dset, "r") as h5f:
            arr = h5f[f"{self.scan_no}/measurement/{self.detector}"]

        super().__init__(arr)

    def _custom_roi_callback(self, eclick, erelease):
        with self.figout:
            self.custom_roi = True

            if eclick.inaxes == self.ax[0]:
                sel = self.custom_roi_selectors[0]
                self.idx = 0
            elif eclick.inaxes == self.ax[1]:
                sel = self.custom_roi_selectors[1]
                self.idx = 1

            x, y = sel.corners
            x = [int(np.round(m, 0)) for m in x]
            y = [int(np.round(m, 0)) for m in y]

            self.col0, self.col1 = x[0], x[1]
            self.row0, self.row1 = y[0], y[-1]
            self._update_plots()

    def _onclick_callback(self, event):
        with self.figout:
            self.custom_roi = False

            if event.inaxes == self.ax[0] and self.if01roi.value is False:
                self.idx = 0
                x, y = event.xdata, event.ydata
            elif event.inaxes == self.ax[1] and self.if23roi.value is False:
                self.idx = 1
                x, y = event.xdata, event.ydata
            else:
                return

            self.col, self.row = [int(np.round(p, 0)) for p in (x, y)]
            self._update_plots()

    def _update_plots(self):
        with self.figout:
            if not self.custom_roi:
                with h5py.File(self.path_dset, "r") as h5f:
                    arr = h5f[f"{self.scan_no}/measurement/{self.detector}"]
                    if self.idx == 0:
                        idx = self.row * self.scan_shape[1] + self.col

                        self.higher_data = arr[idx, :, :]
                        self.higher_img.set_data(self.higher_data)
                        self.lower_curpos.set_offsets([self.col, self.row])

                        self.ax[0].set_title(
                            "Index: [{}, {}]".format(self.row, self.col)
                        )
                        self.ax[1].set_title(
                            "Intensity @ [{}, {}]".format(self.row, self.col)
                        )

                    elif self.idx == 1:
                        self.lower_data = arr[:, self.row, self.col]
                        self.lower_img.set_data(
                            self.lower_data.reshape(self.scan_shape)
                        )
                        self.higher_curpos.set_offsets([self.col, self.row])

                        self.ax[1].set_title(
                            "Index: [{}, {}]".format(self.row, self.col)
                        )
                        self.ax[0].set_title(
                            "Features @ [{}, {}]".format(self.row, self.col)
                        )

            else:
                if self.idx == 0:
                    mask = np.zeros(self.scan_shape, dtype="bool")
                    mask[self.row0 : self.row1, self.col0 : self.col1] = True

                    print("\rLoading...", flush=True, end="")
                    self.higher_data = get_sxdm_frame_sum(
                        self.path_dset, self.scan_no, mask_direct=mask
                    )
                    print("\rDone!      ", flush=True, end="")
                    self.higher_img.set_data(self.higher_data)

                elif self.idx == 1:
                    mask = np.ones(self.det_shape, dtype="bool")
                    mask[self.row0 : self.row1, self.col0 : self.col1] = False

                    self.lower_data = get_sxdm_pos_sum(
                        self.path_dset, self.scan_no, mask_reciprocal=mask
                    )
                    self.lower_img.set_data(self.lower_data.reshape(self.scan_shape))

                self.ax[self.idx].set_title(
                    "Indexes: [{}:{}, {}:{}]".format(
                        self.row0, self.row1, self.col0, self.col1
                    )
                )

            self._update_norm({"new": self.iflog.value})
