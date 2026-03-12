# Testdaten-Quellen

## DWGShare.com (Primär)
Kostenlose CAD-Pläne in DWG-Format. Kein Login nötig.

### Empfohlene Testfälle

| # | Gebäudetyp | Link | Format |
|---|---|---|---|
| 1 | Apartment (Residential) | https://dwgshare.com/119-apartment-typical-floor-plan-cad-drawings-free-download/ | DWG |
| 2 | Multi-Storey Apartment | https://dwgshare.com/118-multi-storey-apartment-building-cad-floor-plans-free-download/ | DWG |
| 3 | 12-Story Office Building | https://dwgshare.com/64-download-free-layout-floor-plans-of-a-12-story-office-building/ | DWG, 498 KB |
| 4 | 2-Storey Office | https://dwgshare.com/105-free-download-floor-plan-and-elevation-drawings-of-a-2-storey-office-building/ | DWG |
| 5 | Large Commercial | https://dwgshare.com/44-free-download-cad-drawing-large-commercial-building-ground-floor-second-floor-plan/ | DWG |
| 6 | Factory 154x275m | https://dwgshare.com/53-free-download-of-cad-floor-plan-drawings-for-a-factory-with-dimensions-154m-x-275m/ | DWG, 1.45 MB |
| 7 | Industrial Plant | https://dwgshare.com/36-autocad-drawing-of-industrial-plant-ground-floor-plan-layout-for-download/ | DWG, 2.81 MB |
| 8 | 5-Star Hotel | https://dwgshare.com/97-free-download-5-star-hotel-full-cad-drawings-floor-plans-sections-elevations/ | DWG |
| 9 | 10-Story Hotel | https://dwgshare.com/99-free-download-of-10-story-hotel-design-drawings/ | DWG |
| 10 | School Building | https://dwgshare.com/9-full-3-storey-school-building-project-autocad-free-download/ | DWG |
| 11 | Shopping Mall | https://dwgshare.com/17-shopping-mall-plan-autocad-file-free-download/ | DWG |

## Akademische Datasets

### FloorPlanCAD (15K Pläne, SVG)
- **Beschreibung:** 15'000+ reale CAD-Grundrisse, 30 Objektkategorien
- **Format:** SVG (aus DWG konvertiert)
- **Lizenz:** CC BY-NC 4.0
- **Links:** https://floorplancad.github.io/ | https://huggingface.co/datasets/Voxel51/FloorPlanCAD

### ArchCAD-400K (Neuestes, Grösstes - 2025)
- **Beschreibung:** 5'538 Zeichnungen, 413'062 annotierte Abschnitte
- **Format:** Multi-modal (Raster, SVG, JSON)
- **Links:** https://huggingface.co/datasets/jackluoluo/ArchCAD

### CubiCasa5K
- **Beschreibung:** 5'000 Grundrisse, 80+ Kategorien
- **Format:** Bilder + SVG Annotationen
- **Links:** https://github.com/CubiCasa/CubiCasa5k

### CVC-FP
- **Beschreibung:** 122 gescannte Grundrisse
- **Format:** Rasterbilder + SVG Groundtruth
- **Links:** https://dag.cvc.uab.es/dataset/cvc-fp-database-for-structural-floor-plan-analysis/

### MLSTRUCT-FP
- **Beschreibung:** 954 hochauflösende Grundrisse mit Wand-Annotationen
- **Format:** PNG + JSON
- **Links:** https://github.com/MLSTRUCT/MLSTRUCT-FP

## GitHub DXF Samples
- **jscad/sample-files:** Einzelne DXF-Grundrisse
  https://github.com/jscad/sample-files/blob/master/dxf/dxf-parser/floorplan.dxf
- **GSStnb/dxfBlocks:** CAD-Blöcke für LibreCAD
  https://github.com/GSStnb/dxfBlocks

## Weitere CAD-Download-Seiten
- FreeCADS: https://www.freecads.com/
- Bibliocad: https://www.bibliocad.com/
- DWGModels: https://dwgmodels.com/
- FreeCadFloorPlans: https://freecadfloorplans.com/

## Empfehlung

Für den Hackathon-Prototyp:
1. **5-10 DWG von DWGShare.com** manuell herunterladen und mit ODA File Converter -> DXF konvertieren
2. **1 DXF von jscad/sample-files** als schneller Minimaltestfall
3. **FloorPlanCAD SVGs** für Batch-Tests der Raumklassifikation (später)
