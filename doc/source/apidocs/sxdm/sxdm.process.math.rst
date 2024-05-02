:py:mod:`sxdm.process.math`
===========================

.. py:module:: sxdm.process.math

.. autodoc2-docstring:: sxdm.process.math
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`_gauss_fit_point <sxdm.process.math._gauss_fit_point>`
     - .. autodoc2-docstring:: sxdm.process.math._gauss_fit_point
          :summary:
   * - :py:obj:`_gauss_fit_multi_point <sxdm.process.math._gauss_fit_multi_point>`
     - .. autodoc2-docstring:: sxdm.process.math._gauss_fit_multi_point
          :summary:
   * - :py:obj:`gauss_fit <sxdm.process.math.gauss_fit>`
     - .. autodoc2-docstring:: sxdm.process.math.gauss_fit
          :summary:
   * - :py:obj:`get_nearest_index <sxdm.process.math.get_nearest_index>`
     - .. autodoc2-docstring:: sxdm.process.math.get_nearest_index
          :summary:
   * - :py:obj:`ang_between <sxdm.process.math.ang_between>`
     - .. autodoc2-docstring:: sxdm.process.math.ang_between
          :summary:
   * - :py:obj:`calc_com_2d <sxdm.process.math.calc_com_2d>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_com_2d
          :summary:
   * - :py:obj:`calc_com_3d <sxdm.process.math.calc_com_3d>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_com_3d
          :summary:
   * - :py:obj:`_calc_com_qspace3d <sxdm.process.math._calc_com_qspace3d>`
     - .. autodoc2-docstring:: sxdm.process.math._calc_com_qspace3d
          :summary:
   * - :py:obj:`calc_coms_qspace3d <sxdm.process.math.calc_coms_qspace3d>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace3d
          :summary:
   * - :py:obj:`_calc_roi_sum_chunk <sxdm.process.math._calc_roi_sum_chunk>`
     - .. autodoc2-docstring:: sxdm.process.math._calc_roi_sum_chunk
          :summary:
   * - :py:obj:`calc_roi_sum <sxdm.process.math.calc_roi_sum>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_roi_sum
          :summary:
   * - :py:obj:`_calc_com_idx <sxdm.process.math._calc_com_idx>`
     - .. autodoc2-docstring:: sxdm.process.math._calc_com_idx
          :summary:
   * - :py:obj:`calc_coms_qspace2d <sxdm.process.math.calc_coms_qspace2d>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace2d
          :summary:

API
~~~

.. py:function:: _gauss_fit_point(path_qspace, roi_slice, rec_axis, qcoords, dir_mask, dir_idx)
   :canonical: sxdm.process.math._gauss_fit_point

   .. autodoc2-docstring:: sxdm.process.math._gauss_fit_point

.. py:function:: _gauss_fit_multi_point(path_qspace, roi_slice, rec_axis, qcoords, mask, dir_idx)
   :canonical: sxdm.process.math._gauss_fit_multi_point

   .. autodoc2-docstring:: sxdm.process.math._gauss_fit_multi_point

.. py:function:: gauss_fit(path_qspace, rec_mask, dir_mask=None, multi=False)
   :canonical: sxdm.process.math.gauss_fit

   .. autodoc2-docstring:: sxdm.process.math.gauss_fit

.. py:function:: get_nearest_index(arr, val)
   :canonical: sxdm.process.math.get_nearest_index

   .. autodoc2-docstring:: sxdm.process.math.get_nearest_index

.. py:function:: ang_between(v1, v2)
   :canonical: sxdm.process.math.ang_between

   .. autodoc2-docstring:: sxdm.process.math.ang_between

.. py:function:: calc_com_2d(arr, x, y, n_pix=None, std=False)
   :canonical: sxdm.process.math.calc_com_2d

   .. autodoc2-docstring:: sxdm.process.math.calc_com_2d

.. py:function:: calc_com_3d(arr, x, y, z, n_pix=None, std=False)
   :canonical: sxdm.process.math.calc_com_3d

   .. autodoc2-docstring:: sxdm.process.math.calc_com_3d

.. py:function:: _calc_com_qspace3d(path_qspace, mask_reciprocal, idx, n_pix=None, std=False)
   :canonical: sxdm.process.math._calc_com_qspace3d

   .. autodoc2-docstring:: sxdm.process.math._calc_com_qspace3d

.. py:function:: calc_coms_qspace3d(path_qspace, mask_reciprocal, n_pix=None, std=False)
   :canonical: sxdm.process.math.calc_coms_qspace3d

   .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace3d

.. py:function:: _calc_roi_sum_chunk(path_qspace, mask_reciprocal, mask_direct, idx_range)
   :canonical: sxdm.process.math._calc_roi_sum_chunk

   .. autodoc2-docstring:: sxdm.process.math._calc_roi_sum_chunk

.. py:function:: calc_roi_sum(path_qspace, mask_reciprocal, mask_direct=None, n_proc=None)
   :canonical: sxdm.process.math.calc_roi_sum

   .. autodoc2-docstring:: sxdm.process.math.calc_roi_sum

.. py:function:: _calc_com_idx(path_h5, path_in_h5, mask_idxs, qx, qy, qz, idx_list, **kwargs)
   :canonical: sxdm.process.math._calc_com_idx

   .. autodoc2-docstring:: sxdm.process.math._calc_com_idx

.. py:function:: calc_coms_qspace2d(path_dset, scan_no, qx, qy, qz, mask_rec=None, n_threads=None, detector='mpx1x4', n_pix=None, std=None, path_data_h5='/{scan_no}/instrument/{detector}/data')
   :canonical: sxdm.process.math.calc_coms_qspace2d

   .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace2d
