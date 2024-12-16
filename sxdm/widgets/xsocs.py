import h5py
import ipywidgets as ipw
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from IPython.display import display

from ..plot.utils import add_colorbar
from ..utils import get_qspace_coords, get_q_extents
from ..utils.bliss import get_qspace_proj

from silx.math import fit
from xsocs.util import gaussian


class Inspect5DQspace(object):
    rec_ax_idx = {0: "qx", 1: "qy", 2: "qz"}

    def __init__(
        self,
        maps_dict,
        path_qspace,
        projections="2d",
        init_idx=[10, 10],
        qspace_roi=np.s_[:, :, :],
        relim_int=True,
        coms=None,
        gauss_fits=None,
        xsocs_gauss=False,
    ):
        """
        Inspect intensity(x, y, q_x, q_y, q_z) data output by XSOCS.

        Parameters
        ----------
        maps_dict : dict
            Items here have the same shape as that of the SXDM scan.
        path_qspace : str
            Path to the qspace hdf5 file output by XSOCS.
        projections : str
            TODO
        init_idx : list of int, default [10,10]
            Indexes of the first (x,y) coordinate to load.
        qspace_roi : tuple of slice, default np.s_[:,:,:]
            Slices of the 3D q-space array representing a q-space ROI. Use the numpy
            shorthand syntax: np.s_[].
        relim_int : bool, default True
            If True, re-compute intensity color limits at each new (x,y) position.
        coms : list of numpy.ndarray, optional
            List of x,y,z COM coordinates, each of the same shape as the SXDM map.
        gauss_fits : dict
            TODO
        xsocs_gauss : bool
            TODO
        """

        self.init_map_name = list(maps_dict.keys())[0]

        self._figout = ipw.Output(layout=dict(border="1px solid grey"))
        self._init_darr = maps_dict[self.init_map_name]
        self.row, self.col = init_idx
        self._h5f = path_qspace
        self._proj = projections
        self.maps_dict = maps_dict
        self.qx, self.qy, self.qz = get_qspace_coords(path_qspace)
        self.roi = qspace_roi
        self.relim_int = relim_int
        self.coms = coms
        self.gauss_fits = gauss_fits
        self.xsocs_gauss = xsocs_gauss

        self._init_fig()
        self._init_widgets()

    def _init_widgets(self):
        self._select_plot = ipw.Select(
            options=self.maps_dict.keys(), value=self.init_map_name
        )
        self._select_plot.observe(self._change_plot, names="value")
        self._select_plot.layout = ipw.Layout(width="30%")

        self._iflog = ipw.Checkbox(value=False, description="Log Intensity")
        self._iflog.observe(self._update_norm, names="value")

    def _update_norm(self, change):
        islog = change["new"]

        if self._proj == "2d":
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
        elif self._proj == "1d":
            for a in self.ax.flatten()[1:]:
                if islog:
                    a.set_yscale("log")
                else:
                    a.set_yscale("linear")

    def _get_rsm(self):
        row, col = self.row, self.col

        with h5py.File(self._h5f, "r") as h5f:
            idx = row * self._init_darr.shape[1] + col
            if np.ma.is_masked(self._init_darr):
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
        with plt.ioff():
            self.fig, self.ax = plt.subplots(2, 2, figsize=(6, 5))
        with self._figout:
            display(self.fig.canvas)

        a0 = self.ax[0, 0]
        self._dmap = a0.imshow(self._init_darr, origin="lower")
        self._curpos = a0.scatter(self.row, self.col, marker="x", c="w")

        self.ax[0, 0].set_xlabel("motor0 (pixels)")
        self.ax[0, 0].set_ylabel("motor1 (pixels)")

        self.qcoords = self.qx[self.roi[0]], self.qy[self.roi[1]], self.qz[self.roi[2]]
        qext = get_q_extents(*self.qcoords)

        if self._proj == "2d":
            rsm = self._get_rsm()
            for i, a in enumerate(self.ax.flatten()[1:]):
                a.imshow(rsm.sum(i).T, extent=qext[i], origin="lower", cmap="magma")

            if self.coms is not None:
                cx, cy, cz = self.coms
                self.coms_scatt = []
                for a, (c0, c1) in zip(
                    self.ax.flatten()[1:], [(cy, cz), (cx, cz), (cx, cy)]
                ):
                    c0_local, c1_local = [c[self.row, self.col] for c in (c0, c1)]
                    scatt = a.scatter(c0_local, c1_local, color="b", marker="x")
                    self.coms_scatt.append(scatt)

            for a in self.ax.flatten():
                _ = add_colorbar(a, a.get_images()[0])

            self.ax.ravel()[1].set_xlabel(r"$q_y~(\AA^{-1})$")
            self.ax.ravel()[3].set_ylabel(r"$q_y~(\AA^{-1})$")

            _ = [self.ax.ravel()[i].set_xlabel(r"$q_x~(\AA^{-1})$") for i in (2, 3)]
            _ = [self.ax.ravel()[i].set_ylabel(r"$q_z~(\AA^{-1})$") for i in (1, 2)]

        elif self._proj == "1d":
            idx = self.row * self._init_darr.shape[1] + self.col
            self.projs, self.fits = [], []
            ax = self.ax.ravel()

            self.qgauss = [
                np.linspace(self.qcoords[i].min(), self.qcoords[i].max(), 1000)
                for i in range(3)
            ]

            for i in range(3):
                proj = get_qspace_proj(
                    self._h5f,
                    idx,
                    self.rec_ax_idx[i],
                    self.roi,
                    bin_norm=self.xsocs_gauss,
                )
                (line_exp,) = ax[i + 1].plot(self.qcoords[i], proj, marker="o", mfc="w")
                self.projs.append(line_exp)

                if self.gauss_fits is not None:
                    gfun = fit.sum_agauss if not self.xsocs_gauss else gaussian
                    gauss = gfun(
                        self.qgauss[i], *self.gauss_fits[self.rec_ax_idx[i]][idx]
                    )
                    (line_fit,) = ax[i + 1].plot(self.qgauss[i], gauss, c="r")
                    self.fits.append(line_fit)

                ax[i + 1].set_autoscaley_on(True)
                ax[i + 1].set_xlabel(rf"$q_{self.rec_ax_idx[i][-1]}~(\AA^{{-1}})$")

        else:
            raise KeyError("not 1d or 2d")

        self.fig.canvas.mpl_connect("button_press_event", self._onclick)
        self.fig.canvas.mpl_connect("key_press_event", self._onkey)

    def _change_plot(self, change):
        darr = self.maps_dict[self._select_plot.value]

        self._dmap.set_array(darr)

        # if not called twice sometimes it gets it wrong, not sure why
        self._dmap.set_clim([np.nanmin(darr), np.nanmax(darr)])
        self._dmap.set_clim([np.nanmin(darr), np.nanmax(darr)])

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
        row, col = self.row, self.col
        self._curpos.set_offsets([col, row])

        if self._proj == "2d":
            self.rsm = self._get_rsm()
            for i, a in enumerate(self.ax.flatten()[1:]):
                topl = self.rsm.sum(i).T
                proj = a.get_images()[0]
                proj.set_array(topl)

                if self.relim_int is True:
                    self._update_norm({"new": self._iflog.value})

                if self.coms is not None:
                    cx, cy, cz = self.coms
                    for scatt, (c0, c1) in zip(
                        self.coms_scatt, [(cy, cz), (cx, cz), (cx, cy)]
                    ):
                        c0_local, c1_local = [c[row, col] for c in (c0, c1)]
                        scatt.set_offsets([c0_local, c1_local])

        elif self._proj == "1d":
            idx = row * self._init_darr.shape[1] + col
            ax = self.ax.ravel()

            for i in range(3):
                proj = get_qspace_proj(
                    self._h5f,
                    idx,
                    self.rec_ax_idx[i],
                    self.roi,
                    bin_norm=self.xsocs_gauss,
                )
                self.projs[i].set_ydata(proj)

                if self.gauss_fits is not None:
                    gfun = fit.sum_agauss if not self.xsocs_gauss else gaussian
                    gfit = gfun(
                        self.qgauss[i], *self.gauss_fits[self.rec_ax_idx[i]][idx]
                    )
                    self.fits[i].set_ydata(gfit)

                if self.relim_int is True:
                    ax[i + 1].relim()
                    ax[i + 1].autoscale_view()

        self.fig.canvas.draw()

    def show(self):
        """
        Display the interactive plot.
        """
        selector = ipw.HBox(
            [self._select_plot, self._iflog], layout=dict(border="1px solid grey")
        )
        gui = ipw.VBox([selector, self._figout])
        display(gui)
