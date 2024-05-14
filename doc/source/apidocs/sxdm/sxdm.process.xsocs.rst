:py:mod:`sxdm.process.xsocs`
============================

.. py:module:: sxdm.process.xsocs

.. autodoc2-docstring:: sxdm.process.xsocs
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`grid_qspace_xsocs <sxdm.process.xsocs.grid_qspace_xsocs>`
     - .. autodoc2-docstring:: sxdm.process.xsocs.grid_qspace_xsocs
          :summary:
   * - :py:obj:`get_qspace_vals_xsocs <sxdm.process.xsocs.get_qspace_vals_xsocs>`
     - .. autodoc2-docstring:: sxdm.process.xsocs.get_qspace_vals_xsocs
          :summary:
   * - :py:obj:`estimate_n_bins <sxdm.process.xsocs.estimate_n_bins>`
     - .. autodoc2-docstring:: sxdm.process.xsocs.estimate_n_bins
          :summary:
   * - :py:obj:`_get_motor_dict <sxdm.process.xsocs._get_motor_dict>`
     - .. autodoc2-docstring:: sxdm.process.xsocs._get_motor_dict
          :summary:
   * - :py:obj:`_shift_write_data <sxdm.process.xsocs._shift_write_data>`
     - .. autodoc2-docstring:: sxdm.process.xsocs._shift_write_data
          :summary:
   * - :py:obj:`_make_shift_master <sxdm.process.xsocs._make_shift_master>`
     - .. autodoc2-docstring:: sxdm.process.xsocs._make_shift_master
          :summary:
   * - :py:obj:`shift_xsocs_data <sxdm.process.xsocs.shift_xsocs_data>`
     - .. autodoc2-docstring:: sxdm.process.xsocs.shift_xsocs_data
          :summary:

API
~~~

.. py:function:: grid_qspace_xsocs(path_qconv, path_master, nbins, roi=None, medfilt_dims=None, offsets=None, overwrite=False, correct_mpx_gaps=True, normalizer=None, mask=None, n_proc=None, center_chan=None, chan_per_deg=None, beam_energy=None, qconv=None, sample_ip=[1, 0, 0], sample_oop=[0, 0, 1], det_ip='y+', det_oop='z-', sampleor='det', det_roi=None)
   :canonical: sxdm.process.xsocs.grid_qspace_xsocs

   .. autodoc2-docstring:: sxdm.process.xsocs.grid_qspace_xsocs

.. py:function:: get_qspace_vals_xsocs(path_master, offsets=dict(), center_chan=None, chan_per_deg=None, beam_energy=None, qconv=None, det_roi=None, sample_ip=[1, 0, 0], sample_oop=[0, 0, 1], det_ip='y+', det_oop='z-', sampleor='det')
   :canonical: sxdm.process.xsocs.get_qspace_vals_xsocs

   .. autodoc2-docstring:: sxdm.process.xsocs.get_qspace_vals_xsocs

.. py:function:: estimate_n_bins(path_master, offsets=dict(), center_chan=None, chan_per_deg=None, beam_energy=None, qconv=None, roi=None)
   :canonical: sxdm.process.xsocs.estimate_n_bins

   .. autodoc2-docstring:: sxdm.process.xsocs.estimate_n_bins

.. py:function:: _get_motor_dict(path_master, ls, motor_name='eta')
   :canonical: sxdm.process.xsocs._get_motor_dict

   .. autodoc2-docstring:: sxdm.process.xsocs._get_motor_dict

.. py:function:: _shift_write_data(path_master, shifts, n_chunks, roi, path_subh5, overwrite=False)
   :canonical: sxdm.process.xsocs._shift_write_data

   .. autodoc2-docstring:: sxdm.process.xsocs._shift_write_data

.. py:function:: _make_shift_master(path_master, path_out)
   :canonical: sxdm.process.xsocs._make_shift_master

   .. autodoc2-docstring:: sxdm.process.xsocs._make_shift_master

.. py:function:: shift_xsocs_data(path_master, path_out, shifts, subh5_list=None, n_chunks=3, roi=None, overwrite=False)
   :canonical: sxdm.process.xsocs.shift_xsocs_data

   .. autodoc2-docstring:: sxdm.process.xsocs.shift_xsocs_data
