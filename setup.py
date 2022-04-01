from distutils.core import setup
import setuptools

setup(
    name="id01-sxdm-utils",
    version="0.1.0",
    author="E. Zatterin",
    author_email="edoardo.zatterin@esrf.fr",
    packages=["sxdm", "sxdm.bliss"],
    license="LICENSE.txt",
    description="Code to treat Scanning X-ray Diffraction Microscopy data\
         collected on beamline ID01 at ESRF",
    long_description=open("README.md").read(),
    install_requires=[
        "numpy",
        "matplotlib",
        "ipywidgets",
        "tqdm",
        "silx",
        "pandas",
        "xrayutilities",
        "ipympl==0.7.0" # xsocs, id01lib
    ],
)

if __name__ == "main":
    setuptools.setup()