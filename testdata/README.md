# Test Data

10 real architectural floor plans (2 DXF + 8 DWG). Files are not stored in the repository (too large).

## Quick Start

DXF files from GitHub:

```bash
# Basement floor plan (~173KB)
curl -o testdata/basement_plan.dxf https://raw.githubusercontent.com/runlevel-6/runlevel-6.github.io/master/download/basement_plan.dxf
```

## DWG Files from DWGShare.com

8 DWG files are downloaded from [DWGShare.com](https://dwgshare.com/), as recommended in the Siemens Hackathon 2025 challenge description. Download manually from the links in [SOURCES.md](SOURCES.md).

Supported formats:
- `testdata/*.dwg` (auto-converted to DXF via ODA File Converter)
- `testdata/*.dxf`

## Sources

See [SOURCES.md](SOURCES.md) for all file origins, licenses, and pipeline test results.
