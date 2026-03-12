# Open Source Tools Research

## Tech Stack (gewählt)

| Kategorie | Tool | Grund |
|---|---|---|
| Package Manager | **uv** | Schnell, lockfile, Docker-optimiert |
| Web Framework | **FastAPI** | Async, auto-docs, file upload |
| DXF Parsing | **ezdxf** (~900 stars, MIT) | Mature, full DXF R12-R2018 support |
| DWG -> DXF | **LibreDWG** (~900 stars, GPL) | Einziger open-source DWG reader |
| 2D Geometry | **Shapely** (~4.4k stars, BSD) | polygonize(), union, containment |
| AI Classification | **OpenRouter** Vision API | GPT-4o/Claude für Raumklassifikation |
| SVG Output | **svgwrite** (MIT) | Stabil, keine Dependencies |
| PDF Export | **WeasyPrint** (~7k stars, BSD) | HTML/CSS -> PDF |
| Task Queue | **Celery + Redis** | Background processing |
| Frontend | **Next.js 15** | React, SSR, TypeScript |
| UI | **Tailwind CSS** | Utility-first CSS |
| SVG Viewer | **react-zoom-pan-pinch** | Pan/Zoom im Browser |

## Alternativen (evaluiert)

### DXF/DWG Parsing
- **dxf-parser** (JS): Veraltet (4 Jahre), weniger Features
- **libredwg-web** (WASM): Browser-DWG, aber unreif

### Geometry
- **OpenCV**: Raster-basiert, verliert Vektorpräzision
- **scikit-image**: Gut für Bildanalyse, aber raster-only

### Room Detection
- **CubiCasa5k**: Grösstes Dataset, aber restriktive Lizenz
- **FloorplanTransformation** (ICCV 2017): Raster-to-Vector, älter
- **DeepFloorPlan**: Guter ML-Ansatz, aber pre-trained weights rar

### PDF Generation
- **ReportLab**: Mächtiger, aber komplexer
- **CairoSVG**: SVG->PDF, LGPL Lizenz

## Architektur-Entscheide

1. **Vektor-first Ansatz**: DXF Entities direkt via ezdxf+Shapely verarbeiten,
   nicht via Bild-Umweg. Präziser und schneller.

2. **Vision API für Klassifikation**: Statt eigenes ML-Modell zu trainieren,
   rendern wir den Plan als Bild und lassen GPT-4o/Claude die Räume
   klassifizieren. Einfacher, flexibler, keine Trainingsdaten nötig.

3. **Heuristik-Fallback**: Wenn AI nicht verfügbar, geometrische Heuristiken
   (Seitenverhältnis, Fläche, Position) für grundlegende Klassifikation.
