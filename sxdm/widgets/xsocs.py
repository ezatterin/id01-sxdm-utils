import h5py
import ipywidgets as ipw
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from IPython.display import display

from ..plot import add_colorbar
from ..utils import get_qspace_coords, get_q_extents

class Inspect5DQspace(object):
    def __init__(
        self,
        maps_dict,
        path_qspace,
        init_idx=[10, 10],
        qspace_roi=np.s_[:, :, :],
        relim_int=False,
    ):
        """
        maps_dict must contain items of shape equivalent to that of the sxdm scan.
        """

        init_map_name = list(maps_dict.keys())[0]

        self._figout = ipw.Output()
        self._init_darr = maps_dict[init_map_name]
        self.row, self.col = init_idx
        self._h5f = path_qspace
        self.maps_dict = maps_dict
        self.qx, self.qy, self.qz = get_qspace_coords(path_qspace)
        self.roi = qspace_roi
        self.relim_int = relim_int

        with self._figout:
            self.fig, self.ax = plt.subplots(
                2, 2, figsize=(4.5, 4), dpi=160, layout="tight"
            )

        self._init_fig()
        self.fig.canvas.mpl_connect("button_press_event", self._onclick)
        self.fig.canvas.mpl_connect("key_press_event", self._onkey)

        self._select_plot = ipw.Select(options=maps_dict.keys(), value=init_map_name)
        self._select_plot.observe(self._change_plot, names="value")
        self._select_plot.layout = ipw.Layout(width="30%")

        self._iflog = ipw.Checkbox(value=False, description="Log Intensity")
        self._iflog.observe(self._update_norm, names="value")

    def _update_norm(self, change):
        islog = change["new"]

        for a in self.ax.flatten()[1:]:
            im = a.get_images()[0]
            arr = im.get_array()
            clim = arr[arr.nonzero()].min(), arr[arr.nonzero()].max()

            if not islog:
                im.set_norm(mpl.colors.Normalize(*clim))
                word = ""
                print(f"\r{word: >50}", end="", flush=True)
            else:
                try:
                    im.set_norm(mpl.colors.LogNorm(*clim))
                except ValueError as err:
                    im.set_norm(mpl.colors.LogNorm(0.1, clim[1]))
                    print(
                        f"\r{err}, setting lower bound to 0.1",
                        end="",
                        flush=True,
                    )

    def _get_rsm(self):
        row, col = self.row, self.col

        with h5py.File(self._h5f, "r") as h5f:
            idx = row * self._init_darr.shape[1] + col
            if np.ma.isMaskedArray(self._init_darr):
                idx_allowed = np.where(~self._init_darr.mask.ravel())[0]
            else:
                idx_allowed = np.arange(self._init_darr.size)

            rsm = h5f["/Data/qspace"][idx][self.roi]
            if idx not in idx_allowed:
                rsm = np.ones_like(rsm)
        self.selected_idx = idx
        with self._figout:
            print(f"\r{(row, col)} --> {idx}", end="", flush=True)

        return rsm

    def _init_fig(self):
        a0 = self.ax[0, 0]
        self._dmap = a0.imshow(self._init_darr, origin="lower")
        self._curpos = a0.scatter(self.row, self.col, marker="x", c="w")

        rsm = self._get_rsm()
        qext = get_q_extents(
            self.qx[self.roi[0]], self.qy[self.roi[1]], self.qz[self.roi[2]]
        )
        for i, a in enumerate(self.ax.flatten()[1:]):
            a.imshow(rsm.sum(i).T, extent=qext[i], origin="lower")

        for a in self.ax.flatten():
            _ = add_colorbar(a, a.get_images()[0])

        self.ax[0, 0].set_xlabel("motor0 (pixels)")
        self.ax[0, 0].set_ylabel("motor1 (pixels)")

        self.ax.ravel()[1].set_xlabel(r"$Q_y~(\AA^{-1})$")
        self.ax.ravel()[3].set_ylabel(r"$Q_y~(\AA^{-1})$")

        _ = [self.ax.ravel()[i].set_xlabel(r"$Q_x~(\AA^{-1})$") for i in (2, 3)]
        _ = [self.ax.ravel()[i].set_ylabel(r"$Q_z~(\AA^{-1})$") for i in (1, 2)]

    def _change_plot(self, change):
        darr = self.maps_dict[change["new"]]

        self._dmap.set_array(darr)
        self._dmap.set_clim([darr.min(), darr.max()])

    def _onclick(self, event):
        if event.inaxes == self.ax[0, 0]:
            self.col, self.row = [
                int(np.round(x, 0)) for x in (event.xdata, event.ydata)
            ]
            self._update()
        else:
            pass

    def _onkey(self, event):
        if event.key in ["39", "right"]:
            self.col += 1
            self._update()
        elif event.key in ["37", "left"]:
            self.col -= 1
            self._update()
        elif event.key in ["40", "down"]:
            self.row -= 1
            self._update()
        elif event.key in ["38", "up"]:
            self.row += 1
            self._update()

    def _update(self):
        self._curpos.set_offsets([self.col, self.row])

        rsm = self._get_rsm()
        for i, a in enumerate(self.ax.flatten()[1:]):
            topl = rsm.sum(i).T
            proj = a.get_images()[0]
            proj.set_array(topl)

            if self.relim_int is True:
                self._update_norm({"new": self._iflog.value})

    def show(self):
        selector = ipw.HBox([self._select_plot, self._iflog])
        gui = ipw.VBox([selector, self._figout])
        display(gui)