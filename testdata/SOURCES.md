# Test Data Sources

All test files are real architectural floor plans. This file documents the origin of each file.

**Source:** Files 1-2 from open GitHub repositories, files 3-10 from [DWGShare.com](https://dwgshare.com/) as recommended in the Siemens Hackathon 2025 challenge description.

## DXF Files

### 1. floorplan_sample.dxf (1.1 MB)
- **Description**: Multi-room building floor plan with walls, doors, rooms, stairs
- **Pipeline result**: 248 walls, 173 doors, 16 rooms detected, 15 classified
- **Source**: [jscad/sample-files](https://github.com/jscad/sample-files) on GitHub
- **License**: Public sample file

### 2. basement_plan.dxf (173 KB)
- **Description**: Basement floor plan layout
- **Pipeline result**: 149 walls, 8 rooms detected, 5 classified
- **Source**: [runlevel-6/runlevel-6.github.io](https://github.com/runlevel-6/runlevel-6.github.io)
- **License**: Public (blog post example)

## DWG Files (from DWGShare.com)

### 3. apartment_highrise_61.dwg (456 KB)
- **Description**: Typical apartment floor plan for levels 14-23 of a residential high-rise
- **Pipeline result**: 295 walls, 2 rooms detected & classified
- **Source**: [DWGShare.com #61](https://dwgshare.com/61-free-cad-download-typical-apartment-floor-plan-levels-14-23-residential-building-dwg/)
- **License**: Free download, DWGShare.com

### 4. apartment_typical_119.dwg (221 KB)
- **Description**: Apartment building typical floor plan (1,400 m2)
- **Pipeline result**: 4099 walls, 61 doors, 126 rooms detected & classified
- **Source**: [DWGShare.com #119](https://dwgshare.com/119-apartment-typical-floor-plan-cad-drawings-free-download/)
- **License**: Free download, DWGShare.com

### 5. dormitory_104.dwg (303 KB)
- **Description**: Ground floor plan of a dormitory building for factory staff
- **Pipeline result**: 3443 walls, 40 doors, 200 rooms detected & classified
- **Source**: [DWGShare.com #104](https://dwgshare.com/104-free-download-cad-floor-plan-layout-of-dormitory-for-factory-staff/)
- **License**: Free download, DWGShare.com

### 6. family_home_360m2_433.dwg (508 KB)
- **Description**: Two-story family home, 360 square meters
- **Pipeline result**: 5180 walls, 24 doors, 93 rooms detected & classified
- **Source**: [DWGShare.com #433](https://dwgshare.com/433-free-cad-drawings-two-story-family-home-360-square-meters/)
- **License**: Free download, DWGShare.com

### 7. hospital_65000m2_55.dwg (774 KB)
- **Description**: First floor plan of a 65,000 m2 hospital building
- **Pipeline result**: 4222 walls, 161 doors, 85 rooms detected & classified
- **Source**: [DWGShare.com #55](https://dwgshare.com/55-free-cad-download-first-floor-plan-of-a-65000-m2-hospital/)
- **License**: Free download, DWGShare.com

### 8. kindergarten_31.dwg (1.9 MB)
- **Description**: Complete kindergarten floor plan drawings
- **Pipeline result**: 4805 walls, 146 doors, 24 rooms detected, 15 classified
- **Source**: [DWGShare.com #31](https://dwgshare.com/31-free-cad-download-kindergarten-floor-plan/)
- **License**: Free download, DWGShare.com

### 9. office_12story_64.dwg (585 KB)
- **Description**: Layout floor plans of a 12-story office building
- **Pipeline result**: 5491 walls, 107 doors, 196 rooms detected & classified
- **Source**: [DWGShare.com #64](https://dwgshare.com/64-download-free-layout-floor-plans-of-a-12-story-office-building/)
- **License**: Free download, DWGShare.com

### 10. office_3story_900m2_84.dwg (541 KB)
- **Description**: Floor plans and elevations of a 3-storey office building (900 m2)
- **Pipeline result**: 1908 walls, 288 rooms detected & classified
- **Source**: [DWGShare.com #84](https://dwgshare.com/84-free-download-floor-plans-and-elevations-of-a-3-storey-office-building-with-a-total-area-of-900-m2/)
- **License**: Free download, DWGShare.com

## Pipeline Test Summary

| # | File | Walls | Doors | Rooms | Pipeline Time |
|---|------|-------|-------|-------|---------------|
| 1 | floorplan_sample.dxf | 248 | 173 | 16/15 | ~6s |
| 2 | basement_plan.dxf | 149 | 0 | 8/5 | ~4s |
| 3 | apartment_highrise_61.dwg | 295 | 0 | 2/2 | ~4s |
| 4 | apartment_typical_119.dwg | 4099 | 61 | 126/126 | ~5s |
| 5 | dormitory_104.dwg | 3443 | 40 | 200/200 | ~6s |
| 6 | family_home_360m2_433.dwg | 5180 | 24 | 93/93 | ~7s |
| 7 | hospital_65000m2_55.dwg | 4222 | 161 | 85/85 | ~7s |
| 8 | kindergarten_31.dwg | 4805 | 146 | 24/15 | ~17s |
| 9 | office_12story_64.dwg | 5491 | 107 | 196/196 | ~9s |
| 10 | office_3story_900m2_84.dwg | 1908 | 0 | 288/288 | ~5s |

All 10 files processed successfully (10/10).

### Detection Methods
- **Doors**: Layer name matching + INSERT block geometry analysis + arc swing detection (80-150°)
- **Rooms**: Shapely polygonize with gap-closing + area filtering
- **Classification**: Gemini 2.5 Flash Vision API (≤80 rooms) or heuristic fallback (>80 rooms)
