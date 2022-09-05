import os
import numpy as np
import multiprocessing as mp
import shutil
import glob
import h5py
import hdf5plugin
import xsocs

from functools import partial
import scipy.ndimage as ndi

from xsocs.io.XsocsH5 import XsocsH5
from xsocs.process.qspace import qspace_conversion
from xsocs.process.qspace import QSpaceConverter

from id01lib.io.bliss import get_positioner
from id01lib.xrd.qspace.bliss import _det_aliases


def grid_qspace_xsocs(
    path_qconv,
    path_master,
    nbins,
    roi=None,
    medfilt_dims=None,
    offsets=None,
    overwrite=False,
    correct_mpx_gaps=True,
    normalizer=None,
    mask=None,
    n_proc=None,
    center_chan=None,
    chan_per_deg=None
):

    converter = QSpaceConverter(
        path_master,
        nbins,
        roi=roi,
        medfilt_dims=medfilt_dims,
        output_f=path_qconv,
        offsets=offsets,
    )

    converter.maxipix_correction = correct_mpx_gaps
    converter.normalizer = normalizer
    converter.mask = mask
    converter.n_proc = n_proc
    converter.disp_times = True
    if center_chan:
        converter.direct_beam = center_chan
    if chan_per_deg:
        converter.channels_per_degree = chan_per_deg

    converter.convert(overwrite=overwrite)

    rc = converter.status
    if rc != QSpaceConverter.DONE:
        raise ValueError(
            "Conversion failed with CODE={0} :\n"
            "{1}"
            ""
            "".format(converter.status, converter.status_msg)
        )


def get_qspace_vals_xsocs(path_master, offsets=dict()):

    h5f = XsocsH5(path_master)
    entry0 = h5f.get_entry_name(entry_idx=0)
    with h5f:
        detpath = h5f._XsocsH5Base__file[f"/{entry0}/measurement/image/data"].name
        detalias = detpath.split("/")[-1]

    det = _det_aliases[detalias]
    angles = {key: None for key in "phi,eta,nu,del".split(",")}
    for a in angles:
        angles[a] = np.sort(np.array([h5f.positioner(e, a) for e in h5f.entries()]))

    nrj, cen_pix, cpd = h5f.acquisition_params().values()

    q_array = qspace_conversion(
        det.pixnum, cen_pix[::-1], cpd, nrj, *angles.values(), offsets=offsets
    )

    qx, qy, qz = q_array.transpose(3, 0, 1, 2)

    return qx, qy, qz


def estimate_n_bins(path_master, offsets=dict()):

    qx, qy, qz = get_qspace_vals_xsocs(path_master, offsets=offsets)

    maxbins = []
    for dim in (qx, qy, qz):
        maxbin = np.inf
        for j in range(dim.ndim):
            step = abs(np.diff(dim, axis=j)).max()
            bins = (abs(dim).max() - abs(dim).min()) / step
            maxbin = min(maxbin, bins)
        maxbins.append(int(maxbin) + 1)

    return maxbins


def _get_eta_shift(path_dset, shifts):
    with h5py.File(path_dset, "r") as h5f:
        scan_nums = [f"{x}.1" for x in range(1, len(list(h5f.keys())) + 1)]

    etashift = dict()
    for s, shift in zip(scan_nums, shifts):
        eta = np.round(get_positioner(path_dset, s, "eta"), 4)
        etashift[str(eta)] = shift

    return etashift


def _shift_write_data(path_dset, shifts, subh5):

    etashift = _get_eta_shift(path_dset, shifts)
    root = subh5.split("_")[-1][:-3]

    with h5py.File(subh5, "r", libver="latest") as h5f:

        data = h5f[f"/{root}/instrument/detector/data"]
        eta = str(np.round(h5f[f"{root}/instrument/positioners/eta"][()], 4))
        shift = etashift[eta]

        map_sh = [h5f[f"{root}/scan/motor_{i}_steps"][()] for i in (0, 1)]  # (x, y)
        data_sh = data.shape  # (x*y, detx, dety)

        n_chunks = 20
        frames_sh = data.shape[1]
        chunk_size = frames_sh // n_chunks

        c0 = [x for x in range(0, frames_sh, chunk_size)]
        c1 = [x for x in c0.copy()[1:]] + [frames_sh]
        idxs = list(zip(c0, c1))

        fname_subh5_shifted = os.path.abspath(subh5).split(".")[0]
        fname_subh5_shifted = shutil.copy(subh5, f"{fname_subh5_shifted}.1_shifted.h5")

        with h5py.File(fname_subh5_shifted, "a", libver="latest") as f:
            det_shift = f[f"{root}/instrument/detector/"]
            data_shift_link = [f"{root}measurement/image/data"]

            del det_shift["data"]
            data_shift = det_shift.create_dataset(
                "data",
                shape=data_sh,
                chunks=(1, len(idxs), len(idxs)),
                dtype=data.dtype,
                **hdf5plugin.Bitshuffle(nelems=0, lz4=True),
            )
            data_shift_link = data_shift

            def shift_write_data(frame_idxs):

                # load and reshape
                i0, i1 = frame_idxs
                dmap = data[:, i0:i1, i0:i1]
                dmap = dmap.reshape(*map_sh, (i1 - i0) ** 2)

                # shift
                if not np.allclose(shift, 0, atol=1e-3):
                    for i in range(dmap.shape[-1]):
                        dmap[..., i] = ndi.shift(dmap[..., i], shift)

                # reshape and write
                dmap = dmap.reshape(data_sh[0], i1 - i0, i1 - i0)
                data_shift[:, i0:i1, i0:i1] = dmap
                del dmap

            # TODO better printing!
            print(f"Shifting #{root}...")
            for i, idx_pair in enumerate(idxs):
                # print(f"\r{i}/{len(idxs)}", flush=True, end=" ")
                shift_write_data(idx_pair)
            print(f"#{root} done.")

def _make_shift_master(path_out, path_dset):

    namelist = os.path.basename(path_dset).split(".")[0].split("_")
    name_sample = "_".join(namelist[:-1])
    name_dset = namelist[-1]

    master_shifted = shutil.copy(
        f"{path_out}/{name_sample}_{name_dset}_master.h5",
        f"{path_out}/{name_sample}_{name_dset}_master_shifted.h5",
    )

    with h5py.File(master_shifted, "a") as h5f:
        scan_nos = list(h5f.keys())
        for s in scan_nos:
            ftolink = f"{name_sample}_{name_dset}_{s}_shifted.h5"
            del h5f[s]
            h5f[s] = h5py.ExternalLink(ftolink, f"/{s}")


# TODO use concurrent.futures instead
def shift_xsocs_data(path_dset, path_out, shifts):
    print(f"Using XSOCS installation: {xsocs.__file__}\n")
    name_sample = os.path.basename(path_dset).split("_")[0]
    subh5_list = glob.glob(f"{path_out}/{name_sample}*.1.h5")

    with mp.Pool() as pool:
        pf = partial(_shift_write_data, path_dset, shifts)
        pool.map(pf, subh5_list)

    _make_shift_master(path_out, path_dset)
