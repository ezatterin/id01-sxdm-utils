:py:mod:`sxdm.io.spec`
======================

.. py:module:: sxdm.io.spec

.. autodoc2-docstring:: sxdm.io.spec
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`FastSpecFile <sxdm.io.spec.FastSpecFile>`
     - .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile
          :summary:
   * - :py:obj:`PiezoScan <sxdm.io.spec.PiezoScan>`
     - .. autodoc2-docstring:: sxdm.io.spec.PiezoScan
          :summary:

API
~~~

.. py:class:: FastSpecFile(filename)
   :canonical: sxdm.io.spec.FastSpecFile

   Bases: :py:obj:`silx.io.specfile.SpecFile`

   .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile.__init__

   .. py:method:: __getitem__(key)
      :canonical: sxdm.io.spec.FastSpecFile.__getitem__

      .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile.__getitem__

.. py:class:: PiezoScan(fast_specfile, scan_number)
   :canonical: sxdm.io.spec.PiezoScan

   Bases: :py:obj:`silx.io.specfile.Scan`

   .. autodoc2-docstring:: sxdm.io.spec.PiezoScan

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.__init__

   .. py:method:: calc_qspace_coordinates(cen_pix=None, detector_distance=None, energy=None, detector='maxipix', ipdir=(1, 0, 0), ndir=(0, 0, 1), ignore_mpx_motors=True)
      :canonical: sxdm.io.spec.PiezoScan.calc_qspace_coordinates

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.calc_qspace_coordinates

   .. py:method:: calc_coms(roi=None, qspace=False, calc_std=False)
      :canonical: sxdm.io.spec.PiezoScan.calc_coms

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.calc_coms
