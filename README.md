# Installation

First install `xsocs`:

```bash
pip install --pre --find-links https://kmap.gitlab-pages.esrf.fr/xsocs/wheels/ xsocs
```

Then `id01lib`:

```bash
pip install -e git+https://gitlab.esrf.fr/id01-science/id01-core.git#egg=id01lib
```

Finally this package, `sxdm`:

```bash
pip install -e git+https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git#egg=sxdm
```

These steps are necessary as none of these three packages is currently available from the Python Packaging Index (PyPI), as they are not mature enough to be published.