"""Tests for DWG to DXF conversion module."""

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

    def test_dwg2dxf_success(self, tmp_path: Path):
        """Successful dwg2dxf conversion should return DXF path."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")
        expected_dxf = tmp_path / "test.dxf"

        def mock_run(cmd, **kwargs):
            # Simulate dwg2dxf creating the output file
            expected_dxf.write_text("FAKE DXF OUTPUT")
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg)

        assert result == expected_dxf
        assert result.exists()

    def test_dwg2dxf_fails_dwgread_succeeds(self, tmp_path: Path):
        """When dwg2dxf fails, should fall back to dwgread."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")
        expected_dxf = tmp_path / "test.dxf"

        call_count = 0

        def mock_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if "dwg2dxf" in cmd:
                return MagicMock(returncode=1, stderr="dwg2dxf failed")
            else:
                # dwgread succeeds
                expected_dxf.write_text("FAKE DXF FROM DWGREAD")
                return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg)

        assert call_count == 2
        assert result == expected_dxf

    def test_both_tools_fail(self, tmp_path: Path):
        """When both dwg2dxf and dwgread fail, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=1, stderr="conversion failed")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            with pytest.raises(RuntimeError, match="conversion failed"):
                convert_dwg_to_dxf(dwg)

    def test_output_file_missing_after_success(self, tmp_path: Path):
        """If tool returns 0 but no output file, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            # Returns success but doesn't create the file
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            with pytest.raises(RuntimeError, match="output file not found"):
                convert_dwg_to_dxf(dwg)

    def test_tools_not_installed(self, tmp_path: Path):
        """If LibreDWG is not installed, should raise RuntimeError about tools."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            raise FileNotFoundError("No such file or directory: 'dwg2dxf'")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            with pytest.raises(RuntimeError, match="LibreDWG tools"):
                convert_dwg_to_dxf(dwg)

    def test_conversion_timeout(self, tmp_path: Path):
        """If conversion exceeds 120s, should raise RuntimeError."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")

        def mock_run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 120)

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
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
            expected_dxf.parent.mkdir(parents=True, exist_ok=True)
            expected_dxf.write_text("FAKE DXF")
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg, out_dir)

        assert result == expected_dxf
        assert result.parent == out_dir

    def test_default_output_dir_is_input_dir(self, tmp_path: Path):
        """Without output_dir, output should be in same dir as input."""
        dwg = tmp_path / "test.dwg"
        dwg.write_text("FAKE DWG")
        expected_dxf = tmp_path / "test.dxf"

        def mock_run(cmd, **kwargs):
            expected_dxf.write_text("FAKE DXF")
            return MagicMock(returncode=0, stderr="")

        with patch("app.pipeline.dwg_converter.subprocess.run", side_effect=mock_run):
            result = convert_dwg_to_dxf(dwg)

        assert result.parent == dwg.parent
