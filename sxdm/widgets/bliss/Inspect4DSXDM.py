import numpy as np
import h5py
import ipywidgets as ipw
import matplotlib as mpl
import os

from tqdm.notebook import tqdm

from sxdm.widgets import Inspect4DArray
from ...io.bliss import (
    get_detector_aliases,
    get_scan_shape,
    get_sxdm_frame_sum,
    get_sxdm_pos_sum,
    get_roi_pos,
    get_piezo_motor_names,
)
from ...io.utils import list_available_counters

from id01lib.xrd.detectors import MaxiPix, MaxiPixGaAs, Eiger2M

_det_aliases = dict(mpx1x4=MaxiPix(), mpxgaas=MaxiPixGaAs(), eiger2M=Eiger2M())


class Inspect4DSXDM(Inspect4DArray):
    """
    Plot SXDM data acquired during a BLISS experiment on ID01. Call with .show().
    """

    def __init__(self, path_dset, scan_no, detector=None):
        """
        Parameters
        ----------
        path_dset : str
            Path to the BLISS dataset .h5 file.
        scan_no : str
            The scan number of the SXDM scan, e.g. 1.1.
        detector : str, optional
            The alias of the detector used. If None it is automatically selected from
            the dataset file.
        """

        detlist = get_detector_aliases(path_dset, scan_no)
        if detector is None:
            detector = detlist[0]
        if detector not in detlist:
            raise ValueError(
                f"Detector {detector} not in data file. Available detectors are: {detlist}."
            )

        self.scan_shape = get_scan_shape(path_dset, scan_no)
        self.det_shape = _det_aliases[detector].pixnum

        self.dir_space_data = get_sxdm_pos_sum(
            path_dset, scan_no, detector=detector, pbar=False
        ).reshape(self.scan_shape)
        self.rec_space_data = get_sxdm_frame_sum(
            path_dset, scan_no, detector=detector, pbar=False
        )

        self.path_dset = path_dset
        self.scan_no = scan_no
        self.detector = detector

        with h5py.File(self.path_dset, "r") as h5f:
            arr = h5f[f"{self.scan_no}/measurement/{self.detector}"]

            super().__init__(arr)

            self.rec_space_curpos.remove()
            self.dir_space_curpos.set_offsets(
                [s // 2 for s in self.dir_space_data.shape]
            )

        m0n, m1n = get_piezo_motor_names(path_dset, scan_no)

        self.ax[0].set_xlabel(f"{m0n} (pixels)")
        self.ax[0].set_ylabel(f"{m1n} (pixels)")

        self.ax[1].invert_yaxis()

        self.ax[1].set_xlabel("detector x (pixels)")
        self.ax[1].set_ylabel("detector y (pixels)")
        self.fig.suptitle(f"{os.path.basename(path_dset)} #{self.scan_no}", y=1.0)

        self._show_rois = ipw.Checkbox(value=False, description="Show experiment ROIs")
        self._show_rois.observe(self._add_rois, names="value")
        self._show_rois.layout = ipw.Layout(width="auto")
        self._show_rois.indent = False

        self._pbar01 = tqdm(display=False)
        self._pbar23 = tqdm(display=False)

        self.iflog.value = True

        self.widgets.children = tuple(
            list(self.widgets.children)
            + [self._show_rois, self._pbar01.container, self._pbar23.container]
        )

    def _custom_roi_callback(self, eclick, erelease):
        with self.figout:
            self.custom_roi = True

            if eclick.inaxes == self.ax[0]:
                sel = self.custom_roi_selectors[0]
                self.sel_ax_idx = 0
            elif eclick.inaxes == self.ax[1]:
                sel = self.custom_roi_selectors[1]
                self.sel_ax_idx = 1

            x, y = sel.corners
            x = [int(np.round(m, 0)) for m in x]
            y = [int(np.round(m, 0)) for m in y]

            self.col0, self.col1 = x[0], x[1]
            self.row0, self.row1 = y[0], y[-1]
            self._update_plots()

    def _onclick_callback(self, event):
        with self.figout:
            self.custom_roi = False

            # does not fire if zooming, panning etc.
            if self.fig.canvas.manager.toolbar.mode.name == "NONE":
                if event.inaxes == self.ax[0] and self.if01roi.value is False:
                    self.sel_ax_idx = 0
                    x, y = event.xdata, event.ydata
                elif event.inaxes == self.ax[1] and self.if23roi.value is False:
                    # not doing anything for the moment as a single pixel on the
                    # detector does not really correspond to much on the sample
                    # self.sel_ax_idx = 1
                    # x, y = event.xdata, event.ydata
                    return
                else:
                    return
            else:
                return

            self.col, self.row = [int(np.round(p, 0)) for p in (x, y)]
            self._update_plots()

    def _update_plots(self):
        with self.figout:
            # single click?
            if not self.custom_roi:
                with h5py.File(self.path_dset, "r") as h5f:
                    arr = h5f[f"{self.scan_no}/measurement/{self.detector}"]
                    if self.sel_ax_idx == 0:
                        idx = self.row * self.scan_shape[1] + self.col

                        self.rec_space_data = arr[idx, :, :]
                        self.higher_img.set_data(self.rec_space_data)
                        self.dir_space_curpos.set_offsets([self.col, self.row])

                        self.ax[0].set_title(
                            "Index: [{}, {}]".format(self.row, self.col)
                        )
                        self.ax[1].set_title(
                            "Intensity @ [{}, {}]".format(self.row, self.col)
                        )

                    # the following is never firing for the moment,
                    # see _onclick_callback. self.sel_ax_idx is never set to 1
                    # when self.custom_roi=False
                    elif self.sel_ax_idx == 1:
                        self.dir_space_data = arr[:, self.row, self.col].reshape(
                            self.scan_shape
                        )
                        self.lower_img.set_data(self.dir_space_data)
                        self.rec_space_curpos.set_offsets([self.col, self.row])

                        self.ax[1].set_title(
                            "Index: [{}, {}]".format(self.row, self.col)
                        )
                        self.ax[0].set_title(
                            "Features @ [{}, {}]".format(self.row, self.col)
                        )

            # using the roi widget?
            else:
                if self.sel_ax_idx == 0:
                    mask = np.ones(self.scan_shape, dtype="bool")
                    mask[self.row0 : self.row1, self.col0 : self.col1] = False

                    try:
                        self.rec_space_data = get_sxdm_frame_sum(
                            self.path_dset,
                            self.scan_no,
                            mask_sample=mask,
                            detector=self.detector,
                            pbar=self._pbar01,
                        )
                    except ValueError:  # mask is empty
                        return

                    self.higher_img.set_data(self.rec_space_data)
                    self.mask_sample = mask
                    self._pbar01.reset()  # TODO not working!

                elif self.sel_ax_idx == 1:
                    mask = np.ones(self.det_shape, dtype="bool")
                    mask[self.row0 : self.row1, self.col0 : self.col1] = False

                    try:
                        self.dir_space_data = get_sxdm_pos_sum(
                            self.path_dset,
                            self.scan_no,
                            mask_detector=mask,
                            detector=self.detector,
                            pbar=self._pbar23,
                        ).reshape(self.scan_shape)
                    except ValueError:  # mask is empty
                        return

                    self.lower_img.set_data(self.dir_space_data)
                    self.mask_detector = mask
                    self._pbar23.reset()  # TODO not working!

                self.ax[self.sel_ax_idx].set_title(
                    "Indexes: [{}:{}, {}:{}]".format(
                        self.row0, self.row1, self.col0, self.col1
                    )
                )

            i = 0 if self.sel_ax_idx == 1 else 1
            self._update_dict = {
                "new": self.iflog.value,
                "axes": [self.ax[i]],
            }
            self._update_norm(self._update_dict)

    def _add_rois(self, change):
        roi_names = [
            m
            for m in list_available_counters(self.path_dset, self.scan_no)
            if self.detector in m
        ]
        roi_names = [
            x
            for x in roi_names
            if not any([s in x for s in "avg,max,min,std".split(",")])
        ]
        roi_names = [x.split("_")[-1] for x in roi_names]
        roi_names.remove(self.detector)

        roipos = get_roi_pos(
            self.path_dset, self.scan_no, roi_names, detector=self.detector
        )

        if change["new"]:
            self._texts, self._patches = [], []
            for name, c in zip(roipos.keys(), mpl.colors.TABLEAU_COLORS):
                roi = roipos[name]
                box = mpl.patches.Rectangle(roi[:2], *roi[2:], fill=None, ec=c)
                _text = self.ax[1].add_patch(box)
                _rect = self.ax[1].text(
                    *[x - 5 for x in roi[:2]],
                    name,
                    size="small",
                    c=c,
                )

                self._texts.append(_text)
                self._patches.append(_rect)

        elif not change["new"]:
            for x in self._texts + self._patches:
                x.remove()

            self.fig.canvas.draw_idle()
