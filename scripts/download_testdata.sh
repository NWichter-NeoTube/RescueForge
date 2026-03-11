#!/bin/bash
# Download sample test data for RescueForge development

TESTDATA_DIR="$(dirname "$0")/../testdata"
mkdir -p "$TESTDATA_DIR"

echo "=== RescueForge Test Data Download ==="

# 1. Minimal DXF from GitHub (always works)
echo ""
echo "[1/2] Downloading sample DXF from GitHub..."
curl -sL -o "$TESTDATA_DIR/floorplan_sample.dxf" \
  "https://raw.githubusercontent.com/jscad/sample-files/master/dxf/dxf-parser/floorplan.dxf"

if [ -f "$TESTDATA_DIR/floorplan_sample.dxf" ]; then
  echo "  OK: floorplan_sample.dxf"
else
  echo "  FAILED: Could not download sample DXF"
fi

# 2. Info about manual DWG downloads
echo ""
echo "[2/2] DWG files must be downloaded manually from DWGShare.com"
echo "  See: docs/test-data-sources.md for links"
echo ""
echo "  Recommended test files:"
echo "  - Office building: https://dwgshare.com/64-download-free-layout-floor-plans-of-a-12-story-office-building/"
echo "  - Factory: https://dwgshare.com/53-free-download-of-cad-floor-plan-drawings-for-a-factory-with-dimensions-154m-x-275m/"
echo "  - Hotel: https://dwgshare.com/97-free-download-5-star-hotel-full-cad-drawings-floor-plans-sections-elevations/"
echo ""
echo "  Place downloaded .dwg files in: $TESTDATA_DIR/"

echo ""
echo "=== Done ==="
ls -la "$TESTDATA_DIR/" 2>/dev/null
