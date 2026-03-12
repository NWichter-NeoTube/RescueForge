"""DWG to DXF conversion using ODA File Converter."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# ODA File Converter binary name (installed via .deb package)
ODA_BINARY = "ODAFileConverter"


def is_dwg_file(filepath: str | Path) -> bool:
    return Path(filepath).suffix.lower() == ".dwg"


def _find_oda_converter() -> str | None:
    """Locate the ODA File Converter binary."""
    # Check common installation paths
    for candidate in [
        ODA_BINARY,
        "/usr/bin/ODAFileConverter",
        "/opt/ODAFileConverter/ODAFileConverter",
    ]:
        if shutil.which(candidate):
            return candidate
    return None


def convert_dwg_to_dxf(dwg_path: str | Path, output_dir: str | Path | None = None) -> Path:
    """Convert a DWG file to DXF using ODA File Converter.

    ODA File Converter works on directories, so we use temp dirs
    to isolate single-file conversion.

    Args:
        dwg_path: Path to the input DWG file.
        output_dir: Directory for the output DXF. Defaults to same dir as input.

    Returns:
        Path to the generated DXF file.

    Raises:
        RuntimeError: If conversion fails.
    """
    dwg_path = Path(dwg_path)
    if not dwg_path.exists():
        raise FileNotFoundError(f"DWG file not found: {dwg_path}")

    if output_dir is None:
        output_dir = dwg_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dxf_path = output_dir / dwg_path.with_suffix(".dxf").name

    logger.info("Converting DWG to DXF: %s -> %s", dwg_path, dxf_path)

    oda_bin = _find_oda_converter()
    if not oda_bin:
        raise RuntimeError(
            "ODA File Converter not found. "
            "Ensure ODAFileConverter is installed in the Docker container."
        )

    try:
        # ODA works on directories, so isolate this single file
        with tempfile.TemporaryDirectory(prefix="oda_in_") as tmp_in, \
             tempfile.TemporaryDirectory(prefix="oda_out_") as tmp_out:

            # Copy DWG to temp input dir
            shutil.copy2(dwg_path, Path(tmp_in) / dwg_path.name)

            # ODAFileConverter <input_dir> <output_dir> <version> <type> <recurse> <audit>
            # ACAD2018 = AutoCAD 2018 DXF format, widely compatible
            result = subprocess.run(
                [oda_bin, tmp_in, tmp_out, "ACAD2018", "DXF", "0", "1"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Find the converted file
            tmp_dxf = Path(tmp_out) / dwg_path.with_suffix(".dxf").name
            if tmp_dxf.exists():
                shutil.move(str(tmp_dxf), str(dxf_path))
            elif result.returncode != 0:
                raise RuntimeError(
                    f"DWG to DXF conversion failed (exit {result.returncode}): {result.stderr}"
                )
            else:
                raise RuntimeError("Conversion completed but output file not found")

        logger.info("DWG conversion successful: %s", dxf_path)
        return dxf_path

    except FileNotFoundError:
        raise RuntimeError(
            "ODA File Converter not found. "
            "Ensure ODAFileConverter is installed in the Docker container."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("DWG conversion timed out after 120 seconds")
