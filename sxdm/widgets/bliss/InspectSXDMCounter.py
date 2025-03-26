import h5py
import ipywidgets as ipw
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import numpy as np

from matplotlib.widgets import Cursor
from silx.io.h5py_utils import retry
from warnings import warn

from IPython.display import display
from IPython.terminal.pt_inputhooks import UnknownBackend
from IPython import get_ipython

from id01lib.io.bliss import get_positioner
from ...plot.utils import add_colorbar
from ...io.utils import list_available_counters
from ...io.bliss import (
    get_roidata,
    get_command,
    get_datetime,
    get_piezo_motor_positions,
    get_scan_shape,
    get_detector_aliases,
    get_sxdm_scan_numbers,
)

ipython = get_ipython()
if ipython is not None:
    try:
        ipython.run_line_magic(magic_name="matplotlib", line="widget")
    except UnknownBackend:
        pass


# TODO:
# - offset_between_two_points
# - file select tab
# - fullscreen
class InspectSXDMCounter(object):
    def __init__(
        self,
        path_dset,
        default_counter=None,
        counter_list=None,
        init_scan_no=None,
        fixed_clims=None,
        show_scan_nos=None,
    ):
        """
        Plot ROI data acquired during a BLISS experiment. Call with .show().

        Parameters
        ----------
        path_dset : str
            Path to the .h5 file containing the dataset.
        default_counter : str, optional
            Name of the ROI to be displayed by default.
        counter_list : list of str, optional
            List of ROI names to display. Defaults to all of the available BLISS
            counters.
        init_scan_no : str or int, optional
            First scan to display. Defaults to the lowest-index SXDM scan in the
            dataset.
        fixed_clims : list, optional
            List of [lower, upper] intensity colour limits. Defaults to [max, min] of
            the displayed data.
        show_scan_nos : list, optional
            List of scan numbers to display.
        """

        # get list of SXDM or mesh scans contained in dataset file
        # if user gives list, check all are present
        scan_nos = get_sxdm_scan_numbers(path_dset, interrupted_scans=False)
        if show_scan_nos is not None:
            for s in show_scan_nos[:]:
                s = f"{s}.1" if isinstance(s, int) else s
                if s not in scan_nos:
                    show_scan_nos.remove(s)
                    msg = f"Removing {s} from the scan list as this is either not an "
                    msg += "SXDM or mesh scan, or it is not in the chosen dataset."
                    print(msg)
            scan_nos = show_scan_nos

        # get commands
        with h5py.File(path_dset, "r") as h5f:
            commands = {s: h5f[f"{s}/title"][()].decode() for s in scan_nos}

        # get first scan to show in widget
        s0 = f"{init_scan_no}.1" if isinstance(init_scan_no, int) else init_scan_no
        scan_no = scan_nos[0] if s0 is None else s0

        # get ROI to be displayed first
        default_det = get_detector_aliases(path_dset, scan_no)[0]
        det_counter_list = [
            x
            for x in list_available_counters(path_dset, scan_no)
            if f"{default_det}_" in x
        ]

        # set class variables
        self.roiname = (
            default_counter if default_counter is not None else det_counter_list[0]
        )
        self.path_dset = path_dset
        self.fixed_clims = fixed_clims
        self.counter_list = counter_list
        self.roidata = get_roidata(path_dset, scan_no, self.roiname)
        self.scan_no = scan_no
        self._scan_nos = scan_nos
        self._commands = commands
        self.command = commands[scan_no]
        self.dsetname = os.path.basename(self.path_dset)

        self.figout = ipw.Output(layout=dict(border="2px solid grey"))
        self._load_counters()
        self._init_fig()
        self._update_norm({"new": False})
        self._init_widgets()
        self._print_sharpness = False

    def _init_fig(self):  # mpl
        with plt.ioff():
            fig, ax = plt.subplots(1, 1, figsize=(4, 4), layout="tight")
        with self.figout:
            display(fig.canvas)

        self.fig, self.ax = fig, ax
        self.img = ax.imshow(self.roidata, origin="lower")
        self._get_piezo_motor_names()
        self._update_img_extent()

        # labels etc
        _ = add_colorbar(ax, self.img)
        _ = ax.set_xlabel(f"{self.m1name} (um)")
        _ = ax.set_ylabel(f"{self.m2name} (um)")
        _ = ax.set_title(f"{self.dsetname}\n#{self.scan_no} - {self.roiname}")

        # connect to mpl event manager
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    def _init_widgets(self):
        # layout of individual items - css properties
        items_layout = ipw.Layout(width="auto")

        # menu to select ROI
        self.roisel = ipw.Dropdown(
            options=self.counters,
            value=self.roiname,
            layout=items_layout,
            description="Counter:",
        )
        self.roisel.observe(self._update_roi, names="value")

        # slider to select scan index
        idxsel = ipw.IntSlider(
            value=self._scan_nos.index(self.scan_no),
            min=0,
            max=(len(self._scan_nos) - 1),
            step=1,
            layout=items_layout,
            description="Scan index",
        )
        idxsel.observe(self._update_scan, names="value")

        # log scale the images?
        self.iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout, indent=False
        )
        self.iflog.observe(self._update_norm, names="value")

        # show a crosshair at the mouse position?
        ifmulti = ipw.Checkbox(
            value=False, description="Crosshair", layout=items_layout, indent=False
        )
        ifmulti.observe(self._add_crosshair, names="value")

        # flip x axis?
        flipx = ipw.Checkbox(
            value=False, description="Flip x axis", layout=items_layout, indent=False
        )
        flipx.observe(self._flip_xaxis, names="value")

        # flip y axis?
        flipy = ipw.Checkbox(
            value=False, description="Flip y axis", layout=items_layout, indent=False
        )
        flipy.observe(self._flip_yaxis, names="value")

        # group checkboxes
        cblayout = {
            "width": "auto",
            "flex_flow": "row nowrap",
            "justify_content": "center",
        }
        ifs = ipw.VBox(
            [
                ipw.HBox([self.iflog, ifmulti], layout=cblayout),
                ipw.HBox([flipx, flipy], layout=cblayout),
            ]
        )

        # HTML table with motor specs
        self.specs = ipw.HTML()
        self.motorspecs = ipw.HTML()
        self._update_specs()

        view_motorspecs = ipw.Accordion([self.motorspecs])
        view_motorspecs.set_title(0, "View motors")
        view_motorspecs.selected_index = None

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

    def _load_counters(self):
        with h5py.File(self.path_dset, "r") as h5f:
            meas = h5f[f"{self.scan_no}/measurement"]

            clist = []
            for k, v in meas.items():
                try:
                    if len(v.shape) == 1:
                        clist.append(k)
                except AttributeError:
                    pass

        self.counters = clist if self.counter_list is None else self.counter_list

    def _on_click(self, event):  # mpl
        with self.figout:
            if event.inaxes == self.ax:
                x, y = event.xdata, event.ydata
                m1n, m2n = self.m1name, self.m2name

                msg = f"You clicked: {m1n},{x:.4f}, {m2n},{y:.4f}"
                print(msg)
            else:
                pass

    def _add_crosshair(self, change):  # mpl
        ismulti = change["new"]
        if ismulti:
            self.multi = Cursor(self.ax, color="r", lw=0.7, useblit=True)
        else:
            del self.multi

    def _flip_xaxis(self, change):  # mpl
        self.ax.invert_xaxis()

    def _flip_yaxis(self, change):  # mpl
        self.ax.invert_yaxis()

    @retry()
    def _update_roi(self, change):  # mpl
        roi = change["new"]

        roidata = get_roidata(self.path_dset, self.scan_no, roi)

        img = self.img
        img.set_data(roidata)
        img.axes.set_title(f"{self.dsetname}\n#{self.scan_no} - {roi}")
        try:
            img.set_clim(roidata.min(), roidata.max())
        except ValueError:
            img.set_clim(0.1, roidata.max())

        self.roidata = roidata
        self._update_norm({"new": self.iflog.value})

    def _update_norm(self, change):  # mpl
        islog = change["new"]
        im = self.img
        roidata = im.get_array()

        if self.fixed_clims is None:
            _clims = [roidata.min(), roidata.max()]
        else:
            _clims = self.fixed_clims
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
    def _get_piezo_motor_names(self):
        self.m1name, self.m2name = [self.command.split(" ")[x] for x in (1, 5)]

    def _get_piezo_coordinates(self):
        self._get_piezo_motor_names()
        m1n, m2n = self.m1name, self.m2name

        sh = get_scan_shape(self.path_dset, self.scan_no)
        try:
            m1, m2 = get_piezo_motor_positions(self.path_dset, self.scan_no)
        except ValueError:  # failed scan: cannot reshape m1, m2 to sh
            try:
                m1m, m2m, m1M, m2M = [
                    float(self.command.split(" ")[i][:-1]) for i in (2, 6, 3, 7)
                ]
            except ValueError:  # no comma
                m1m, m2m, m1M, m2M = [
                    float(self.command.split(" ")[i]) for i in (2, 6, 3, 7)
                ]
            m1, m2 = [
                np.linspace(m, M, s) for m, M, s in zip([m1m, m2m], [m1M, m2M], sh)
            ]
            m1, m2 = np.meshgrid(m1, m2)

        self.piezo_motorpos = {f"{m1n}": m1, f"{m2n}": m2}
        self._m1 = m1
        self._m2 = m2
        self._map_shape = sh

    @retry()
    def _update_img_extent(self):  # mpl
        self._get_piezo_coordinates()
        sh = self._map_shape
        m1, m2 = self._m1, self._m2

        # surely this can be done in a more intelligent way
        if m1.size != sh[0] * sh[1]:
            m1m, m1M, m2m, m2M = [
                float(self.command.split(" ")[x][:-1]) for x in (2, 3, 6, 7)
            ]
            self.img.set_extent([m1m, m1M, m2m, m2M])
        else:
            self.img.set_extent([m1.min(), m1.max(), m2.min(), m2.max()])

        _ = self.ax.set_xlabel(f"{self.m1name} (um)")
        _ = self.ax.set_ylabel(f"{self.m2name} (um)")

    @retry()
    def _update_specs(self):
        specs = [
            "<div>",
            "<style>",
            "    .specs tbody {",
            "        font-size: small ;",
            "        text-align: right ;",
            "    }",
            "</style>",
            '<table class="specs rendered_html output_html">',
            "  <tbody>",
            "    <tr>",
            "      <th>Command</th>",
            "      <td>{}</td>".format(get_command(self.path_dset, self.scan_no)),
            "    </tr>",
            "    <tr>",
            "      <th>Datetime</th>",
            "      <td>{}</td>".format(get_datetime(self.path_dset, self.scan_no)),
            "    </tr>",
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        specs = "\n".join(specs)
        self.specs.value = specs

        with h5py.File(self.path_dset, "r") as h5f:
            motors = list(h5f[f"/{self.scan_no}/instrument/positioners/"].keys())

        positions = {m: get_positioner(self.path_dset, self.scan_no, m) for m in motors}
        motorspecs = [
            "<div>",
            '<table class="specs rendered_html output_html">',
            "  <tbody>",
        ]

        for mot, val in positions.items():
            try:
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
            except AttributeError:
                pass

        motorspecs += ["  </tbody>", "</table>", "</div>"]

        motorspecs = "\n".join(motorspecs)
        self.motorspecs.value = motorspecs

    def _get_sharpness(self):
        gy, gx = np.gradient(self.roidata)
        gnorm = np.sqrt(gx**2 + gy**2)
        self.sharpness = np.average(gnorm)

        with self.figout:
            print(f"Image sharpness: {self.sharpness}")

    @retry()
    def _update_scan(self, change):
        scan_idx = change["new"]
        self.scan_no = self._scan_nos[scan_idx]
        self.command = self._commands[self.scan_no]

        self._load_counters()

        _selected = self.roisel.value
        self.roisel.options = self.counters
        self.roisel.value = _selected

        self._update_roi({"new": self.roisel.value})

        self._get_piezo_motor_names()
        self._update_specs()

        self._update_norm({"new": self.iflog.value})
        self._update_img_extent()

        if self._print_sharpness is True:
            self._get_sharpness()

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


def InspectROI(*args, **kwargs):
    msg = "InspectROI is deprecated and will be removed in future releases. "
    msg += "Use InspectSXDMCounter instead."
    warn(msg, DeprecationWarning, stacklevel=2)

    return InspectSXDMCounter(*args, **kwargs)
