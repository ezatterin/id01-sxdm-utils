:py:mod:`sxdm.utils.bliss`
==========================

.. py:module:: sxdm.utils.bliss

.. autodoc2-docstring:: sxdm.utils.bliss
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`get_SXDM_info <sxdm.utils.bliss.get_SXDM_info>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.get_SXDM_info
          :summary:
   * - :py:obj:`parse_scan_command <sxdm.utils.bliss.parse_scan_command>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.parse_scan_command
          :summary:
   * - :py:obj:`make_xsocs_links <sxdm.utils.bliss.make_xsocs_links>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.make_xsocs_links
          :summary:
   * - :py:obj:`make_xsocs_links_stitch <sxdm.utils.bliss.make_xsocs_links_stitch>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.make_xsocs_links_stitch
          :summary:
   * - :py:obj:`get_qspace_proj <sxdm.utils.bliss.get_qspace_proj>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.get_qspace_proj
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`__all__ <sxdm.utils.bliss.__all__>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.__all__
          :summary:
   * - :py:obj:`ScanRange <sxdm.utils.bliss.ScanRange>`
     - .. autodoc2-docstring:: sxdm.utils.bliss.ScanRange
          :summary:

API
~~~

.. py:data:: __all__
   :canonical: sxdm.utils.bliss.__all__
   :value: ['get_SXDM_info', 'parse_scan_command', 'make_xsocs_links']

   .. autodoc2-docstring:: sxdm.utils.bliss.__all__

.. py:data:: ScanRange
   :canonical: sxdm.utils.bliss.ScanRange
   :value: 'namedtuple(...)'

   .. autodoc2-docstring:: sxdm.utils.bliss.ScanRange

.. py:function:: get_SXDM_info(path_dset, scan_range=(1, None))
   :canonical: sxdm.utils.bliss.get_SXDM_info

   .. autodoc2-docstring:: sxdm.utils.bliss.get_SXDM_info

.. py:function:: parse_scan_command(command)
   :canonical: sxdm.utils.bliss.parse_scan_command

   .. autodoc2-docstring:: sxdm.utils.bliss.parse_scan_command

.. py:function:: make_xsocs_links(path_dset, path_out, scan_nums=None, detector=None, name_outh5=None, stitch_counter=None)
   :canonical: sxdm.utils.bliss.make_xsocs_links

   .. autodoc2-docstring:: sxdm.utils.bliss.make_xsocs_links

.. py:function:: make_xsocs_links_stitch(dset_path_list, scan_nums_list, path_out, name_outh5, detector=None)
   :canonical: sxdm.utils.bliss.make_xsocs_links_stitch

   .. autodoc2-docstring:: sxdm.utils.bliss.make_xsocs_links_stitch

.. py:function:: get_qspace_proj(path_qspace, dir_idx, rec_ax, qspace_roi=None, bin_norm=False)
   :canonical: sxdm.utils.bliss.get_qspace_proj

   .. autodoc2-docstring:: sxdm.utils.bliss.get_qspace_proj
