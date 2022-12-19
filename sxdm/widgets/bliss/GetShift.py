import ipywidgets as ipw
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import numpy as np
import scipy.ndimage as ndi

from IPython.display import display
from IPython.terminal.pt_inputhooks import UnknownBackend
from IPython import get_ipython

from sxdm.io.utils import list_available_counters
from sxdm.plot.utils import add_colorbar
from sxdm.io.bliss import (
    get_roidata,
    get_piezo_motor_names,
)

ipython = get_ipython()
if ipython is not None:
    try:
        ipython.magic("matplotlib widget")
    except UnknownBackend:
        pass


class GetShift(object):
    def __init__(
        self,
        path_h5,
        scan_nos,
        counter_name="mpx1x4_mpx4int",
        fixed_clims=None,
    ):
        """
        Estimate shift between images of counters acquired during an SXDM experiment.

        Parameters
        ----------
        path_h5 : str
            Path to the .h5 file containing the dataset.
        scan_nos : list of str
            List of scan numbers to be treated, of the form ['1.1', '2.1', '3.1'].
        counter_name : str, default "mpx1x4_mpx4int"
            Name of the counter to be displayed by default.
        fixed_clims : list, optional
            List of [lower, upper] intensity colour limits. Defaults to [max, min] of
            the displayed data.
        """

        self.path_h5 = path_h5
        self.scan_nos = scan_nos
        self.counter_name = counter_name
        self.fixed_clims = fixed_clims
        self.dsetname = os.path.basename(path_h5)
        self.figout = ipw.Output(layout=dict(border="2px solid grey"))

        self.data = get_roidata(
            path_h5, self.scan_nos[0], counter_name, return_pi_motors=False
        )

        self.shifts = np.zeros((len(self.scan_nos), 2))
        self.scan_idx = 0
        self.scan_no = self.scan_nos[self.scan_idx]

        self.marks = {s: None for s in self.scan_nos}

        self._load_counters_list()
        self._init_fig()
        self._update_norm({"new": False})
        self._init_widgets()
        self._update_counter({"new": counter_name})
        self._calc_shifts()

    def _load_counters_list(self):
        self.counters = list_available_counters(self.path_h5, self.scan_no)

    def _load_piezo_motor_names(self):
        self.m1name, self.m2name = get_piezo_motor_names(self.path_h5, self.scan_no)

    def _init_fig(self):

        with plt.ioff():
            fig, ax = plt.subplots(1, 1, figsize=(4, 4), layout="tight")
        with self.figout:
            display(fig.canvas)
        self.fig, self.ax = fig, ax

        # image
        self.img = ax.imshow(self.data, origin="lower")
        self._load_piezo_motor_names()

        # init scatter
        dim0, dim1 = self.data.shape
        self.refmark = ax.scatter(dim1 // 2, dim0 // 2, marker="x", color="red")
        self.marks[self.scan_no] = [dim1 // 2, dim0 // 2]

        # labels etc
        _ = add_colorbar(ax, self.img)
        _ = ax.set_xlabel(f"{self.m1name} (pixels)")
        _ = ax.set_ylabel(f"{self.m2name} (pixels)")
        _ = ax.set_title(f"{self.dsetname}\n#{self.scan_no} - {self.counter_name}")

        # connect to mpl event manager
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    def _init_widgets(self):

        # layout of individual items - css properties
        items_layout = ipw.Layout(width="auto")

        # menu to select left ROI
        self.roisel = ipw.Dropdown(
            options=self.counters,
            value=self.counter_name,
            layout=items_layout,
            description="Counter:",
        )
        self.roisel.observe(self._update_counter, names="value")

        # slider to select scan index
        self.idxsel = ipw.IntSlider(
            value=self.scan_nos.index(self.scan_no),
            min=0,
            max=(len(self.scan_nos) - 1),
            step=1,
            layout=items_layout,
            description="Scan index",
        )
        self.idxsel.observe(self._update_scan, names="value")

        # log scale the images?
        self.iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout, indent=False
        )
        self.iflog.observe(self._update_norm, names="value")

        # shift counter?
        self.shiftit = ipw.ToggleButton(
            value=False,
            description="Apply shift to selected counter",
            tooltip="Apply shift to selected counter",
            layout={"width": "100%"},
        )
        self.shiftit.observe(self._apply_shift_counter)

        # incr or decr scan idx
        self.fwd = ipw.Button(description=">>")
        self.fwd.on_click(self._scan_idx_fwd)

        self.bkw = ipw.Button(description="<<")
        self.bkw.on_click(self._scan_idx_bkw)

        # shifts
        self.shifts_widget = ipw.HTML()
        view_shifts = ipw.Accordion([self.shifts_widget])
        view_shifts.set_title(0, "View shifts")
        view_shifts.selected_index = None
        view_shifts.layout = {"font-family": "Liberation Sans"}

        # group checkboxes
        cblayout = {
            "width": "auto",
            "flex_flow": "row nowrap",
            "justify_content": "center",
        }
        ifs = ipw.VBox(
            [
                ipw.HBox([self.iflog], layout=cblayout),
                ipw.HBox([self.bkw, self.fwd], layout=cblayout),
                ipw.HBox([self.shiftit], layout=cblayout),
                view_shifts,
            ]
        )

        # group all widgets together
        self.selector = ipw.VBox([self.roisel, self.idxsel, ifs])
        self.selector.layout = {
            "border": "2px solid grey",
            "width": "30%",
            "padding": "2px",
            "align-items": "stretch",
        }

    def _scan_idx_fwd(self, widget):
        try:
            self.scan_idx += 1
            self._update_scan({"new": self.scan_idx})
        except IndexError:
            self.scan_idx -= 1
        self.idxsel.value = self.scan_idx

    def _scan_idx_bkw(self, widget):

        if self.scan_idx > 0:
            self.scan_idx -= 1
            self._update_scan({"new": self.scan_idx})
        elif self.scan_idx < 0:
            self.scan_idx += 1
        self.idxsel.value = self.scan_idx

    def _update_norm(self, change):
        # when scan idx changed with slider (_update_scan)

        islog = change["new"]

        im = self.img
        data = im.get_array()

        if self.fixed_clims is None:
            _clims = [data[data.nonzero()].min(), data.max()]
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
        """
        Displays widget.
        """

        display(
            ipw.HBox(
                [self.selector, self.figout],
                layout={"justify-content": "space-between"},
            )
        )

    def _on_click(self, event):
        with self.figout:
            if event.inaxes == self.ax:
                x, y = event.xdata, event.ydata
                m1n, m2n = self.m1name, self.m2name

                msg = f"You clicked: {m1n},{x:.4f}, {m2n},{y:.4f}"
                print(f"\r {msg}", flush=True, end="")

                if self.fig.canvas.toolbar.mode == "":
                    self.refmark.set_offsets([x, y])
                    self.marks[self.scan_no] = [x, y]
                else:
                    pass

            else:
                pass

    def _update_counter(self, change):
        # when counter changed in drop-down menu

        if not self.shiftit.value:
            self.counter_name = change["new"]
            data = get_roidata(self.path_h5, self.scan_no, self.counter_name)
        else:
            data = self.dmaps_shifted[self.scan_no]

        img = self.img
        img.set_data(data)
        img.axes.set_title(f"{self.dsetname}\n#{self.scan_no} - {self.counter_name}")
        try:
            img.set_clim(data.min(), data.max())
        except ValueError:
            img.set_clim(0.1, data.max())

        self.data = data
        self._update_norm({"new": False})

    def _update_mark(self):
        # when scan idx changed with slider (_update_scan)

        if self.marks[self.scan_no] is None:
            off = self.marks[self.scan_nos[self.scan_idx - 1]]

            if off is None:  # because you skip scans with slider
                off = self.marks[self.scan_nos[0]]
            if self.shiftit.value:
                off += self.shifts[self.scan_nos.index(self.scan_no)][::-1]

            self.refmark.set_offsets(off)
            self.marks[self.scan_no] = off
        else:
            off = self.marks[self.scan_no]
            if self.shiftit.value:
                off += self.shifts[self.scan_nos.index(self.scan_no)][::-1]
            self.refmark.set_offsets(off)

    def _update_scan(self, change):
        # when scan idx changed with slider

        self.scan_idx = change["new"]
        self.scan_no = self.scan_nos[self.scan_idx]

        self._update_counter({"new": self.roisel.value})
        self._load_piezo_motor_names()
        self._update_norm({"new": self.iflog.value})
        self._update_mark()
        self._calc_shifts()

    def _apply_shift_counter(self, change):

        if self.shiftit.value:
            self._calc_shifts()
            self.dmaps = [
                get_roidata(self.path_h5, s, self.counter_name) for s in self.scan_nos
            ]
            self.dmaps_shifted = {
                n: ndi.shift(x, s, order=0)
                for n, x, s in zip(self.scan_nos, self.dmaps, self.shifts)
            }
            self.idxsel.value = 0
            self.roisel.disabled = True
        else:
            self.idxsel.value = 0
            self.roisel.disabled = False

    def _calc_shifts(self):
        pos = [
            self.marks[x] if self.marks[x] is not None else self.marks[self.scan_nos[0]]
            for x in self.scan_nos
        ]
        shifts = np.array(pos) - np.array(pos[0])

        self.shifts = np.fliplr(-shifts)
        self._update_shifts_tab()

    def _update_shifts_tab(self):
        shifts_tab = [
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
            "      <th>rows</th>",
            "      <th>cols</th>",
            "    </tr>",
            *[
                f"     <tr><td>{x:.3f}</td><td>{y:.3f}</td></tr>"
                for x, y in self.shifts
            ],
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        self.shifts_widget.value = "\n".join(shifts_tab)


class GetShiftCustom(object):
    def __init__(
        self,
        img_list,
        fixed_clims=None,
        init_shifts=None,
    ):
        """
        Estimate shift between images of counters acquired during an SXDM experiment.

        Parameters
        ----------
        img_list : list of 2D np.ndarray
            List of images to be shifted.
            List of scan numbers to be treated, of the form ['1.1', '2.1', '3.1'].
            Name of the counter to be displayed by default.
        fixed_clims : list, optional
            List of [lower, upper] intensity colour limits. Defaults to [max, min] of
            the displayed data.
        """

        self.fixed_clims = fixed_clims if fixed_clims is not None else False
        self.img_list = img_list
        self.figout = ipw.Output(layout=dict(border="2px solid grey"))

        self.data = img_list[0]
        self.img_idx = 0
        self.init = True

        self.shifts = (
            np.zeros((len(img_list), 2)) if init_shifts is None else init_shifts
        )
        self.marks = {key: None for key in range(len(img_list))}

        self._init_fig()
        self._update_norm({"new": False})
        self._init_widgets()
        self._calc_shifts()

    def _init_fig(self):

        with plt.ioff():
            fig, ax = plt.subplots(1, 1, figsize=(4, 4), layout="tight")
        with self.figout:
            display(fig.canvas)
        self.fig, self.ax = fig, ax

        # image
        self.img = ax.imshow(self.data, origin="lower")

        # init scatter
        dim0, dim1 = self.data.shape
        self.refmark = ax.scatter(dim1 // 2, dim0 // 2, marker="x", color="red")
        self.marks[self.img_idx] = [dim1 // 2, dim0 // 2]

        # labels etc
        _ = add_colorbar(ax, self.img)
        _ = ax.set_title(f"#{self.img_idx}")

        # connect to mpl event manager
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    def _init_widgets(self):

        # layout of individual items - css properties
        items_layout = ipw.Layout(width="auto")

        # slider to select scan index
        self.idxsel = ipw.IntSlider(
            value=self.img_idx,
            min=0,
            max=(len(self.img_list) - 1),
            step=1,
            layout=items_layout,
            description="Scan index",
        )
        self.idxsel.observe(self._update_scan, names="value")

        # log scale the images?
        self.iflog = ipw.Checkbox(
            value=False, description="Log Intensity", layout=items_layout, indent=False
        )
        self.iflog.observe(self._update_norm, names="value")

        # shift?
        self.shiftit = ipw.ToggleButton(
            value=False,
            description="Apply shift to images",
            tooltip="Apply shift to images",
            layout={"width": "100%"},
        )
        self.shiftit.observe(self._apply_shift_counter)

        # incr or decr scan idx
        self._fwd = ipw.Button(description=">>")
        self._fwd.on_click(self._img_idx_fwd)

        self._bkw = ipw.Button(description="<<")
        self._bkw.on_click(self._img_idx_bkw)

        # shifts
        self.shifts_widget = ipw.HTML()
        view_shifts = ipw.Accordion([self.shifts_widget])
        view_shifts.set_title(0, "View shifts")
        view_shifts.selected_index = None
        view_shifts.layout = {"font-family": "Liberation Sans"}

        # group checkboxes
        cblayout = {
            "width": "auto",
            "flex_flow": "row nowrap",
            "justify_content": "center",
        }
        ifs = ipw.VBox(
            [
                ipw.HBox([self.iflog], layout=cblayout),
                ipw.HBox([self._bkw, self._fwd], layout=cblayout),
                ipw.HBox([self.shiftit], layout=cblayout),
                view_shifts,
            ]
        )

        # group all widgets together
        self.selector = ipw.VBox([self.idxsel, ifs])
        self.selector.layout = {
            "border": "2px solid grey",
            "width": "30%",
            "padding": "2px",
            "align-items": "stretch",
        }

    def _img_idx_fwd(self, widget):
        try:
            self.img_idx += 1
            self._update_scan({"new": self.img_idx})
        except (IndexError, KeyError):
            self.img_idx -= 1
        self.idxsel.value = self.img_idx

    def _img_idx_bkw(self, widget):

        if self.img_idx > 0:
            self.img_idx -= 1
            self._update_scan({"new": self.img_idx})
        elif self.img_idx < 0:
            self.img_idx += 1
        self.idxsel.value = self.img_idx

    def _update_norm(self, change):
        # when scan idx changed with slider (_update_scan)

        islog = change["new"]

        im = self.img
        data = im.get_array()

        if not self.fixed_clims:
            _clims = [data[data.nonzero()].min(), data.max()]
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
        """
        Displays widget.
        """

        display(
            ipw.HBox(
                [self.selector, self.figout],
                layout={"justify-content": "space-between"},
            )
        )

    def _on_click(self, event):
        with self.figout:
            if event.inaxes == self.ax:
                x, y = event.xdata, event.ydata

                msg = f"You clicked: col={x:.4f}, row={y:.4f}"
                print(f"\r {msg}", flush=True, end="")

                if self.fig.canvas.toolbar.mode == "":
                    self.refmark.set_offsets([x, y])
                    self.marks[self.img_idx] = [x, y]
                else:
                    pass

            else:
                pass

    def _update_mark(self):
        # when scan idx changed with slider (_update_scan)

        if self.marks[self.img_idx] is None:
            off = self.marks[self.img_idx - 1]

            if off is None:  # because you skip scans with slider
                off = self.marks[0]
            if self.shiftit.value:
                off += self.shifts[self.img_idx][::-1]

            self.refmark.set_offsets(off)
            self.marks[self.img_idx] = off
        else:
            off = self.marks[self.img_idx]
            if self.shiftit.value:
                off += self.shifts[self.img_idx][::-1]
            self.refmark.set_offsets(off)

    def _update_scan(self, change):
        # when scan idx changed with slider

        self.img_idx = change["new"]
        if self.shiftit.value:
            self.img.set_data(self.img_list_shifted[self.img_idx])
        else:
            self.img.set_data(self.img_list[self.img_idx])
        self.ax.set_title(f"#{self.img_idx}")

        self._update_norm({"new": self.iflog.value})
        self._update_mark()
        self._calc_shifts()

    def _apply_shift_counter(self, change):

        if self.shiftit.value:
            self._calc_shifts()
            self.img_list_shifted = {
                n: ndi.shift(x, s, order=0)
                for n, x, s in zip(
                    range(len(self.img_list)), self.img_list, self.shifts
                )
            }
            self.idxsel.value = 0
        else:
            self.idxsel.value = 0

    def _calc_shifts(self):

        if self.shifts.any() is True and self.init is True:
            for x in range(1, len(self.img_list)):
                self.marks[x] = list(np.array(self.marks[0]) - self.shifts[x][::-1])
            self.init = False
        else:
            pos = [
                self.marks[x] if self.marks[x] is not None else self.marks[0]
                for x in range(len(self.img_list))
            ]
            shifts = np.array(pos) - np.array(pos[0])
            self.shifts = np.fliplr(-shifts)
        self._update_shifts_tab()

    def _update_shifts_tab(self):
        shifts_tab = [
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
            "      <th>rows</th>",
            "      <th>cols</th>",
            "    </tr>",
            *[
                f"     <tr><td>{x:.3f}</td><td>{y:.3f}</td></tr>"
                for x, y in self.shifts
            ],
            "  </tbody>",
            "</table>",
            "</div>",
        ]

        self.shifts_widget.value = "\n".join(shifts_tab)
