import h5py
import ipywidgets as ipw
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

from matplotlib.widgets import Cursor
from IPython.display import display
from silx.io.h5py_utils import retry

from ..plot import add_colorbar
from ..io.bliss import get_roidata, get_motorpos, get_command, get_datetime


class InspectROI(object):
    def __init__(
        self,
        path_h5,
        default_roi="mpx1x4_mpx4int",
        roilist=None,
        init_scan_no=None,
    ):
        self.roiname = default_roi
        self.path_h5 = path_h5

        # get list of rois + other stuff
        with h5py.File(path_h5, "r") as h5f:

            nscans = len(list(h5f.keys()))
            scan_idxs = range(1, nscans + 1)
            commands = [h5f[f"{s}.1/title"][()].decode() for s in scan_idxs]

            self._scan_nos = [
                f"{s}.1" for s, c in zip(scan_idxs, commands) if "sxdm" in c
            ]
            self._commands = {s: h5f[f"{s}/title"][()].decode() for s in self._scan_nos}

            self.scan_no = self._scan_nos[0] if init_scan_no is None else init_scan_no
            self.command = self._commands[self.scan_no]

            counters = list(h5f[f"{self.scan_no}/measurement"].keys())
            self.roilist = counters if roilist is None else roilist

        # default roi data and motors
        self.roidata = get_roidata(
            path_h5, self._scan_nos[0], self.roiname, return_pi_motors=False
        )

        # output widget to be filled with plt.figure
        self.figout = ipw.Output(layout=dict(border="2px solid grey"))

        self._init_fig()
        self._init_widgets()

    def _init_fig(self):  # mpl

        with self.figout:
            fig, ax = plt.subplots(1, 1, figsize=(4, 4), layout="tight")

        self.fig, self.ax = fig, ax
        self.img = ax.imshow(self.roidata, origin="lower")
        self._get_motor_names()
        self._update_piezo_coordinates()

        # labels etc
        _ = add_colorbar(ax, self.img)
        _ = ax.set_xlabel(f"{self.m1name} (um)")
        _ = ax.set_ylabel(f"{self.m2name} (um)")
        _ = ax.set_title(f"#{self.scan_no} - {self.roiname}")

        # connect to mpl event manager
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    def _init_widgets(self):

        # layout of individual items - css properties
        items_layout = ipw.Layout(width="auto")

        # menu to select left ROI
        self.roisel = ipw.Dropdown(
            options=self.roilist,
            value=self.roiname,
            layout=items_layout,
            description="ROI:",
        )
        self.roisel.observe(self._update_roi, names="value")

        # slider to select scan index
        idxsel = ipw.IntSlider(
            value=0,
            min=0,
            max=(len(self._scan_nos) - 1),
            step=1,
            layout=items_layout,
            description="Scan index",
        )
        idxsel.observe(self._update_scan, names="value")

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
            [self.roisel, idxsel, ifs, self.specs, view_motorspecs]
        )
        self.selector.layout = {
            "border": "2px solid grey",
            "width": "30%",
            "padding": "2px",
            "align-items": "stretch",
        }

    def _on_click(self, event):  # mpl
        with self.figout:
            if event.inaxes == self.ax:
                x, y = event.xdata, event.ydata
                m1n, m2n = self.m1name, self.m2name

                msg = f"You clicked: {m1n},{x:.4f}, {m2n},{y:.4f}"
                print(msg)
            else:
                pass

    def _add_crosshar(self, change):  # mpl
        ismulti = change["new"]
        if ismulti:
            self.multi = Cursor(self.ax, color="r", lw=0.7, useblit=True)
        else:
            del self.multi

    @retry()
    def _update_roi(self, change):  # mpl
        roi = change["new"]
        img = self.img
        roidata = get_roidata(self.path_h5, self.scan_no, roi)
        dsetname = os.path.basename(self.path_h5)

        img.set_data(roidata)
        img.axes.set_title(f"{dsetname}\n#{self.scan_no} - {roi}")
        try:
            img.set_clim(roidata.min(), roidata.max())
        except ValueError:
            img.set_clim(0.1, roidata.max())

        self.roidata = roidata

    def _update_norm(self, change):  # mpl
        islog = change["new"]
        im = self.img
        roidata = im.get_array()

        _clims = [roidata.min(), roidata.max()]
        self.clims = _clims

        if islog:
            try:
                _ = im.set_norm(mpl.colors.LogNorm(*_clims))
            except ValueError as err:
                print("{}, setting lower bound to 0.1".format(err))
                _ = im.set_norm(mpl.colors.LogNorm(0.1, _clims[1]))
        else:
            _ = im.set_norm(mpl.colors.Normalize(*_clims))

    @retry()
    def _get_motor_names(self):
        command = self.command
        m1name, m2name = [command.split(" ")[x][:-1] for x in (1, 5)]

        self.m1name, self.m2name = m1name, m2name

    @retry()
    def _update_piezo_coordinates(self):  # mpl
        command = self.command
        with h5py.File(self.path_h5, "r") as h5f:
            sh = [h5f[self.scan_no][f"technique/{x}"][()] for x in ("dim0", "dim1")]
            m1n, m2n = self.m1name, self.m2name

            self.ax.set_xlabel(f"{m1n} (um)")
            self.ax.set_ylabel(f"{m2n} (um)")

            m1, m2 = [
                h5f[f"{self.scan_no}/instrument/positioners/{m}_position"][()]
                for m in (m1n, m2n)
            ]

            # surely this can be done in a more intelligent way
            if m1.size != sh[0] * sh[1]:
                m1m, m1M, m2m, m2M = [
                    float(command.split(" ")[x][:-1]) for x in (2, 3, 6, 7)
                ]
                self.img.set_extent([m1m, m1M, m2m, m2M])
            else:
                self.img.set_extent([m1.min(), m1.max(), m2.min(), m2.max()])

    @retry()
    def _update_specs(self):

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
            "      <td>{}</td>".format(get_command(self.path_h5, self.scan_no)),
            "    </tr>",
            "    <tr>",
            "      <th>Datetime</th>",
            "      <td>{}</td>".format(get_datetime(self.path_h5, self.scan_no)),
            "    </tr>",
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        specs = "\n".join(specs)
        self.specs.value = specs

        with h5py.File(self.path_h5, "r") as h5f:
            motors = list(h5f[f"/{self.scan_no}/instrument/positioners/"].keys())

        positions = {m: get_motorpos(self.path_h5, self.scan_no, m) for m in motors}
        motorspecs = [
            "<div>",
            '<table class="specs rendered_html output_html">',
            "  <tbody>",
        ]

        for mot, val in positions.items():
            if len(val.shape) == 0:
                _insert = [
                    "    <tr>",
                    "      <th>{}</th>".format(mot),
                    "      <td>{:.5f}</td>".format(val),
                    "    </tr>",
                ]
                _ = [motorspecs.append(x) for x in _insert]
            else:
                pass

        motorspecs += ["  </tbody>", "</table>", "</div>"]

        motorspecs = "\n".join(motorspecs)
        self.motorspecs.value = motorspecs

    @retry()
    def _update_scan(self, change):
        scan_idx = change["new"]
        self.scan_no = self._scan_nos[scan_idx]
        self.command = self._commands[self.scan_no]

        self._update_roi({"new": self.roisel.value})
        self._get_motor_names()
        self._update_piezo_coordinates()
        self._update_specs()

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
