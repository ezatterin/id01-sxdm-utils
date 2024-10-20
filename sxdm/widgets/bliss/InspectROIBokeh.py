# import h5py
# import ipywidgets as ipw
# import matplotlib.pyplot as plt
# import matplotlib as mpl
# import panel as pn
# import os
# import numpy as np

# from matplotlib.widgets import Cursor
# from IPython.display import display
# from silx.io.h5py_utils import retry
# from IPython import get_ipython

# from bokeh import models as bk_models
# from bokeh import plotting as bk_plotting

# from ...plot.utils import add_colorbar
# from ...io.bliss import get_roidata, get_positioner, get_command, get_datetime

# ipython = get_ipython()
# ipython.magic("matplotlib widget")


# css = """
# .bk.app_layout {
#     border-radius: 5px;
#     border: 1px black solid;
#     }
# """

# pn.extension("ipywidgets", raw_css=[css])


# class InspectROI(object):
#     def __init__(
#         self,
#         path_h5,
#         default_roi="mpx1x4_mpx4int",
#         roilist=None,
#         init_scan_no=None,
#         fixed_clims=None,
#         backend="mpl",
#         bk_opts=dict(width=300, height=300),
#     ):
#         """
#         Plot ROI data acquired during a BLISS experiment.

#         Parameters
#         ----------
#         path_h5 : str
#             Path to the .h5 file containing the dataset.
#         default_roi : str, default "mpx1x4_mpx4int"
#             Name of the ROI to be displayed by default.
#         roilist : list of str, optional
#             List of ROI names to display. Defaults to all of the available BLISS
#             counters.
#         init_scan_no : str, optional
#             First scan to display. Defaults to the lowest-index SXDM scan in the
#             dataset.
#         fixed_clims : list, optional
#             List of [lower, upper] intensity colour limits. Defaults to [max, min] of
#             the displayed data.
#         """

#         self.roiname = default_roi
#         self.path_h5 = path_h5
#         self.fixed_clims = fixed_clims
#         self.bk_opts = bk_opts
#         self.backend = backend

#         # get list of rois + other stuff
#         with h5py.File(path_h5, "r") as h5f:

#             scan_nos = list(h5f.keys())
#             commands = [h5f[f"{s}/title"][()].decode() for s in scan_nos]

#             scan_nos = [s for s, c in zip(scan_nos, commands) if "sxdm" in c]
#             scan_nos_int = sorted([int(s.split(".")[0]) for s in scan_nos])

#             self._scan_nos = [f"{s}.1" for s in scan_nos_int]
#             self._commands = {s: h5f[f"{s}/title"][()].decode() for s in self._scan_nos}
#             self.scan_no = self._scan_nos[0] if init_scan_no is None else init_scan_no

#             try:
#                 self.command = self._commands[self.scan_no]
#             except KeyError:
#                 raise KeyError(f"Scan {self.scan_no} is not an SXDM scan!")

#             counters = list(h5f[f"{self.scan_no}/measurement"].keys())
#             self.roilist = counters if roilist is None else roilist

#         # default roi data and motors
#         self.roidata = get_roidata(
#             path_h5, self.scan_no, self.roiname, return_pi_motors=False
#         )

#         # output widget to be filled with plt.figure

#         if backend == "mpl":
#             self.figout = ipw.Output(layout=dict(border="2px solid grey"))
#             self._init_fig()
#             self._update_norm({"new": False})
#         elif backend == "bokeh":
#             self._init_bk_data_source()
#             self._init_bk_figs()

#         self._init_widgets()
#         self._print_sharpness = False

#     def _init_bk_data_source(self):
#         self._get_piezo_coordinates()
#         m1, m2 = self._m1, self._m2
#         self.bk_roidatasource = bk_models.ColumnDataSource(
#             data=dict(
#                 image=[self.roidata],
#                 x=[m1.min()],
#                 y=[m2.min()],
#                 dw=[m1.max()],
#                 dh=[m2.max()],
#             )
#         )

#     def _init_bk_uroi_source(self):
#         pass

#     def _init_bk_figs(self):
#         bk_fig = bk_plotting.figure(tools="pan,reset", **self.bk_opts)
#         bk_img = bk_fig.image(
#             source=self.bk_roidatasource,
#             palette="Viridis256",
#         )

#         self.bk_fig = bk_fig
#         self.bk_img = bk_img
#         self.figout = pn.pane.Bokeh(
#             bk_fig, align=("end", "center"), sizing_mode="scale_both", margin=(5,5,5,5)
#         )

#     def _init_fig(self):  # mpl

#         with plt.ioff():
#             fig, ax = plt.subplots(1, 1, figsize=(4, 4), layout="tight")
#         with self.figout:
#             display(fig.canvas)

#         self.fig, self.ax = fig, ax
#         self.img = ax.imshow(self.roidata, origin="lower")
#         self._get_piezo_motor_names()
#         self._update_img_extent()

#         # labels etc
#         _ = add_colorbar(ax, self.img)
#         _ = ax.set_xlabel(f"{self.m1name} (um)")
#         _ = ax.set_ylabel(f"{self.m2name} (um)")
#         _ = ax.set_title(f"#{self.scan_no} - {self.roiname}")

#         # connect to mpl event manager
#         self.fig.canvas.mpl_connect("button_press_event", self._on_click)

#     def _init_widgets(self):

#         # layout of individual items - css properties
#         items_layout = ipw.Layout(width="auto")

#         # menu to select left ROI
#         self.roisel = ipw.Dropdown(
#             options=self.roilist,
#             value=self.roiname,
#             layout=items_layout,
#             description="ROI:",
#         )
#         self.roisel.observe(self._update_roi, names="value")

#         # slider to select scan index
#         idxsel = ipw.IntSlider(
#             value=self._scan_nos.index(self.scan_no),
#             min=0,
#             max=(len(self._scan_nos) - 1),
#             step=1,
#             layout=items_layout,
#             description="Scan index",
#         )
#         idxsel.observe(self._update_scan, names="value")

#         # log scale the images?
#         iflog = ipw.Checkbox(
#             value=False, description="Log Intensity", layout=items_layout, indent=False
#         )
#         iflog.observe(self._update_norm, names="value")

#         # show a crosshair at the mouse position?
#         ifmulti = ipw.Checkbox(
#             value=False, description="Crosshair", layout=items_layout, indent=False
#         )
#         ifmulti.observe(self._add_crosshair, names="value")

#         # group checkboxes
#         ifs = ipw.HBox(
#             [iflog, ifmulti],
#             layout={
#                 "width": "auto",
#                 "flex_flow": "row nowrap",
#                 "justify_content": "center",
#             },
#         )

#         # HTML table with motor specs
#         self.specs = ipw.HTML()
#         self.motorspecs = ipw.HTML()
#         self._update_specs()

#         view_motorspecs = ipw.Accordion([self.motorspecs])
#         view_motorspecs.set_title(0, "View motors")
#         view_motorspecs.selected_index = None
#         view_motorspecs.layout = {"font-family": "Liberation Sans"}

#         # TODO!
#         self.debug = ipw.Text(
#             value="All good", placeholder="Type something", description="Debug:"
#         )

#         # group all widgets together
#         self.selector = ipw.VBox(
#             [self.debug, self.roisel, idxsel, ifs, self.specs, view_motorspecs]
#         )
#         self.selector.layout = {
#             "border": "2px solid grey",
#             "width": "30%",
#             "padding": "2px",
#             "align-items": "stretch",
#         }

#     def _on_click(self, event):  # mpl
#         with self.figout:
#             if event.inaxes == self.ax:
#                 x, y = event.xdata, event.ydata
#                 m1n, m2n = self.m1name, self.m2name

#                 msg = f"You clicked: {m1n},{x:.4f}, {m2n},{y:.4f}"
#                 print(msg)
#             else:
#                 pass

#     def _add_crosshair(self, change):  # mpl
#         ismulti = change["new"]
#         if ismulti:
#             self.multi = Cursor(self.ax, color="r", lw=0.7, useblit=True)
#         else:
#             del self.multi

#     @retry()
#     def _update_roi(self, change):  # mpl, bk
#         roi = change["new"]

#         roidata = get_roidata(self.path_h5, self.scan_no, roi)
#         dsetname = os.path.basename(self.path_h5)

#         if self.backend == "mpl":
#             img = self.img
#             img.set_data(roidata)
#             img.axes.set_title(f"{dsetname}\n#{self.scan_no} - {roi}")
#             try:
#                 img.set_clim(roidata.min(), roidata.max())
#             except ValueError:
#                 img.set_clim(0.1, roidata.max())

#             self.roidata = roidata
#             self._update_norm({"new": False})

#         elif self.backend == "bokeh":
#             self.bk_roidatasource.data["image"] = [roidata]
#             pn.io.push_notebook(self.figout)

#     def _update_norm(self, change):  # mpl
#         islog = change["new"]
#         im = self.img
#         roidata = im.get_array()

#         if self.fixed_clims is None:
#             _clims = [roidata.min(), roidata.max()]
#         else:
#             _clims = self.fixed_clims
#         self.clims = _clims

#         if islog:
#             try:
#                 _ = im.set_norm(mpl.colors.LogNorm(*_clims))
#             except ValueError as err:
#                 print("{}, setting lower bound to 0.1".format(err))
#                 _ = im.set_norm(mpl.colors.LogNorm(0.1, _clims[1]))
#         else:
#             _ = im.set_norm(mpl.colors.Normalize(*_clims))

#     @retry()
#     def _get_piezo_motor_names(self):
#         m1name, m2name = [self.command.split(" ")[x][:-1] for x in (1, 5)]
#         self.m1name, self.m2name = m1name, m2name

#     def _get_piezo_coordinates(self):
#         self._get_piezo_motor_names()
#         with h5py.File(self.path_h5, "r") as h5f:
#             sh = [h5f[self.scan_no][f"technique/{x}"][()] for x in ("dim0", "dim1")]
#             m1n, m2n = self.m1name, self.m2name
#             m1, m2 = [
#                 h5f[f"{self.scan_no}/instrument/positioners/{m}_position"][()].reshape(
#                     sh
#                 )
#                 for m in (m1n, m2n)
#             ]

#             self.piezo_motorpos = {f"{m1n}": m1, f"{m2n}": m2}
#             self._m1 = m1
#             self._m2 = m2
#             self._map_shape = sh

#     @retry()
#     def _update_img_extent(self):  # mpl
#         self._get_piezo_coordinates()
#         sh = self._map_shape
#         m1, m2 = self._m1, self._m2

#         # surely this can be done in a more intelligent way
#         if m1.size != sh[0] * sh[1]:
#             m1m, m1M, m2m, m2M = [
#                 float(self.command.split(" ")[x][:-1]) for x in (2, 3, 6, 7)
#             ]
#             self.img.set_extent([m1m, m1M, m2m, m2M])
#         else:
#             self.img.set_extent([m1.min(), m1.max(), m2.min(), m2.max()])

#     @retry()
#     def _update_specs(self):

#         specs = [
#             "<div>",
#             "<style>",
#             "    .specs tbody {",
#             "        font-family: Liberation Sans, sans-serif ;",
#             "        font-size: small ;",
#             "        text-align: right ;",
#             "    }",
#             "</style>",
#             '<table class="specs rendered_html output_html">',
#             "  <tbody>",
#             "    <tr>",
#             "      <th>Command</th>",
#             "      <td>{}</td>".format(get_command(self.path_h5, self.scan_no)),
#             "    </tr>",
#             "    <tr>",
#             "      <th>Datetime</th>",
#             "      <td>{}</td>".format(get_datetime(self.path_h5, self.scan_no)),
#             "    </tr>",
#             "  </tbody>",
#             "</table>",
#             "</div>",
#         ]

#         specs = "\n".join(specs)
#         self.specs.value = specs

#         with h5py.File(self.path_h5, "r") as h5f:
#             motors = list(h5f[f"/{self.scan_no}/instrument/positioners/"].keys())

#         positions = {m: get_positioner(self.path_h5, self.scan_no, m) for m in motors}
#         motorspecs = [
#             "<div>",
#             '<table class="specs rendered_html output_html">',
#             "  <tbody>",
#         ]

#         for mot, val in positions.items():
#             if len(val.shape) == 0:
#                 _insert = [
#                     "    <tr>",
#                     "      <th>{}</th>".format(mot),
#                     "      <td>{:.5f}</td>".format(val),
#                     "    </tr>",
#                 ]
#                 _ = [motorspecs.append(x) for x in _insert]
#             else:
#                 pass

#         motorspecs += ["  </tbody>", "</table>", "</div>"]

#         motorspecs = "\n".join(motorspecs)
#         self.motorspecs.value = motorspecs

#     def _get_sharpness(self):
#         gy, gx = np.gradient(self.roidata)
#         gnorm = np.sqrt(gx**2 + gy**2)
#         self.sharpness = np.average(gnorm)

#         with self.figout:
#             print(f"Image sharpness: {self.sharpness}")

#     @retry()
#     def _update_scan(self, change):
#         scan_idx = change["new"]
#         self.scan_no = self._scan_nos[scan_idx]
#         self.command = self._commands[self.scan_no]

#         self._update_roi({"new": self.roisel.value})
#         self._get_piezo_motor_names()
#         self._update_specs()

#         if self.backend == "mpl":
#             self._update_norm({"new": False})
#             self._update_img_extent()

#         if self._print_sharpness is True:
#             self._get_sharpness()

#     def show(self):
#         """
#         Displays widget.
#         """

#         if self.backend == "mpl":
#             display(
#                 ipw.HBox(
#                     [self.selector, self.figout],
#                     layout={"justify-content": "space-between"},
#                 )
#             )
#         # TODO embedding does not work!
#         # https://panel.holoviz.org/reference/panes/IPyWidget.html#limitations
#         # rewrite widgets as panel widgets e ciao
#         elif self.backend == "bokeh":
#             self.selector.layout = {
#                 "border": "2px solid grey",
#                 "padding": "2px",
#                 "align-items": "stretch",
#                 "width": "auto",
#                 "display": "flex",
#                 "flex_flow": "column",
#             }
#             select = pn.Column(
#                 self.selector, align="start", width_policy="max", height_policy="max"
#             )
#             app = pn.panel(pn.Row(select, self.figout, css_classes=["app_layout"]))
#             display(app)
