:orphan:

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
   * - :py:obj:`calc_coms_qspace3d <sxdm.process.math.calc_coms_qspace3d>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace3d
          :summary:
   * - :py:obj:`calc_roi_sum <sxdm.process.math.calc_roi_sum>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_roi_sum
          :summary:
   * - :py:obj:`calc_coms_qspace2d <sxdm.process.math.calc_coms_qspace2d>`
     - .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace2d
          :summary:

API
~~~

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

.. py:function:: calc_coms_qspace3d(path_qspace, mask_reciprocal, n_pix=None, std=False)
   :canonical: sxdm.process.math.calc_coms_qspace3d

   .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace3d

.. py:function:: calc_roi_sum(path_qspace, mask_reciprocal, mask_direct=None, n_proc=None)
   :canonical: sxdm.process.math.calc_roi_sum

   .. autodoc2-docstring:: sxdm.process.math.calc_roi_sum

.. py:function:: calc_coms_qspace2d(path_dset, scan_no, qx, qy, qz, mask_rec=None, n_threads=None, detector='mpx1x4', n_pix=None, std=None, path_data_h5='/{scan_no}/instrument/{detector}/data')
   :canonical: sxdm.process.math.calc_coms_qspace2d

   .. autodoc2-docstring:: sxdm.process.math.calc_coms_qspace2d
