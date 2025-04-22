"""
Helper functions useful to plot SXDM maps.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import gif
import os

from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from matplotlib.patches import FancyArrowPatch, Rectangle, ArrowStyle

from tqdm.notebook import tqdm

from ..io.bliss import (
    get_piezo_motor_names,
    get_roidata,
    get_sxdm_frame_sum,
    get_detector_aliases,
    get_sxdm_pos_sum,
    get_counter,
    get_positioner,
    get_sxdm_scan_numbers,
    get_scan_shape,
)

from ..utils import get_q_extents


def add_hsv_colorbar(
    tiltmag,
    ax,
    labels,
    size="20%",
    pad=0.05,
    magnitude_precision=2,
    origin="lower",
    **kwargs,
):
    prec = magnitude_precision
    a, b = np.meshgrid(np.linspace(0, 1, 100), np.linspace(180, -180, 100))
    cmap = make_hsv(a, b, **kwargs)

    cax = make_axes_locatable(ax).append_axes("right", size=size, pad=pad)
    cax.imshow(cmap, aspect="auto", origin=origin)

    cax.tick_params(
        labelsize="small", left=False, right=True, labelleft=False, labelright=True
    )
    cax.locator_params(axis="y", tight=True, nbins=7)

    cax.set_yticks([0, 25, 50, 75, 100])
    cax.set_yticklabels(labels)

    cax.set_xticks([0, 99])
    cax.set_xticklabels(
        [f"{tiltmag.min():.{prec}f}", f"{tiltmag.max():.{prec}f}"], rotation=40
    )

    cax.yaxis.set_label_position("right")
    cax.set_ylabel(r"Direction", labelpad=3, fontsize="small")
    cax.set_xlabel(r"Magnitude $(\degree)$", labelpad=1, fontsize="small")

    return cax


def make_hsv(tiltmag, azimuth, stretch=False, v2s=False):
    # hue is the azimuth - normalised [0,1] - needed for HSV
    h = (azimuth % 360) / (360)

    # saturation is the tilt - normalised [0,1]
    s = np.abs(tiltmag)
    if stretch:
        s -= s.min()
    s /= s.max()

    # value is just 1
    v = np.ones_like(h)

    # stack the array
    if v2s:
        im = np.dstack((h, v, s))
    else:
        im = np.dstack((h, s, v))
    im = mpl.colors.hsv_to_rgb(im)

    return im


def add_scalebar(
    ax,
    h_size=None,
    v_size=None,
    label=None,
    color="black",
    loc="lower right",
    pad=0.5,
    sep=5,
    **font_kwargs,
):
    """
    Add a scale bar to a Matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to which the scale bar is added.
    h_size : float, optional
        Horizontal size of the scale bar in data units.
        If None, defaults to a quarter of the image width.
    v_size : float, optional
        Vertical size of the scale bar in data units.
        If None, defaults to 1/100 of the image height.
    label : str, optional
        Label for the scale bar. If None, defaults to the horizontal size.
    color : str, optional
        Color of the scale bar and label. Default is 'black'.
    loc : str or int, optional
        Location code or descriptive string to position the scale bar.
        Default is 'lower right'.
    pad : float, optional
        Padding between the scale bar and the anchor point. Default is 0.5.
    sep : int, optional
        Separation between the scale bar and the label. Default is 5.
    **font_kwargs
        Additional keyword arguments for font properties of the label.

    Returns
    -------
    None
    """
    # size of the img in data coords
    try:
        img = ax.get_images()[0]
        ext = img.get_extent()  # left, right, bottom, top
        xsize, ysize = (ext[1] - ext[0], ext[3] - ext[2])
    except (AttributeError, IndexError):
        img = [x for x in ax.get_children() if type(x) is mpl.collections.QuadMesh][0]
        xc, yc = img.get_coordinates().T
        xsize, ysize = [c.max() - c.min() for c in (xc, yc)]

    # size of the scalebar wrt the image size in um or nm
    if h_size is None:
        h_size = xsize // 4
    if v_size is None:
        v_size = ysize // 100

    # label
    if label is None:
        label = f"{h_size:.0f}"

    # the scale bar object
    fontprops = fm.FontProperties(**font_kwargs)
    scalebar = AnchoredSizeBar(
        ax.transData,
        h_size,
        label,
        loc,
        color=color,
        frameon=False,
        size_vertical=v_size,
        pad=pad,
        sep=sep,
        fontproperties=fontprops,
    )

    # add scalebar to ax
    ax.add_artist(scalebar)


def add_colorbar(
    ax,
    mappable,
    loc="right",
    size="3%",
    pad=0.05,
    label_size="small",
    scientific_notation=False,
    **kwargs,
):
    """
    Add a colorbar to the given axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to which the colorbar will be added.
    mappable : matplotlib.cm.ScalarMappable
        The mappable object that the colorbar will be based on.
    loc : str, optional
        The location where the colorbar will be placed. Default is "right".
    size : str or float, optional
        The size of the colorbar. Default is "3%".
    pad : float, optional
        The padding between the colorbar and the axes. Default is 0.05.
    label_size : str or int, optional
        The size of the colorbar labels. Default is "small".
    scientific_notation : bool, optional
        Whether to use scientific notation for colorbar labels. Default is False.
    **kwargs
        Additional keyword arguments to be passed to matplotlib.colorbar.Colorbar.

    Returns
    -------
    matplotlib.colorbar.Colorbar
        The colorbar object.
    """

    fig = ax.get_figure()
    cax = make_axes_locatable(ax).append_axes(loc, size=size, pad=pad)
    cax.tick_params(labelsize=label_size)
    cbar = fig.colorbar(mappable, cax=cax, **kwargs)
    if scientific_notation:
        cax.ticklabel_format(
            axis="y", style="scientific", scilimits=(0, 0), useMathText=True
        )

    return cbar


def add_roi_box(ax, roi, **kwargs):
    rect = Rectangle((roi[0], roi[2]), roi[1] - roi[0], roi[3] - roi[2], **kwargs)
    ax.add_patch(rect)


def add_letter(ax, letter, x=0.03, y=0.92, fs="large", fw="bold", **kwargs):
    txt = ax.text(
        x, y, letter, transform=ax.transAxes, fontweight=fw, fontsize=fs, **kwargs
    )
    return txt


def add_roilabel(ax, roi, loc="upper left", frameon=False, pad=0.05, prop=None):
    if prop is None:
        prop = dict(
            color="black",
            fontsize="small",
            bbox=dict(facecolor="whitesmoke", alpha=0.7, lw=0, pad=1.5),
        )

    at = mpl.offsetbox.AnchoredText(roi, loc=loc, frameon=frameon, pad=pad, prop=prop)

    ax.add_artist(at)


def add_directions(
    ax,
    text_x,
    text_y,
    loc="lower left",
    color="k",
    transform=None,
    angle=0,
    length=0.1,
    line_width=0.5,
    aspect_ratio=1,
    head_width=1.2,
    head_length=3,
    arrow_props=None,
    tpad_x=0.01,
    tpad_y=0.01,
    text_props=None,
    pad=0.4,
    borderpad=0.5,
    frameon=False,
    return_artist=False,
):
    """
    Add directional arrows with labels to a Matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to which the arrows and labels are added.
    text_x : str
        Label for the x-direction arrow.
    text_y : str
        Label for the y-direction arrow.
    loc : str or int, optional
        Location code or descriptive string to position the arrows and labels.
        Default is 'lower left'. Valid locations are 'upper left', 'upper center',
        'upper right', 'center left', 'center', 'center right', 'lower left',
        'lower center', 'lower right'.
    color : str, optional
        Color for the arrows and labels. Default is 'k' (black).
    transform : matplotlib.transforms.Transform, optional
        Transformation applied to the arrows and labels. Default is None.
    angle : float, optional
        Rotation angle for the arrows in degrees. Default is 0.
    length : float, optional
        Length of the arrows. Default is 0.1.
    line_width : float, optional
        Line width of the arrows. Default is 0.5.
    aspect_ratio : float, optional
        Aspect ratio of the y-direction arrow relative to the x-direction arrow.
        Default is 1.
    head_width : float, optional
        Width of the arrow heads. Default is 1.2.
    head_length : float, optional
        Length of the arrow heads. Default is 3.
    arrow_props : dict, optional
        Additional properties for the arrows. Default is None.
    tpad_x : float, optional
        Padding between the x-direction arrow and its label. Default is 0.01.
    tpad_y : float, optional
        Padding between the y-direction arrow and its label. Default is 0.01.
    text_props : dict, optional
        Additional properties for the text labels. Default is None.
    pad : float, optional
        Padding between the anchored box and the arrows. Default is 0.4.
    borderpad : float, optional
        Padding between the border of the anchored box and its content. Default is 0.5.
    frameon : bool, optional
        Whether to draw a frame around the anchored box. Default is False.
    return_artist : bool, optional
        If True, returns the anchored box artist instead of adding it to the axis.
        Default is False.

    Returns
    -------
    matplotlib.offsetbox.AnchoredOffsetbox or None
        The anchored box artist if `return_artist` is True, otherwise None.
    """

    # arrows
    alx = length
    aly = length * aspect_ratio

    arrowstyle = ArrowStyle("->", head_width=head_width, head_length=head_length)
    if arrow_props is None:
        arrow_props = dict()
    if "color" not in arrow_props:
        arrow_props["color"] = color
    if "linewidth" not in arrow_props:
        arrow_props["linewidth"] = line_width

    a_coords = [(0, aly), (alx, 0)]
    arr_x, arr_y = [
        FancyArrowPatch(
            (0, 0),
            c,
            arrowstyle=arrowstyle,
            shrinkA=0.0,
            shrinkB=0.0,
            **arrow_props,
        )
        for c in a_coords
    ]

    # text
    if text_props is None:
        text_props = dict()
    if "color" not in text_props:
        text_props["color"] = color

    t_coords = [((alx + tpad_x), 0), (0, (aly + tpad_y))]
    t_align = [dict(va="center"), dict(ha="center")]

    txt_x, txt_y = [
        mpl.text.Text(
            *c,
            t,
            transform=transform,
            **al,
            **text_props,
        )
        for c, t, al in zip(t_coords, [text_x, text_y], t_align)
    ]

    # box
    if transform is None:
        transform = ax.transAxes

    t_start = transform
    t_end = t_start + mpl.transforms.Affine2D().rotate_deg(angle)

    box = mpl.offsetbox.AuxTransformBox(t_end)
    [box.add_artist(a) for a in (arr_x, arr_y, txt_x, txt_y)]

    # anchored box
    abox = mpl.offsetbox.AnchoredOffsetbox(
        loc,
        child=box,
        pad=pad,
        borderpad=borderpad,
        frameon=frameon,
    )

    if return_artist:
        return abox
    else:
        ax.add_artist(abox)


def gif_sxdm_sums(
    path_dset,
    path_out=None,
    scan_nos=None,
    time_between_frames=500,
    moving_motor="eta",
    clim_sample=[None, None],
    clim_detector=[None, None],
    detector=None,
):
    """
    Generate a GIF for a series of SXDM scans showing data integrated in direct (sample)
    and reciprocal (detector) space.

    Parameters
    ----------
    path_dset : str
        Path to the HDF5 BLISS dataset.
    path_out : str, optional
        Output path for the .gif file. Defaults to '.'.
    scan_nos : list
        List of scan numbers.
    time_between_frames : int, optional
        Interval between frames of the GIF in milliseconds. Defaults to 500.
    moving_motor : str, optional
        Name of the BLISS motor whose value is changing between one SXDM scan and the
        next. Defaults to "eta".
    clim_sample : list, optional
        Color limit range for the sample plot. Defaults to [None, None].
    clim_detector : list, optional
        Color limit range for the detector plot. Defaults to [None, None].
    detector : str or None, optional
        Detector alias. If None, the first detector found is used. Defaults to None.

    Returns
    -------
    None
    """

    if path_out is None:
        path_out = os.path.abspath(".")

    if scan_nos is None:
        scan_nos = get_sxdm_scan_numbers(path_dset)

    if detector is None:
        det = get_detector_aliases(path_dset, scan_nos[0])[0]
    else:
        det = detector

    @gif.frame
    def plot_sxdm_sums(scan_no):
        fint = get_sxdm_frame_sum(path_dset, scan_no, detector=det, pbar=False)
        try:
            dint = get_roidata(path_dset, scan_no, f"{det}_int")
        except KeyError:
            dint = get_sxdm_pos_sum(path_dset, scan_no, detector=det, pbar=False)
            map_shape = get_scan_shape(path_dset, scan_no)
            dint = dint.reshape(map_shape)

        fig, ax = plt.subplots(1, 2, figsize=(6, 3), layout="tight", dpi=120)

        m0name, m1name = get_piezo_motor_names(path_dset, scan_no)
        try:
            m0, m1 = [
                get_counter(path_dset, scan_no, f"{m}_position")
                for m in (m0name, m1name)
            ]
        except KeyError:
            m0, m1 = [get_counter(path_dset, scan_no, f"{m}") for m in (m0name, m1name)]
        pi_ext = [m0.min(), m0.max(), m1.min(), m1.max()]

        _ = ax[0].imshow(
            dint,
            cmap="viridis",
            extent=pi_ext,
            norm=mpl.colors.LogNorm(*clim_sample),
            origin="lower",
        )
        _ = ax[1].imshow(
            fint,
            norm=mpl.colors.LogNorm(*clim_detector),
            origin="upper",
            cmap="inferno",
        )

        for a in ax:
            _ = add_colorbar(a, a.get_images()[0])

        ax[0].set_title("Sum over (detx, dety)")
        ax[0].set_xlabel(f"{m0name} (um)")
        ax[0].set_ylabel(f"{m1name} (um)")

        ax[1].set_title(f"Sum over ({m0name}, {m1name})")
        ax[1].set_xlabel("detx (pix)")
        ax[1].set_ylabel("dety (pix)")

        moving_mot = get_positioner(path_dset, scan_no, moving_motor)
        title = f"{os.path.basename(path_dset)} #{scan_no}"
        title += f"@ {moving_motor}$={moving_mot:.3f}$"

        fig.subplots_adjust(hspace=-0.5)
        fig.suptitle(title, y=0.94)

    frames = []
    for s in tqdm(scan_nos):
        frames.append(plot_sxdm_sums(s))

    gif.save(
        frames,
        f"{path_out}/macro_{os.path.basename(path_dset)}_framesums.gif",
        duration=time_between_frames,
    )


def gif_sxdm(
    path_dset,
    detector_roi=None,
    scan_nos=None,
    gif_duration=5,
    moving_motor="eta",
    clim_sample=[None, None],
    detector=None,
):
    """
    Generate a GIF for a series of SXDM scans for a selected detector ROI.

    Parameters
    ----------
    path_dset : str
        Path to the HDF5 BLISS dataset.
    detector_roi : str or None, optional
        Region of interest (ROI) for the detector. If None, the full detector is used.
        Defaults to None.
    scan_nos : list or None, optional
        List of scan numbers. If None, all SXDM scan numbers are used. Defaults to None.
    gif_duration : int, optional
        Duration of the GIF in seconds. Defaults to 5.
    moving_motor : str, optional
        Name of the BLISS motor whose value is changing between one SXDM scan and the
        next. Defaults to "eta".
    clim_sample : list, optional
        Color limit range for the sample plot. Defaults to [None, None].
    detector : str or None, optional
        Detector alias. If None, the first detector found is used. Defaults to None.

    Returns
    -------
    None
    """

    if scan_nos is None:
        scan_nos = get_sxdm_scan_numbers(path_dset)

    if detector is None:
        det = get_detector_aliases(path_dset, scan_nos[0])[0]
    else:
        det = detector

    @gif.frame
    def plot_sxdm_sums(scan_no):
        if detector_roi is None:
            try:
                dint = get_roidata(path_dset, scan_no, f"{det}_int")
            except KeyError:
                dint = get_sxdm_pos_sum(path_dset, scan_no, detector=det, pbar=False)
        else:
            dint = get_roidata(path_dset, scan_no, detector_roi)

        fig, ax = plt.subplots(1, 1, figsize=(4, 3), layout="tight", dpi=120)

        m0name, m1name = get_piezo_motor_names(path_dset, scan_no)
        try:
            m0, m1 = [get_counter(path_dset, scan_no, f"{m}") for m in (m0name, m1name)]
        except KeyError:
            m0, m1 = [
                get_counter(path_dset, scan_no, f"{m}_position")
                for m in (m0name, m1name)
            ]
        pi_ext = [m0.min(), m0.max(), m1.min(), m1.max()]

        im = ax.imshow(
            dint,
            cmap="viridis",
            extent=pi_ext,
            norm=mpl.colors.LogNorm(*clim_sample),
        )

        _ = add_colorbar(ax, im)

        ax.set_title("Sum over (detx, dety)")
        ax.set_xlabel(f"{m0name} (um)")
        ax.set_ylabel(f"{m1name} (um)")

        moving_mot = get_positioner(path_dset, scan_no, moving_motor)
        title = f"{os.path.basename(path_dset)} #{scan_no}"
        title += f"@ {moving_motor}$={moving_mot:.3f}$"

        ax.set_title(title)

    frames = []
    for s in tqdm(scan_nos):
        frames.append(plot_sxdm_sums(s))

    gif.save(
        frames,
        f"macro_{os.path.basename(path_dset)}_roi_int.gif",
        duration=gif_duration,
        unit="seconds",
        between="startend",
    )
