"""Tests for DWG to DXF conversion module (ODA File Converter)."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.dwg_converter import convert_dwg_to_dxf, is_dwg_file


class TestIsDwgFile:
    def test_dwg_lowercase(self):
        assert is_dwg_file("plan.dwg") is True

    def test_dwg_uppercase(self):
        assert is_dwg_file("PLAN.DWG") is True

    def test_dwg_mixed_case(self):
        assert is_dwg_file("Plan.Dwg") is True

    def test_dxf_not_dwg(self):
        assert is_dwg_file("plan.dxf") is False

    def test_svg_not_dwg(self):
        assert is_dwg_file("plan.svg") is False

    def test_path_object(self):
        assert is_dwg_file(Path("/some/path/plan.dwg")) is True

    def test_no_extension(self):
        assert is_dwg_file("planfile") is False


class TestConvertDwgToDxf:
    def test_nonexistent_file_raises(self):
        """Non-existent DWG file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="not found"):
            convert_dwg_to_dxf("/nonexistent/plan.dwg")

    def test_oda_converter_success(self, tmp_path: Path):
        """Successful ODA conversion should return DXF path."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            # ODA writes to the output dir (2nd arg)
            out_dir = Path(cmd[2])
            (out_dir / "test.dxf").write_text("FAKE DXF OUTPUT")
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value="ODAFileConverter"), \
             patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg)

        assert result == tmp_path / "test.dxf"
        assert result.exists()

    def test_oda_converter_fails(self, tmp_path: Path):
        """When ODA converter fails, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=1, stderr="conversion failed")

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value="ODAFileConverter"), \
             patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            with pytest.raises(RuntimeError, match="conversion failed"):
                convert_dwg_to_dxf(dwg)

    def test_output_file_missing_after_success(self, tmp_path: Path):
        """If tool returns 0 but no output file, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            # Returns success but doesn't create the file
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value="ODAFileConverter"), \
             patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            with pytest.raises(RuntimeError, match="output file not found"):
                convert_dwg_to_dxf(dwg)

    def test_converter_not_installed(self, tmp_path: Path):
        """If ODA converter is not installed, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value=None):
            with pytest.raises(RuntimeError, match="ODA File Converter not found"):
                convert_dwg_to_dxf(dwg)

    def test_conversion_timeout(self, tmp_path: Path):
        """If conversion exceeds 120s, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 120)

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value="ODAFileConverter"), \
             patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            with pytest.raises(RuntimeError, match="timed out"):
                convert_dwg_to_dxf(dwg)

    def test_custom_output_dir(self, tmp_path: Path):
        """Should write output to specified output directory."""
        dwg = tmp_path / "input" / "test.dwg"
        dwg.parent.mkdir()
        dwg.write_text("FAKE DWG")
        out_dir = tmp_path / "output"

        expected_dxf = out_dir / "test.dxf"

        def mock_run(cmd, **kwargs):
            oda_out = Path(cmd[2])
            (oda_out / "test.dxf").write_text("FAKE DXF")
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value="ODAFileConverter"), \
             patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg, out_dir)

        assert result == expected_dxf
        assert result.parent == out_dir

    def test_default_output_dir_is_input_dir(self, tmp_path: Path):
        """Without output_dir, output should be in same dir as input."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            oda_out = Path(cmd[2])
            (oda_out / "test.dxf").write_text("FAKE DXF")
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter._find_oda_converter", return_value="ODAFileConverter"), \
             patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg)

        assert result.parent == dwg.parent
