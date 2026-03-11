"""DWG to DXF conversion using LibreDWG (dwg2dxf command)."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def is_dwg_file(filepath: str | Path) -> bool:
    return Path(filepath).suffix.lower() == ".dwg"


def convert_dwg_to_dxf(dwg_path: str | Path, output_dir: str | Path | None = None) -> Path:
    """Convert a DWG file to DXF using LibreDWG's dwg2dxf tool.

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

    try:
        result = subprocess.run(
            ["dwg2dxf", "-o", str(dxf_path), str(dwg_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            # Try alternative: dwgread with DXF output
            result = subprocess.run(
                ["dwgread", "-O", "DXF", "-o", str(dxf_path), str(dwg_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )

        if result.returncode != 0:
            raise RuntimeError(
                f"DWG to DXF conversion failed (exit {result.returncode}): {result.stderr}"
            )

        if not dxf_path.exists():
            raise RuntimeError("Conversion completed but output file not found")

        logger.info("DWG conversion successful: %s", dxf_path)
        return dxf_path

    except FileNotFoundError:
        raise RuntimeError(
            "LibreDWG tools (dwg2dxf) not found. "
            "Ensure libredwg-tools is installed in the Docker container."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("DWG conversion timed out after 120 seconds")
