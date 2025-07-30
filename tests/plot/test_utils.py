"""Tests for the plotting utility functions."""

import os
import pytest
import sxdm

# Constants at module level
SAMPLE_DATASET = os.path.join(
    "doc/source/examples/data/MA1234/id01/20230710/RAW_DATA/InGaN/InGaN_0001/InGaN_0001.h5"
)


class TestGifSxdm:
    """Tests for the gif_sxdm function."""

    # note tmp_path is a pytest fixture
    def test_default_parameters(self, tmp_path):
        """Test gif_sxdm with default parameters."""
        outfile = os.path.join(tmp_path, "test_output.gif")
        sxdm.plot.utils.gif_sxdm(path_dset=SAMPLE_DATASET, outfile=outfile)
        assert os.path.exists(outfile)

    def test_specific_parameters(self, tmp_path):
        """Test gif_sxdm with custom ROI, scan numbers and visualization parameters."""
        outfile = os.path.join(tmp_path, "test_output_roi.gif")
        sxdm.plot.utils.gif_sxdm(
            path_dset=SAMPLE_DATASET,
            detector_roi="mpx1x4_roi1",
            scan_nos=[1, 2],
            outfile=outfile,
            time_between_frames=200,
            moving_motor="eta",
            norm="log",
            clims=[1, 1000],
            cmap="inferno",
        )
        assert os.path.exists(outfile)

    def test_invalid_normalization(self):
        """Test that invalid normalization raises appropriate error."""
        with pytest.raises(ValueError, match="Unknown normalisation type"):
            sxdm.plot.utils.gif_sxdm(path_dset=SAMPLE_DATASET, norm="invalid")

    def test_nonexistent_detector_roi(self):
        """Test that non-existent detector ROI raises KeyError."""
        with pytest.raises(KeyError):
            sxdm.plot.utils.gif_sxdm(
                path_dset=SAMPLE_DATASET, detector_roi="nonexistent_roi"
            )

    def test_invalid_scan_numbers(self):
        """Test that invalid scan numbers raise KeyError."""
        with pytest.raises(KeyError):
            sxdm.plot.utils.gif_sxdm(path_dset=SAMPLE_DATASET, scan_nos=[9999])
