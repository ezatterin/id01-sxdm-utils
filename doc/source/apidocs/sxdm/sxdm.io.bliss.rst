:py:mod:`sxdm.io.bliss`
=======================

.. py:module:: sxdm.io.bliss

.. autodoc2-docstring:: sxdm.io.bliss
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`get_sxdm_scan_numbers <sxdm.io.bliss.get_sxdm_scan_numbers>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_scan_numbers
          :summary:
   * - :py:obj:`get_datetime <sxdm.io.bliss.get_datetime>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_datetime
          :summary:
   * - :py:obj:`get_det_params <sxdm.io.bliss.get_det_params>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_det_params
          :summary:
   * - :py:obj:`get_piezo_motor_names <sxdm.io.bliss.get_piezo_motor_names>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_piezo_motor_names
          :summary:
   * - :py:obj:`get_piezo_motor_positions <sxdm.io.bliss.get_piezo_motor_positions>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_piezo_motor_positions
          :summary:
   * - :py:obj:`get_roidata <sxdm.io.bliss.get_roidata>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_roidata
          :summary:
   * - :py:obj:`get_counter_sxdm <sxdm.io.bliss.get_counter_sxdm>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_counter_sxdm
          :summary:
   * - :py:obj:`get_sxdm_frame_sum <sxdm.io.bliss.get_sxdm_frame_sum>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_frame_sum
          :summary:
   * - :py:obj:`get_sxdm_pos_sum <sxdm.io.bliss.get_sxdm_pos_sum>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_pos_sum
          :summary:
   * - :py:obj:`get_roi_pos <sxdm.io.bliss.get_roi_pos>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_roi_pos
          :summary:
   * - :py:obj:`get_scan_table <sxdm.io.bliss.get_scan_table>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_scan_table
          :summary:
   * - :py:obj:`get_sxdm_frame_sum_multi <sxdm.io.bliss.get_sxdm_frame_sum_multi>`
     - .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_frame_sum_multi
          :summary:

API
~~~

.. py:function:: get_sxdm_scan_numbers(h5f, interrupted_scans=False)
   :canonical: sxdm.io.bliss.get_sxdm_scan_numbers

   .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_scan_numbers

.. py:function:: get_datetime(h5f, scan_no)
   :canonical: sxdm.io.bliss.get_datetime

   .. autodoc2-docstring:: sxdm.io.bliss.get_datetime

.. py:function:: get_det_params(h5f, scan_no)
   :canonical: sxdm.io.bliss.get_det_params

   .. autodoc2-docstring:: sxdm.io.bliss.get_det_params

.. py:function:: get_piezo_motor_names(h5f, scan_no)
   :canonical: sxdm.io.bliss.get_piezo_motor_names

   .. autodoc2-docstring:: sxdm.io.bliss.get_piezo_motor_names

.. py:function:: get_piezo_motor_positions(h5f, scan_no)
   :canonical: sxdm.io.bliss.get_piezo_motor_positions

   .. autodoc2-docstring:: sxdm.io.bliss.get_piezo_motor_positions

.. py:function:: get_roidata(h5f, scan_no, roi_name, return_pi_motors=False)
   :canonical: sxdm.io.bliss.get_roidata

   .. autodoc2-docstring:: sxdm.io.bliss.get_roidata

.. py:function:: get_counter_sxdm(h5f, scan_no, counter, return_pi_motors=False)
   :canonical: sxdm.io.bliss.get_counter_sxdm

   .. autodoc2-docstring:: sxdm.io.bliss.get_counter_sxdm

.. py:function:: get_sxdm_frame_sum(path_dset, scan_no, mask_sample=None, detector=None, n_proc=None, pbar=True, path_data_h5='/{scan_no}/instrument/{detector}/data', roi=None)
   :canonical: sxdm.io.bliss.get_sxdm_frame_sum

   .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_frame_sum

.. py:function:: get_sxdm_pos_sum(path_dset, scan_no, mask_detector=None, detector=None, n_proc=None, pbar=True, path_data_h5='/{scan_no}/instrument/{detector}/data')
   :canonical: sxdm.io.bliss.get_sxdm_pos_sum

   .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_pos_sum

.. py:function:: get_roi_pos(h5f, scan_no, roi_names_list, detector='mpx1x4')
   :canonical: sxdm.io.bliss.get_roi_pos

   .. autodoc2-docstring:: sxdm.io.bliss.get_roi_pos

.. py:function:: get_scan_table(path_dset)
   :canonical: sxdm.io.bliss.get_scan_table

   .. autodoc2-docstring:: sxdm.io.bliss.get_scan_table

.. py:function:: get_sxdm_frame_sum_multi(path_framesum, path_dset, scan_nums=None, detector=None, path_data_h5='/{scan_no}/instrument/{detector}/data')
   :canonical: sxdm.io.bliss.get_sxdm_frame_sum_multi

   .. autodoc2-docstring:: sxdm.io.bliss.get_sxdm_frame_sum_multi
