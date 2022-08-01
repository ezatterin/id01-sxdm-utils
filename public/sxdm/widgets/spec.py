"""
Various widgets to aid the analysis of SXDM data.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import ipywidgets as ipw

from matplotlib.widgets import MultiCursor, RectangleSelector
from IPython.display import display

from ..utils import get_detector_roilist
from ..plot import add_colorbar

mpl.rcParams["font.family"] = "Liberation Sans, sans-serif"


class RoiPlotter(object):
    """
    Explore the contents of a _fast_xxxxx.spec file containing one or more SXDM scans
    collected on id01.

    Parameters
    ----------
    fast_spec_file : `sxdm.io.FastSpecFile`
        Spec file opened via sxdm.io.FastSpecFile(path_to_specfile)
    detector : str
        The detector used during the experiment. For the moment only "maxipix" and
        "eiger" are supported. Defaults to "maxipix".

    Methods
    -------
    show : NoneType
        Returns the widget.
    """

    def __init__(self, fast_spec_file, detector="maxipix"):

        # init variables
        self.detector = detector
        self.fsf = fast_spec_file
        self.pscan = self.fsf[0]
        self.motors = self.pscan.motor_names
        self.rois, self.roi_init = get_detector_roilist(self.pscan, detector)

        # default ROI
        roidata_init = self.pscan.get_roidata(self.roi_init)

        # output widget to be filled with plt.figure
        self.figout = ipw.Output(layout=dict(border="2px solid grey"))

        ## figure
        with self.figout:
            self.fig, self.axs = plt.subplots(
                1, 2, figsize=(6, 2.8), sharex=True, sharey=True, layout="tight"
            )

        # roi images
        self.imgL, self.imgR = [ax.imshow(roidata_init) for ax in self.axs]
        pm = self.pscan.piezo_motor_names

        # labels etc
        _ = [add_colorbar(ax, im) for ax, im in zip(self.axs, [self.imgL, self.imgR])]
        _ = [a.set_xlabel("{} (um)".format(pm[0])) for a in self.axs]
        _ = self.axs[0].set_ylabel("{} (um)".format(pm[1]))
        _ = [a.set_title("mpx4int") for a in self.axs]

        ## widgets
        # layout of individual items - css properties
        items_layout = ipw.Layout(width="auto")

        # menu to select left ROI
        self.roiselL = ipw.Dropdown(
            options=self.rois,
            value=self.roi_init,
            layout=items_layout,
            description="Left ROI",
        )
        self.roiselL.observe(self._update_roi, names="value")

        # menu to select right ROI
        self.roiselR = ipw.Dropdown(
            options=self.rois,
            value=self.roi_init,
            layout=items_layout,
            description="Right ROI",
        )
        self.roiselR.observe(self._update_roi, names="value")

        # slider to select scan index
        idxsel = ipw.IntSlider(
            value=0,
            min=0,
            max=(len(self.fsf.keys()) - 1),
            step=1,
            layout=items_layout,
            description="Scan index",
        )
        idxsel.observe(self._update_pscan, names="value")

        # log scale the images?
        iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout, indent=False
        )
        iflog.observe(self._update_norm, names="value")

        # show a crosshair at the mouse position?
        ifmulti = ipw.Checkbox(
            value=False, description="Crosshair", layout=items_layout, indent=False
        )
        ifmulti.observe(self._add_crosshar, names="value")

        # group checkboxes
        ifs = ipw.HBox(
            [iflog, ifmulti],
            layout={
                "width": "auto",
                "flex_flow": "row nowrap",
                "justify_content": "center",
            },
        )

        # HTML table with motor specs
        self.specs = ipw.HTML()
        self.motorspecs = ipw.HTML()
        self._update_specs()

        view_motorspecs = ipw.Accordion([self.motorspecs])
        view_motorspecs.set_title(0, "View motors")
        view_motorspecs.selected_index = None
        view_motorspecs.layout = {"font-family": "Liberation Sans"}

        # group all widgets together
        self.selector = ipw.VBox(
            [self.roiselL, self.roiselR, idxsel, ifs, self.specs, view_motorspecs]
        )
        self.selector.layout = {
            "border": "2px solid grey",
            "width": "30%",
            "padding": "2px",
            "align-items": "stretch",
        }

    def show(self):
        """
        Displays widget.
        """

        display(
            ipw.HBox(
                [self.selector, self.figout],
                layout={"justify-content": "space-between"},
            )
        )

    # writes the HTML table with scan specs
    def _update_specs(self):

        angles = "eta,del,phi,nu".split(",")
        angles = [self.pscan.get_positioner(ang) for ang in angles]

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

        positions = {m: self.pscan.get_positioner(m) for m in self.motors}

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

    # updates extents of images based on pi coords
    def _update_piezo_coordinates(self):
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

    # updates the images
    def _update_pscan(self, change):
        scan_idx = change["new"]
        self.pscan = self.fsf[scan_idx]

        _ = [
            self._update_roi({"new": x.value, "owner": x})
            for x in (self.roiselL, self.roiselR)
        ]

        self._update_piezo_coordinates()
        self._update_specs()

    # updates the ROI based on selection
    def _update_roi(self, change):
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

    # updates norm and clims
    def _update_norm(self, change):
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

    def _add_crosshar(self, change):
        ismulti = change["new"]
        if ismulti:
            self.multi = MultiCursor(
                self.fig.canvas, self.axs, color="r", lw=0.7, horizOn=True
            )
        else:
            del self.multi


class FramesExplorer(object):
    def __init__(self, pscan, detector="maxipix", coms=None):

        """
        TODO!
        """

        ## init variables
        self.pscan = pscan
        self.detector = detector

        try:
            self.frames = pscan.frames
        except AttributeError:
            self.frames = pscan.get_detector_frames()

        self.frames = self.frames.reshape(*pscan.shape, *self.frames.shape[1:])
        self.rois, self.roi_init = get_detector_roilist(pscan, detector)
        self.m1, self.m2 = pscan.get_piezo_coordinates()
        self.row, self.col = 0, 0
        self.roi_idxs = np.s_[:, :]
        self.newroi = None

        # init figure widget
        self.figout = ipw.Output(layout=dict(border="2px solid grey"))
        with self.figout:
            self.fig, self.axs = plt.subplots(1, 2, figsize=(8, 2.5), layout="tight")

        # populate axes with images
        self.imgroi = self.axs[0].imshow(pscan.get_roidata(self.roi_init))
        self.imgframe = self.axs[1].imshow(
            self.frames[self.row, self.col, ...], cmap="magma"
        )

        # init cursor pos on imgroi
        _x, _y = self.m1[self.row, self.col], self.m2[self.row, self.col]
        self.curpos = self.axs[0].scatter(_x, _y, marker="x", c="r")

        # cbar and title
        _ = [
            add_colorbar(ax, im)
            for ax, im in zip(self.axs, [self.imgroi, self.imgframe])
        ]
        self.imgroi.axes.set_title("mpx4int")

        # connect to mpl event manager
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        # load COMs
        self.coms = coms
        if coms is not None:
            self.cy, self.cz = coms
            self.com = self.axs[1].scatter(self.cz, self.cy, marker="x", c="b")

        # widget layout - items
        items_layout = ipw.Layout(width="auto", justify_content="space-between")

        ## checkboxes
        self.iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout
        )
        self.iflog.observe(self._update_norm, names="value")

        self.ifrois = ipw.Checkbox(
            value=False, description="Show ROIs", layout=items_layout
        )
        self.ifrois.observe(self._add_rois, names="value")

        self.ifmakeroi = ipw.Checkbox(
            value=False, description="Define new ROI", layout=items_layout
        )
        self.ifmakeroi.observe(self._define_roi, names="value")

        # ROI selection for imgroi
        self.roisel = ipw.Dropdown(
            options=self.rois,
            value=self.roi_init,
            layout=items_layout,
            description="ROI",
        )
        self.roisel.observe(self._update_roi, names="value")

        # group widgets together
        self.widgets = ipw.HBox(
            [self.roisel, self.iflog, self.ifrois, self.ifmakeroi],
            layout=dict(border="2px solid grey"),
        )

        # ROI selector
        self.makeroi = RectangleSelector(
            self.axs[1],
            self._line_select_callback,
            useblit=True,
            button=[1, 3],  # disable middle button
            minspanx=5,
            minspany=5,
            spancoords="pixels",
            interactive=True,
        )

    def show(self):
        """
        Displays widget.
        """

        display(ipw.VBox([self.widgets, self.figout]))

    def _line_select_callback(self, eclick, erelease):
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
        self._update_norm({"new": self.iflog.value})

    def _define_roi(self, change):
        if change["new"]:
            self.makeroi.set_active(True)
            self.makeroi.set_visible(True)
        else:
            self.makeroi.set_active(False)
            self.makeroi.set_visible(False)

    def _update_plots(self):
        with self.figout:
            _frame = self.frames[self.row, self.col, ...]
            self.imgframe.set_data(_frame)
            self._update_norm({"new": self.iflog.value})  # updates also clim

            self.curpos.set_offsets([self.col, self.row])
            if self.coms is not None:
                _cy, _cz = self.cy[self.row, self.col], self.cz[self.row, self.col]
                self.com.set_offsets([_cz, _cy])

    def _on_click(self, event):
        if event.inaxes == self.axs[0]:
            self.col, self.row = [
                int(np.round(x, 0)) for x in (event.xdata, event.ydata)
            ]
            self._update_plots()
        else:
            pass

    def _on_key(self, event):
        if event.key in ["39", "right"]:
            self.col += 1
            self._update_plots()
        elif event.key in ["37", "left"]:
            self.col -= 1
            self._update_plots()
        elif event.key in ["40", "down"]:
            self.row += 1
            self._update_plots()
        elif event.key in ["38", "up"]:
            self.row -= 1
            self._update_plots()

    def _update_norm(self, change):
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
                except ValueError:
                    _ = im.set_norm(mpl.colors.LogNorm(0.1, c[1]))
        else:
            _ = [
                im.set_norm(mpl.colors.Normalize(*c))
                for im, c in zip((self.imgroi, self.imgframe), _clims)
            ]

    def _add_rois(self, change):
        global texts, patches

        roipos = self.pscan.get_roipos()
        roinames, _ = get_detector_roilist(self.pscan, self.detector)
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

    def _update_roi(self, change):
        roi = change["new"]
        roidata = self.pscan.get_roidata(roi)

        self.imgroi.set_data(roidata)
        self.imgroi.axes.set_title(roi)
        try:
            self.imgroi.set_clim(roidata.min(), roidata.max())
        except ValueError:
            self.imgroi.set_clim(0.1, roidata.max())
