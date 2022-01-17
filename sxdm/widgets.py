"""
Various widgets to aid the analysis of SXDM data.
"""

from .utils import load_detector_roilist

import sxdm
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

import ipywidgets as ipw
from matplotlib.widgets import MultiCursor, RectangleSelector

mpl.rcParams["font.family"] = "Liberation Sans, sans-serif"


class RoiPlotter(object):
    def __init__(self, fast_spec_file, detector="maxipix"):

        figout = ipw.Output(layout=dict(border="2px solid grey"))

        # init
        self.detector = detector
        self.fsf = fast_spec_file

        self.pscan = self.fsf[0]
        self.motors = self.pscan.motor_names

        self.rois, self.roi_init = load_detector_roilist(self.pscan, detector)

        roidata_init = self.pscan.get_roidata(self.roi_init)

        # figure
        with figout:
            self.fig, self.axs = plt.subplots(
                1, 2, figsize=(6, 2.8), sharex=True, sharey=True
            )

        self.imgL, self.imgR = [ax.imshow(roidata_init) for ax in self.axs]

        _ = [
            sxdm.plot.add_colorbar(ax, im)
            for ax, im in zip(self.axs, [self.imgL, self.imgR])
        ]

        pm = self.pscan.piezo_motor_names
        _ = [a.set_xlabel("{} (um)".format(pm[0])) for a in self.axs]
        _ = self.axs[0].set_ylabel("{} (um)".format(pm[1]))

        _ = [a.set_title("mpx4int") for a in self.axs]

        self.fig.tight_layout()

        # widgets
        items_layout = ipw.Layout(width="auto")

        self.roiselL = ipw.Dropdown(
            options=self.rois,
            value=self.roi_init,
            layout=items_layout,
            description="Left ROI",
        )
        self.roiselL.observe(self.update_roi, names="value")

        self.roiselR = ipw.Dropdown(
            options=self.rois,
            value=self.roi_init,
            layout=items_layout,
            description="Right ROI",
        )
        self.roiselR.observe(self.update_roi, names="value")

        idxsel = ipw.IntSlider(
            value=0,
            min=0,
            max=(len(self.fsf.keys()) - 1),
            step=1,
            layout=items_layout,
            description="Scan index",
        )
        idxsel.observe(self.update_pscan, names="value")

        iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout, indent=False
        )
        iflog.observe(self.update_norm, names="value")

        ifmulti = ipw.Checkbox(
            value=False, description="Crosshair", layout=items_layout, indent=False
        )
        ifmulti.observe(self.add_crosshair, names="value")

        ifs = ipw.HBox(
            [iflog, ifmulti],
            layout={
                "width": "auto",
                "flex_flow": "row nowrap",
                "justify_content": "center",
            },
        )

        self.specs = ipw.HTML()
        self.motorspecs = ipw.HTML()
        self.update_specs()

        view_motorspecs = ipw.Accordion([self.motorspecs])
        view_motorspecs.set_title(0, "View motors")
        view_motorspecs.selected_index = None
        view_motorspecs.layout = {"font-family": "Liberation Sans"}

        selector = ipw.VBox(
            [self.roiselL, self.roiselR, idxsel, ifs, self.specs, view_motorspecs]
        )
        selector.layout = {
            "border": "2px solid grey",
            "width": "30%",
            "padding": "2px",
            "align-items": "stretch",
        }

        self.show = ipw.HBox(
            [selector, figout], layout={"justify-content": "space-between"}
        )

    def update_specs(self):

        angles = "eta,del,phi,nu".split(",")
        angles = [self.pscan.get_motorpos(ang) for ang in angles]

        specs = [
            "<div>",
            "<style>",
            "    .specs tbody {",
            "        font-family: Liberation Sans, sans-serif ;",
            "        font-size: small ;",
            "        text-align: right ;",
            "    }",
            "</style>",
            '<table class="specs rendered_html output_html">',
            "  <tbody>",
            "    <tr>",
            "      <th>Command</th>",
            "      <td>{}</td>".format(self.pscan.command),
            "    </tr>",
            "    <tr>",
            "      <th>Datetime</th>",
            "      <td>{}</td>".format(self.pscan.datetime),
            "    </tr>",
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        specs = "\n".join(specs)
        self.specs.value = specs

        positions = {m: self.pscan.get_motorpos(m) for m in self.motors}

        motorspecs = [
            "<div>",
            '<table class="specs rendered_html output_html">',
            "  <tbody>",
        ]

        for mot, val in positions.items():
            _insert = [
                "    <tr>",
                "      <th>{}</th>".format(mot),
                "      <td>{:.5f}</td>".format(val),
                "    </tr>",
            ]
            _ = [motorspecs.append(x) for x in _insert]

        motorspecs += ["  </tbody>", "</table>", "</div>"]

        motorspecs = "\n".join(motorspecs)
        self.motorspecs.value = motorspecs

    def update_piezo_coordinates(self):
        try:
            m1, m2 = self.pscan.get_piezo_coordinates()
            for img in (self.imgL, self.imgR):
                img.set_extent([m1.min(), m1.max(), m2.min(), m2.max()])
        except ValueError:
            command = self.pscan.command.split(" ")
            m1min, m1max = [int(command[i]) for i in (3, 4)]
            m2min, m2max = [int(command[i]) for i in (7, 8)]
            for img in (self.imgL, self.imgR):
                img.set_extent([m1min, m1max, m2min, m2max])

    def update_pscan(self, change):
        scan_idx = change["new"]
        self.pscan = self.fsf[scan_idx]

        _ = [
            self.update_roi({"new": x.value, "owner": x})
            for x in (self.roiselL, self.roiselR)
        ]

        self.update_piezo_coordinates()
        self.update_specs()
        self.fig.tight_layout()

    def update_roi(self, change):
        roi = change["new"]
        roidata = self.pscan.get_roidata(roi)

        menu = change["owner"]
        img = self.imgL if menu == self.roiselL else self.imgR

        img.set_data(roidata)
        img.axes.set_title(roi)
        try:
            img.set_clim(roidata.min(), roidata.max())
        except ValueError:
            img.set_clim(0.1, roidata.max())

    def update_norm(self, change):
        islog = change["new"]

        _clims = [
            (im.get_array().min(), im.get_array().max())
            for im in (self.imgL, self.imgR)
        ]
        self.clims = _clims
        if islog:
            for im, c in zip((self.imgL, self.imgR), _clims):
                try:
                    _ = im.set_norm(mpl.colors.LogNorm(*c))
                except ValueError as err:
                    print("{}, setting lower bound to 0.1".format(err))
                    _ = im.set_norm(mpl.colors.LogNorm(0.1, c[1]))
        else:
            _ = [
                im.set_norm(mpl.colors.Normalize(*c))
                for im, c in zip((self.imgL, self.imgR), _clims)
            ]

    def add_crosshair(self, change):
        ismulti = change["new"]
        if ismulti:
            self.multi = MultiCursor(
                self.fig.canvas, self.axs, color="r", lw=0.7, horizOn=True
            )
        else:
            del self.multi


class FramesExplorer(object):
    def __init__(self, pscan, detector="maxipix", coms=None, qconvert=False):

        # init data
        self.pscan = pscan
        self.detector = detector
        #         self.frames = frames.reshape(*pscan.shape, *frames.shape[1:])
        try:
            self.frames = pscan.frames
        except AttributeError:
            self.frames = pscan.get_detector_frames()
        self.frames = self.frames.reshape(*pscan.shape, *self.frames.shape[1:])

        self.rois, self.roi_init = load_detector_roilist(pscan, detector)
        self.m1, self.m2 = pscan.get_piezo_coordinates()

        self.row, self.col = 0, 0

        self.roi_idxs = np.s_[:, :]
        self.newroi = None

        # init figure widget
        self.figout = ipw.Output(layout=dict(border="2px solid grey"))
        with self.figout:
            self.fig, self.axs = plt.subplots(1, 2, figsize=(8, 2.5))

        # populate axes
        self.imgroi = self.axs[0].imshow(pscan.get_roidata(self.roi_init))
        self.imgframe = self.axs[1].imshow(
            self.frames[self.row, self.col, ...], cmap="magma"
        )

        _x, _y = self.m1[self.row, self.col], self.m2[self.row, self.col]
        self.curpos = self.axs[0].scatter(_x, _y, marker="x", c="r")

        _ = [
            sxdm.plot.add_colorbar(ax, im)
            for ax, im in zip(self.axs, [self.imgroi, self.imgframe])
        ]
        self.imgroi.axes.set_title("mpx4int")

        # connect to mpl event manager
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

        self.coms = coms
        if coms is not None:
            self.cy, self.cz = coms
            self.com = self.axs[1].scatter(self.cz, self.cy, marker="x", c="b")

        # widgets
        items_layout = ipw.Layout(width="auto", justify_content="space-between")

        self.iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout
        )
        self.iflog.observe(self.update_norm, names="value")

        self.ifrois = ipw.Checkbox(
            value=False, description="Show ROIs", layout=items_layout
        )
        self.ifrois.observe(self.add_rois, names="value")

        self.ifmakeroi = ipw.Checkbox(
            value=False, description="Define new ROI", layout=items_layout
        )
        self.ifmakeroi.observe(self.define_roi, names="value")

        self.roisel = ipw.Dropdown(
            options=self.rois,
            value=self.roi_init,
            layout=items_layout,
            description="ROI",
        )
        self.roisel.observe(self.update_roi, names="value")

        self.widgets = ipw.HBox(
            [self.roisel, self.iflog, self.ifrois, self.ifmakeroi],
            layout=dict(border="2px solid grey"),
        )

        # ROI selector
        self.makeroi = RectangleSelector(
            self.axs[1],
            self.line_select_callback,
            useblit=True,
            button=[1, 3],  # disable middle button
            minspanx=5,
            minspany=5,
            spancoords="pixels",
            interactive=True,
        )

        # output
        self.show = ipw.VBox([self.widgets, self.figout])

    def line_select_callback(self, eclick, erelease):
        x, y = self.makeroi.corners
        x = [int(np.round(m, 0)) for m in x]
        y = [int(np.round(m, 0)) for m in y]

        col0, col1 = x[0], x[1]
        row0, row1 = y[0], y[-1]

        self.roi_idxs = np.s_[:, :, row0:row1, col0:col1]
        self.roidata_new = self.frames[self.roi_idxs].sum(axis=(2, 3))
        self.imgroi.axes.set_title(
            "custom: {}:{}, {}:{}".format(row0, row1, col0, col1)
        )

        self.imgroi.set_data(self.roidata_new)
        self.update_norm({"new": self.iflog.value})

    def define_roi(self, change):
        if change["new"]:
            self.makeroi.set_active(True)
            self.makeroi.set_visible(True)
        else:
            self.makeroi.set_active(False)
            self.makeroi.set_visible(False)

    def update_plots(self):
        with self.figout:
            _frame = self.frames[self.row, self.col, ...]
            self.imgframe.set_data(_frame)
            self.update_norm({"new": self.iflog.value})  # updates also clim

            self.curpos.set_offsets([self.col, self.row])
            if self.coms is not None:
                _cy, _cz = self.cy[self.row, self.col], self.cz[self.row, self.col]
                self.com.set_offsets([_cz, _cy])

    def on_click(self, event):
        if event.inaxes == self.axs[0]:
            self.col, self.row = [
                int(np.round(x, 0)) for x in (event.xdata, event.ydata)
            ]
            self.update_plots()
        else:
            pass

    def on_key(self, event):
        if event.key == "39":
            self.col += 1
            self.update_plots()
        elif event.key == "37":
            self.col -= 1
            self.update_plots()
        elif event.key == "40":
            self.row += 1
            self.update_plots()
        elif event.key == "38":
            self.row -= 1
            self.update_plots()

    def update_norm(self, change):
        islog = change["new"]

        _clims = [
            (im.get_array().min(), im.get_array().max())
            for im in (self.imgroi, self.imgframe)
        ]
        self.clims = _clims
        if islog:
            for im, c in zip((self.imgroi, self.imgframe), _clims):
                try:
                    _ = im.set_norm(mpl.colors.LogNorm(*c))
                except ValueError as err:
                    _ = im.set_norm(mpl.colors.LogNorm(0.1, c[1]))
        else:
            _ = [
                im.set_norm(mpl.colors.Normalize(*c))
                for im, c in zip((self.imgroi, self.imgframe), _clims)
            ]

    def add_rois(self, change):
        global texts, patches

        roipos = self.pscan.get_roipos()
        roinames, _ = load_detector_roilist(self.pscan, self.detector)
        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"] * 2

        if change["new"]:
            texts, patches = [], []
            for i, r in enumerate(roinames):
                roi = roipos[r]
                _rect = mpl.patches.Rectangle(
                    (roi[0], roi[2]),
                    roi[1] - roi[0],
                    roi[3] - roi[2],
                    fill=False,
                    ec=colors[i],
                )
                self.axs[1].add_patch(_rect)
                _text = self.axs[1].annotate(
                    r,
                    (roi[0] + 15, roi[2] + 20),
                    color=colors[i],
                    fontsize="x-small",
                    weight="bold",
                )

                texts.append(_text)
                patches.append(_rect)

        elif not change["new"]:
            for x in texts + patches:
                x.remove()

            self.fig.canvas.draw_idle()

    def update_roi(self, change):
        roi = change["new"]
        roidata = self.pscan.get_roidata(roi)

        self.imgroi.set_data(roidata)
        self.imgroi.axes.set_title(roi)
        try:
            self.imgroi.set_clim(roidata.min(), roidata.max())
        except ValueError:
            self.imgroi.set_clim(0.1, roidata.max())
