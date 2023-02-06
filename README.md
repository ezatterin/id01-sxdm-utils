[![pipeline status](https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/badges/main/pipeline.svg)](https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/-/commits/main)

# How to run the tutorial notebooks on Jupyter-slurm

1. Go to the [Jupyter-SLURM hub](https://jupyter-slurm.esrf.fr/). 
2. Log in with the ESRF SSO.
3. Spawn an instance with 1/4 of a node (for 2D-SXDM) or the full node (for 3D-SXDM) and the desired time limit.
4. Once the instance is spawned the interface shows the contents of the user's home directory on the NICE cluster. On the right of the interface click on `New` and then `Terminal`. This opens a terminal in the same directory.
5. Clone the `sxdm` repository by pasting `git clone https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git` in the terminal. 
    * If a connection error appears, type `export no_proxy='.esrf.fr'` and try again.
6. Close the terminal.
7. Navigate to `id01-sxdm-utils/examples/`
8. Click on the notebook!

# Installation on a local machine

First install `xsocs`:

```bash
pip install --pre --find-links https://kmap.gitlab-pages.esrf.fr/xsocs/wheels/ xsocs
```

Then `id01lib`:

```bash
pip install -e git+https://gitlab.esrf.fr/id01-science/id01-core.git#egg=id01-core
```

Finally this package, `sxdm`:

```bash
pip install -e git+https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git#egg=id01-sxdm-utils
```

These steps are necessary as none of these three packages is currently available from the Python Packaging Index (PyPI), as they are not mature enough to be published.
