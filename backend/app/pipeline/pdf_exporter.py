"""PDF export using WeasyPrint - converts SVG orientation plans to printable PDFs."""

import logging
from pathlib import Path

from weasyprint import HTML

logger = logging.getLogger(__name__)


class PDFExportError(Exception):
    """Raised when PDF export fails."""


def export_pdf(
    svg_path: str | Path,
    output_path: str | Path,
    paper_format: str = "A3",
) -> Path:
    """Convert an SVG orientation plan to a PDF.

    Wraps the SVG in an HTML page and uses WeasyPrint to produce a
    standards-compliant PDF suitable for printing.

    Args:
        svg_path: Path to the input SVG file.
        output_path: Path for the output PDF file.
        paper_format: "A3" or "A4".

    Returns:
        Path to the generated PDF file.

    Raises:
        PDFExportError: If the SVG file is missing or WeasyPrint fails.
    """
    svg_path = Path(svg_path)
    output_path = Path(output_path)

    if not svg_path.exists():
        raise PDFExportError(f"SVG file not found: {svg_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        svg_content = svg_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PDFExportError(f"Failed to read SVG file: {exc}") from exc

    if not svg_content.strip():
        raise PDFExportError(f"SVG file is empty: {svg_path}")

    if paper_format == "A3":
        page_size = "420mm 297mm"
    else:
        page_size = "297mm 210mm"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<style>
    @page {{
        size: {page_size};
        margin: 0;
    }}
    body {{
        margin: 0;
        padding: 0;
    }}
    svg {{
        width: 100%;
        height: 100%;
    }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""

    logger.info("Exporting PDF: %s -> %s", svg_path, output_path)

    try:
        html = HTML(string=html_content, base_url=str(svg_path.parent))
        html.write_pdf(str(output_path))
    except Exception as exc:
        # Clean up partial output
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        raise PDFExportError(f"WeasyPrint failed: {exc}") from exc

    if not output_path.exists():
        raise PDFExportError("PDF file was not created")

    file_size = output_path.stat().st_size
    if file_size == 0:
        output_path.unlink()
        raise PDFExportError("PDF file is empty (0 bytes)")

    logger.info("PDF exported: %s (%d bytes)", output_path, file_size)
    return output_path
