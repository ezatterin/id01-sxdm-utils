import matplotlib as mpl
import matplotlib.pyplot as plt
import ipywidgets as ipw
import numpy as np
import h5py

from ..plot.utils import add_colorbar
from IPython.display import display
from matplotlib.widgets import RectangleSelector


class Inspect4DArray(object):
    def __init__(self, arr, fixed_clims=None):
        # arr is 4D - d0, d1, d2, d3

        self.ish5 = False if not isinstance(arr, h5py.Dataset) else True
        self.data = arr
        self.d0 = 30
        self.d1 = 30

        if not self.ish5:
            self.dir_space_data = self.data.sum(axis=(2, 3))
            self.rec_space_data = self.data.sum(axis=(0, 1))

        self.fixed_clims = fixed_clims

        self._init_fig()
        self._init_widgets()

    def _init_fig(self):
        self.figout = ipw.Output(
            layout=dict(border="2px solid grey", flex="4 1 0%", width="auto")
        )

        with plt.ioff():
            fig, ax = plt.subplots(1, 2, figsize=(8, 3.5))
        with self.figout:
            display(fig.canvas)

        self.lower_img = ax[0].imshow(self.dir_space_data, origin="lower")
        self.higher_img = ax[1].imshow(self.rec_space_data, origin="lower")

        self.dir_space_curpos = ax[0].scatter(0, 0, marker="x", c="r")
        self.rec_space_curpos = ax[1].scatter(0, 0, marker="x", c="r")

        for a in ax:
            add_colorbar(a, a.get_images()[0])

        ax[0].set_title("Sum over full detector space")
        ax[1].set_title("Sum over full sample space")

        fig.subplots_adjust(left=0.05, right=0.9, wspace=0.4)
        fig.canvas.mpl_connect("button_press_event", self._onclick_callback)
        fig.canvas.mpl_connect("key_press_event", self._onkey)

        self.fig, self.ax = fig, ax

    def _init_widgets(self):
        # ROI selectors
        self.custom_roi_selectors = []
        for i in range(2):
            self.custom_roi_selectors.append(
                RectangleSelector(
                    self.ax[i],
                    self._custom_roi_callback,
                    useblit=True,
                    button=[1, 3],  # disable middle button
                    minspanx=5,
                    minspany=5,
                    spancoords="pixels",
                    interactive=True,
                )
            )
        [s.set_active(False) for s in self.custom_roi_selectors]

        # log scale?
        self.iflog = ipw.Checkbox(value=False, description="Log Intensity")
        self.iflog.observe(self._update_norm, names="value")

        # custom sample space roi?
        self.if01roi = ipw.Checkbox(value=False, description="Define sample space ROI")
        self.if01roi.observe(self._is_d01_roi, names="value")

        # custom detector space roi?
        self.if23roi = ipw.Checkbox(
            value=False, description="Define detector space ROI"
        )
        self.if23roi.observe(self._is_d23_roi, names="value")

        for w in (self.iflog, self.if01roi, self.if23roi):
            w.layout = ipw.Layout(width="auto")
            w.indent = False

        # group widgets together
        self.widgets = ipw.VBox(
            [self.iflog, self.if01roi, self.if23roi],
            layout=dict(
                border="2px solid grey",
                align_items="stretch",
                flex="1 1 0%",
                width="auto",
            ),
        )

    def _onkey(self, event):
        if event.key in ["39", "right"]:
            self.col += 1
            self._update_plots()
        elif event.key in ["37", "left"]:
            self.col -= 1
            self._update_plots()
        elif event.key in ["40", "down"]:
            self.row -= 1
            self._update_plots()
        elif event.key in ["38", "up"]:
            self.row += 1
            self._update_plots()

    def _is_d01_roi(self, change):
        if change["new"]:
            self.custom_roi_selectors[0].set_active(True)
            self.custom_roi_selectors[0].set_visible(True)
        else:
            self.custom_roi_selectors[0].set_active(False)
            self.custom_roi_selectors[0].set_visible(False)

    def _is_d23_roi(self, change):
        if change["new"]:
            self.custom_roi_selectors[1].set_active(True)
            self.custom_roi_selectors[1].set_visible(True)
        else:
            self.custom_roi_selectors[1].set_active(False)
            self.custom_roi_selectors[1].set_visible(False)

    def _custom_roi_callback(self, eclick, erelease):
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
        self.custom_roi = False

        if event.inaxes == self.ax[0] and self.if01roi.value is False:
            self.sel_ax_idx = 0
            x, y = event.xdata, event.ydata
        elif event.inaxes == self.ax[1] and self.if23roi.value is False:
            self.sel_ax_idx = 1
            x, y = event.xdata, event.ydata
        else:
            return

        self.col, self.row = [int(np.round(p, 0)) for p in (x, y)]
        self._update_plots()

    def _update_plots(self):
        if not self.custom_roi:
            if self.sel_ax_idx == 0:
                self.rec_space_data = self.data[self.row, self.col, :, :]
                self.higher_img.set_data(self.rec_space_data)
                self.dir_space_curpos.set_offsets([self.col, self.row])

                self.ax[0].set_title("Index: [{}, {}]".format(self.row, self.col))
                self.ax[1].set_title("Intensity @ [{}, {}]".format(self.row, self.col))

            elif self.sel_ax_idx == 1:
                self.dir_space_data = self.data[:, :, self.row, self.col]
                self.lower_img.set_data(self.dir_space_data)
                self.rec_space_curpos.set_offsets([self.col, self.row])

                self.ax[1].set_title("Index: [{}, {}]".format(self.row, self.col))
                self.ax[0].set_title("Features @ [{}, {}]".format(self.row, self.col))

        else:
            if self.sel_ax_idx == 0:
                self.rec_space_data = self.data[
                    self.row0 : self.row1, self.col0 : self.col1, :, :
                ].sum(axis=(0, 1))
                self.higher_img.set_data(self.rec_space_data)
            elif self.sel_ax_idx == 1:
                self.dir_space_data = self.data[
                    :, :, self.row0 : self.row1, self.col0 : self.col1
                ].sum(axis=(2, 3))
                self.lower_img.set_data(self.dir_space_data)

            self.ax[self.sel_ax_idx].set_title(
                "Indexes: [{}:{}, {}:{}]".format(
                    self.row0, self.row1, self.col0, self.col1
                )
            )

        self._update_norm({"new": self.iflog.value})

    def _update_norm(self, change):
        islog = change["new"]
        whichax = change.get("axes", self.ax)

        for im in [a.get_images()[0] for a in whichax]:
            data = im.get_array()

            if self.fixed_clims is None:
                try:
                    _clims = [data[data.nonzero()].min(), data.max()]
                except ValueError:  # only 0s
                    _clims = [0, 1]
            else:
                _clims = self.fixed_clims

            self.clims = _clims

            if islog:
                try:
                    _ = im.set_norm(mpl.colors.LogNorm(*_clims))
                except ValueError as err:
                    print(f"{err}, setting lower bound to 0.1")
                    _ = im.set_norm(mpl.colors.LogNorm(0.1, _clims[1]))
            else:
                _ = im.set_norm(mpl.colors.Normalize(*_clims))

    def show(self):
        display(
            ipw.HBox([self.widgets, self.figout], layout=dict(align_items="stretch"))
        )
