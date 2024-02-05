from distutils.core import setup
import setuptools

setup(
    name="id01-sxdm-utils",
    version="0.1.0",
    author="E. Zatterin",
    author_email="edoardo.zatterin@esrf.fr",
    packages=[
        "sxdm",
        "sxdm.plot",
        "sxdm.io",
        "sxdm.process",
        "sxdm.utils",
        "sxdm.widgets",
        "sxdm.widgets.bliss",
    ],
    license="LICENSE.txt",
    description="Code to treat Scanning X-ray Diffraction Microscopy data\
         collected on beamline ID01 at ESRF",
    long_description=open("README.md").read(),
    install_requires=[
        "numpy",
        "matplotlib",
        "ipywidgets",
        "gif",
        "tqdm",
        "silx>=1.0.0",
        "pandas",
        "xrayutilities",
        "ipympl", 
        "scikit-image",
        "hdf5plugin" # xsocs, id01lib
    ],
)

if __name__ == "main":
    setuptools.setup()
