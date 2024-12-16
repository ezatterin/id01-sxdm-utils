# {py:mod}`sxdm.utils.general`

```{py:module} sxdm.utils.general
```

```{autodoc2-docstring} sxdm.utils.general
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_qspace_coords <sxdm.utils.general.get_qspace_coords>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_qspace_coords
    :summary:
    ```
* - {py:obj}`get_filelist <sxdm.utils.general.get_filelist>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_filelist
    :summary:
    ```
* - {py:obj}`get_pi_extents <sxdm.utils.general.get_pi_extents>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_pi_extents
    :summary:
    ```
* - {py:obj}`get_q_extents <sxdm.utils.general.get_q_extents>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_q_extents
    :summary:
    ```
* - {py:obj}`get_detector_roilist <sxdm.utils.general.get_detector_roilist>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_detector_roilist
    :summary:
    ```
* - {py:obj}`get_shift_dset <sxdm.utils.general.get_shift_dset>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_shift_dset
    :summary:
    ```
* - {py:obj}`get_shift <sxdm.utils.general.get_shift>`
  - ```{autodoc2-docstring} sxdm.utils.general.get_shift
    :summary:
    ```
* - {py:obj}`calc_refl_id01 <sxdm.utils.general.calc_refl_id01>`
  - ```{autodoc2-docstring} sxdm.utils.general.calc_refl_id01
    :summary:
    ```
* - {py:obj}`slice_from_mask <sxdm.utils.general.slice_from_mask>`
  - ```{autodoc2-docstring} sxdm.utils.general.slice_from_mask
    :summary:
    ```
````

### API

````{py:function} get_qspace_coords(h5f)
:canonical: sxdm.utils.general.get_qspace_coords

```{autodoc2-docstring} sxdm.utils.general.get_qspace_coords
```
````

````{py:function} get_filelist(sample_dir)
:canonical: sxdm.utils.general.get_filelist

```{autodoc2-docstring} sxdm.utils.general.get_filelist
```
````

````{py:function} get_pi_extents(m0, m1, winidx)
:canonical: sxdm.utils.general.get_pi_extents

```{autodoc2-docstring} sxdm.utils.general.get_pi_extents
```
````

````{py:function} get_q_extents(qx, qy, qz)
:canonical: sxdm.utils.general.get_q_extents

```{autodoc2-docstring} sxdm.utils.general.get_q_extents
```
````

````{py:function} get_detector_roilist(pscan, detector)
:canonical: sxdm.utils.general.get_detector_roilist

```{autodoc2-docstring} sxdm.utils.general.get_detector_roilist
```
````

````{py:function} get_shift_dset(path_dset, roi, scan_nums, log=False, med_filt=None, return_maps=False, **xcorr_kwargs)
:canonical: sxdm.utils.general.get_shift_dset

```{autodoc2-docstring} sxdm.utils.general.get_shift_dset
```
````

````{py:function} get_shift(images, med_filt=None, **xcorr_kwargs)
:canonical: sxdm.utils.general.get_shift

```{autodoc2-docstring} sxdm.utils.general.get_shift
```
````

````{py:function} calc_refl_id01(hkl, material, ip_dir, oop_dir, nrj, bounds={'eta': (-2, 120), 'phi': (-180, 180), 'nu': 0, 'delta': (-2, 130)}, return_q_com=False)
:canonical: sxdm.utils.general.calc_refl_id01

```{autodoc2-docstring} sxdm.utils.general.calc_refl_id01
```
````

````{py:function} slice_from_mask()
:canonical: sxdm.utils.general.slice_from_mask

```{autodoc2-docstring} sxdm.utils.general.slice_from_mask
```
````
