# RescueForge

> AI-powered tool that transforms CAD building plans (DWG/DXF) into DIN 14095 / FKS-compliant fire department orientation plans with automatic scale detection, fire safety element recognition, corridor-centerline escape routes, and multi-language support.

**Siemens Hackathon 2025 | Track: Industrial AI** &middot; v0.5.0

[English](#what-it-does) | [Deutsch](#deutsch)

---

## What it does

1. **Upload** a DWG or DXF building plan (single or batch)
2. **Automatic cleanup** — removes irrelevant details (furniture, dimensions, annotations)
3. **Wall extraction** — detects walls, doors, fire walls, fire doors, windows, stairs, and sprinkler systems
4. **Unit auto-detection** — corrects incorrectly declared DXF units (e.g. mm vs inches) using building-size heuristics
5. **Room detection** — generates room polygons from closed wall structures using computational geometry (Shapely + STRtree)
6. **Room classification** — AI-powered classification (16 room types) via OpenRouter Vision API with retry logic and heuristic fallback
7. **DIN 14095 Plan-Set** — generates floor plan, cover sheet, situation plan, and compliance report as SVG + PDF + DOCX
8. **Corridor-centerline escape routes** — Voronoi-based medial axis extraction with NetworkX graph routing through corridor geometry
9. **Symbol collision avoidance** — automatic placement adjustments preventing overlapping symbols in small rooms

## Hackathon Deliverables

| Deliverable | Status |
|-------------|--------|
| Working prototype (Docker Compose) | Done |
| AI-powered room classification (Vision API) | Done |
| DIN 14095 / FKS-compliant plan output (SVG + PDF) | Done |
| Cover sheet + situation plan + compliance report | Done |
| Interactive room editor (reclassify & regenerate) | Done |
| Batch upload (multi-floor processing) | Done |
| WebSocket real-time progress | Done |
| 340 automated tests (19 suites) | Done |
| CI/CD pipeline (GitHub Actions) | Done |
| 13-slide presentation (PPTX) | Done |
| AutoCAD plugin concept (Web-first architecture) | Done |
| Multi-language support (EN/DE) | Done |
| DIN-standard scale detection (1:50 – 1:1000) | Done |
| Fire safety element recognition (walls, doors, sprinklers) | Done |
| Corridor-centerline escape routes (Voronoi + NetworkX) | Done |
| Symbol collision avoidance | Done |
| Pixel-based visual regression testing (CairoSVG) | Done |
| Real-world DXF compatibility testing | Done |

## Architecture

```
Frontend (Next.js 15)  -->  Backend (FastAPI)  -->  Celery Worker
     ^                        ^                      |
     '-- WebSocket status ----'              Redis (task queue)
```

### Pipeline stages (10 steps)

```
DWG -> [LibreDWG] -> DXF
    -> [ezdxf] -> Entities (walls, doors, fire walls, fire doors, windows, sprinklers)
    -> [Unit Detection] -> Auto-correct declared units via building-size heuristic
    -> [Shapely + STRtree] -> Room polygons
    -> [OpenRouter Vision] -> Classified rooms (16 types)
    -> [Voronoi + NetworkX] -> Corridor-centerline escape routes
    -> [svgwrite + SymbolPlacer] -> DIN 14095 SVG (collision-free symbols, RAL colors, 10m grid)
    -> [WeasyPrint] -> PDF
    -> [Supplementary] -> Cover Sheet + Situation Plan + Compliance Report (DOCX)
```

### Key Algorithms

| Algorithm | Purpose | Implementation |
|-----------|---------|---------------|
| Unit auto-detection | Correct wrong $INSUNITS headers | Try all unit conversions, pick one giving 5–500m building size |
| DIN scale snapping | Standard architectural scales | Snap to nearest of 1:50, 1:100, 1:200, 1:250, 1:500, 1:1000 |
| Wall-gap door detection | Find doors as gaps between wall endpoints | Spatial bucketing + collinearity/perpendicularity checks |
| Door deduplication | Merge arc + layer + INSERT detections | Sort by position, merge within tolerance, prefer standard widths |
| Voronoi medial axis | Corridor centerline extraction | scipy.spatial.Voronoi on boundary points, filter ridges inside polygon |
| NetworkX corridor routing | Escape routes along corridors | Weighted graph through corridor centerlines + room adjacency |
| BFS escape routes | Shortest paths to exits | Room adjacency graph, fallback chain: stairwell → lobby → corridor |
| Symbol collision avoidance | Prevent overlapping symbols | AABB overlap detection with 4-direction shift, label-aware placement |
| Edge-based symbol placement | Professional symbol positioning | Place symbols near room edges instead of fixed centroid offsets |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, Celery |
| Frontend | Next.js 15, React 19, Tailwind CSS, lucide-react |
| i18n | Built-in EN/DE toggle (German default, localStorage persisted) |
| CAD Parsing | ezdxf, LibreDWG |
| Geometry | Shapely (STRtree), NumPy, SciPy (Voronoi) |
| Graph Routing | NetworkX (corridor centerline escape routes) |
| AI Classification | OpenRouter (Gemini 2.5 Flash) with retry + heuristic fallback |
| SVG Generation | svgwrite |
| PDF Export | WeasyPrint |
| Task Queue | Celery + Redis |
| Security | SecurityHeadersMiddleware, RateLimitMiddleware, CSP, input validation |
| Package Manager | uv |
| Infrastructure | Docker Compose (non-root containers) |
| CI/CD | GitHub Actions (lint, test, Docker build) |
| Testing | pytest (340 backend tests, 19 suites), Cypress E2E |
| Visual Regression | CairoSVG pixel-based + JSON structural fingerprints |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenRouter API Key ([openrouter.ai](https://openrouter.ai))

### Setup

```bash
# Clone
git clone https://github.com/your-org/rescueforge.git
cd rescueforge

# Configure
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Build & Run (development)
docker compose up --build

# Build & Run (production)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Check assigned ports
docker compose ps
```

The frontend is available on port 3000. The backend uses an internal dynamic port — the frontend proxies all `/api/*` requests via Next.js rewrites, so no direct backend access is required.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for vision model | required |
| `OPENROUTER_MODEL` | AI model to use | `google/gemini-2.5-flash` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `MAX_UPLOAD_SIZE_MB` | Max upload file size | `50` |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins | `*` |
| `BACKEND_URL` | Internal backend URL for Next.js proxy | `http://backend:8000` |

## Features

### Core Pipeline
- **DWG/DXF parsing** with ezdxf (multilingual layer support: EN/DE/FR/ES/VI)
- **Unit auto-detection** — corrects wrongly declared $INSUNITS (mm, cm, m, in, ft)
- **Fire safety recognition** — fire walls (Brandwand), fire doors (T30/T60/T90), sprinkler systems, windows
- **Door detection** — arc-based + layer-based + INSERT block + wall-gap detection with deduplication
- **Room detection** via Shapely computational geometry with STRtree spatial indexing
- **AI classification** using OpenRouter Vision API (Gemini 2.5 Flash) with automatic retry (up to 3 attempts) and heuristic fallback
- **DIN 14095 SVG** output with filled walls, RAL colors, 10m reference grid, DIN title block
- **DIN scale** — auto-computed standard architectural scale (1:50 – 1:1000)
- **Escape routes** — corridor-centerline routing via Voronoi medial axis + NetworkX, with BFS fallback chain (stairwell → lobby → corridor)
- **Symbol collision avoidance** — automatic placement adjustments preventing overlapping symbols in small rooms
- **PDF export** via WeasyPrint
- **Compliance report** — DOCX document listing DIN compliance status and manual input requirements

### DIN 14095 / FKS Symbols (18 total)
- North arrow, scale bar, floor section indicator
- Smoke detectors, manual call points
- Fire access arrows, sprinkler access arrows
- Key depot (Schlüsseldepot), fire alarm panel (BMA/BMZ)
- Gas / water / electricity shutoff symbols
- Stair direction arrows, elevator symbols
- Wall hydrant, RWA (smoke extraction), assembly point
- Erstinformationsstelle (first information point, DIN 14034-6 2024)
- Complete legend auto-generated from detected room types

### Frontend
- **Real-time progress** via WebSocket (auto-fallback to HTTP polling)
- **Interactive room editor** — reclassify rooms and regenerate plan
- **Comparison view** — side-by-side original DXF vs. FKS plan
- **Batch upload** for multi-floor processing
- **Keyboard shortcuts** — Ctrl+S (SVG download), Ctrl+P (PDF download)
- **Loading skeleton** — animated placeholder during plan generation
- **Dark mode** toggle
- **EN/DE language** toggle
- **Mobile responsive** design

### Security & Reliability
- **SecurityHeadersMiddleware** — X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy
- **RateLimitMiddleware** — configurable request rate limiting
- **Celery task timeouts** — hard limit 600s, soft limit 550s, acks_late
- **Error persistence** — detailed error.json on pipeline failure (step, elapsed time, error type)
- **Input validation** — room type enum validation, job ID format checks
- **Non-root Docker containers** — production-hardened images

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (version, status) |
| `POST` | `/api/upload` | Upload single DWG/DXF file |
| `POST` | `/api/upload/batch` | Batch upload (max 10 files) |
| `GET` | `/api/jobs/{job_id}` | Get processing status |
| `GET` | `/api/jobs/{job_id}/svg` | Download FKS orientation plan (SVG) |
| `GET` | `/api/jobs/{job_id}/pdf` | Download FKS orientation plan (PDF) |
| `GET` | `/api/jobs/{job_id}/cover-sheet` | Download cover sheet |
| `GET` | `/api/jobs/{job_id}/situation-plan` | Download situation plan |
| `GET` | `/api/jobs/{job_id}/original-svg` | Raw DXF preview (before FKS processing) |
| `GET` | `/api/jobs/{job_id}/data` | Floor plan data as JSON |
| `GET` | `/api/jobs/{job_id}/metrics` | Pipeline performance metrics |
| `GET` | `/api/jobs/{job_id}/error` | Detailed error info for failed jobs |
| `PUT` | `/api/jobs/{job_id}/rooms` | Update room classifications & regenerate |
| `WS` | `/api/ws/{job_id}` | WebSocket real-time progress updates |

Interactive API docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Project Structure

```
rescueforge/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes, WebSocket, Celery tasks
│   │   ├── pipeline/      # Core processing pipeline
│   │   │   ├── dwg_converter.py    # DWG -> DXF conversion (LibreDWG)
│   │   │   ├── dxf_parser.py       # DXF entity extraction + fire safety detection
│   │   │   ├── room_detector.py    # Room polygon detection (Shapely + STRtree)
│   │   │   ├── room_classifier.py  # AI room classification (OpenRouter + retry)
│   │   │   ├── plan_generator.py   # DIN 14095 SVG + cover sheet + situation plan
│   │   │   ├── compliance_doc.py   # DIN compliance report (DOCX)
│   │   │   └── pdf_exporter.py     # PDF export (WeasyPrint)
│   │   ├── services/      # OpenRouter client (with retry & rate-limit)
│   │   ├── models/        # Pydantic schemas (16 room types, fire safety fields)
│   │   └── utils/         # Geometry, 18 FKS symbols, translations, corridor routing
│   ├── tests/             # 340 pytest tests (19 suites)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components (PlanViewer, RoomEditor, etc.)
│   │   └── lib/           # API client, i18n, SVG sanitizer
│   ├── cypress/           # Cypress E2E tests
│   ├── Dockerfile
│   └── package.json
├── autocad-plugin/        # AutoCAD plugin concept (Web-first architecture)
├── testdata/              # 15 test files (10 samples + 5 synthetic, see SOURCES.md)
│   └── generate_test_dxfs.py  # Generates 5 synthetic DXFs (mm/m/cm, multilingual)
├── docs/                  # API docs, demo script, FKS specs, presentations
├── docker-compose.yml     # Development setup
├── docker-compose.prod.yml # Production overrides
└── .env.example
```

## DIN 14095 / FKS Guideline Compliance

Output plans follow [DIN 14095](https://www.din.de/) (Feuerwehr-Laufkarten / Orientierungspläne) and the [FKS Richtlinie Orientierungsplaene](https://docs.feukos.ch/richtlinie-orientierungsplane/):

### Plan Set (3 documents + compliance report)
- **Cover Sheet (Deckblatt):** Building info, complete legend, 18 symbol reference entries
- **Situation Plan (Situationsplan):** Building outline with labeled sides (A-D), access points, north arrow
- **Floor Plan (Geschossplan):** A3/A4 landscape format (420x297mm / 297x210mm)
- **Compliance Report:** DOCX document with DIN compliance checklist and manual input requirements

### DIN 14095 Features
- **Filled walls** — double-line polygon rendering (not just lines), RAL 9004 Signalschwarz (#282828)
- **Fire walls** — RAL 3000 Feuerrot (#AF2B1E), 2x normal thickness
- **Fire doors** — red rendering with T-rating labels (T30/T60/T90)
- **10m reference grid** — gray dashed lines with metre labels at edges
- **DIN title block (Schriftfeld)** — ISO 7200-inspired 3-column layout with DIN 14095 / DIN 14034-6 references, creation date, registration number, page number
- **Standard scales** — auto-detected from building size (1:50, 1:100, 1:200, 1:250, 1:500, 1:1000)
- **Room numbering** — DIN format "Type floor.counter" (e.g., "Office 0.03")
- **Minimum sizes** — 7mm symbol minimum, 2mm (5.7pt) font minimum per DIN specification

### Color Coding (RAL standard)
- Corridors: RAL 6019 Weissgrün (#BDECB6) — horizontal escape routes
- Stairwells: DIN dark green (#006400) — vertical escape routes
- Danger zones: Red (#FF0000) — dashed border for technical/server/garage rooms
- Fire walls: RAL 3000 Feuerrot (#AF2B1E)
- Walls: RAL 9004 Signalschwarz (#282828)

### Detection Capabilities
- **Walls:** Layer-based (A-WALL, Wand, MAUER, MUR, PARED, tuong_xay, ...)
- **Doors:** Arc sweep detection + layer-based + INSERT block + wall-gap analysis, with deduplication
- **Fire walls:** Brandwand, FIRE_WALL, FW- patterns
- **Fire doors:** Brandschutz, T30/T60/T90, EI30/EI60/EI90 patterns
- **Windows:** WINDOW, Fenster, GLAZING, Verglasung patterns
- **Sprinklers:** SPRINKLER, SPK, Löschanlage patterns
- **Stairs:** A-STAIR, Treppe, cau thang, escalera patterns
- **Multilingual:** English, German, French, Spanish, Vietnamese layer names

## Testing

```bash
# Backend tests (in Docker — full suite)
docker compose exec backend uv run pytest -v
# 340 tests, 19 suites

# Local tests (no Docker / Celery required)
cd backend && uv run pytest tests/test_dxf_parser.py tests/test_plan_generator.py \
    tests/test_room_detector.py tests/test_symbols_extended.py tests/test_translations.py \
    tests/test_visual_regression.py tests/test_corridor_routing.py \
    tests/test_symbol_collision.py -v

# Generate synthetic test DXFs (if needed)
cd testdata && python generate_test_dxfs.py

# With coverage report
docker compose exec backend uv run pytest --cov=app --cov-report=term-missing -v

# Frontend E2E tests (requires running app)
cd frontend && npm run cypress:open   # interactive
cd frontend && npm run test:e2e       # headless

# Lint
docker compose exec backend uv run ruff check app/
```

### Test Suites

| Suite | Tests | Coverage |
|-------|-------|----------|
| `test_plan_generator.py` | 50 | SVG output, DIN title block, filled walls, fire features, escape routes, unit detection, language EN/DE, room numbering, utility symbols, reference grid |
| `test_dxf_parser.py` | 39 | Layer classification (12 categories), multilingual patterns (EN/DE/FR/ES/VI), block detection, fire wall/door/window/sprinkler patterns, anonymized layers, 5 synthetic DXF files, door deduplication |
| `test_api_routes.py` | 25 | Upload, batch, status, download, metrics, room update, error endpoints |
| `test_symbols_extended.py` | 22 | All 18 FKS symbols return valid svgwrite Groups |
| `test_error_handling.py` | 22 | DXF errors, PDF errors, retry logic, room type validation, security |
| `test_openrouter.py` | 20 | Retry logic (429, 500s, timeout, connect), Retry-After header, vision/text API |
| `test_api_routes_extended.py` | 19 | File downloads, original SVG, error endpoint, job state machine, room validation |
| `test_dwg_converter.py` | 16 | DWG detection, dwg2dxf/dwgread mock, timeout, fallback, path handling |
| `test_translations.py` | 15 | Localization (EN/DE), room labels, fallback, key coverage completeness |
| `test_websocket.py` | 13 | Step labels, UUID validation, progress/success/failure states |
| `test_room_classifier.py` | 10 | Heuristic, Vision API mock, markdown parsing, fallback |
| `test_tasks.py` | 9 | Error persistence, metrics structure, task config, pipeline step tracking |
| `test_room_detector.py` | 8 | Room detection, shared walls, polygon validation |
| `test_performance.py` | 6 | Pipeline benchmarks, memory usage |
| `test_visual_regression.py` | 24 | SVG fingerprint baselines (7 scenarios), pixel-based regression (CairoSVG), fire features, escape routes |
| `test_corridor_routing.py` | 8 | Voronoi medial axis, corridor graph, NetworkX pathfinding, degenerate polygons |
| `test_symbol_collision.py` | 6 | AABB overlap detection, shift on overlap, label registration, small rooms |
| `test_real_world_dxf.py` | 5 | Real-world DXF files from open sources, parser robustness |
| `test_rate_limiting.py` | 3 | Rate limit middleware, concurrent requests |
| **Total** | **340** | |

### Synthetic Test DXF Files

5 generated DXFs covering different units, layer conventions, and fire safety elements:

| File | Dimensions | Unit | Layers | Special |
|------|-----------|------|--------|---------|
| `office_simple_mm.dxf` | 20m × 15m | mm | German (Wand_EG, Tür_EG) | Brandschutz_T30 fire door |
| `house_meters.dxf` | 12m × 10m | m | English (A-WALL, A-DOOR) | Standard AIA layers |
| `warehouse_cm.dxf` | 50m × 30m | cm | Mixed (MAUER, Brandwand) | Fire walls + sprinklers |
| `anonymized_layers.dxf` | 15m × 12m | mm | DWGShare.com_N, layerN | Anonymized layer names |
| `multilingual_layers.dxf` | 18m × 14m | mm | VI/FR/ES (tuong_xay, PORTE) | Vietnamese/French/Spanish |

## Performance

Typical pipeline duration for a standard office building (14 rooms, 248 walls):

| Step | Duration |
|------|----------|
| DXF Parsing | ~500ms |
| Room Detection (Shapely + STRtree) | ~300ms |
| AI Classification (Vision API, up to 3 attempts) | ~5000ms |
| SVG Generation + Escape Routes | ~100ms |
| PDF Export (WeasyPrint) | ~2000ms |
| Cover Sheet + Situation Plan | ~20ms |
| **Total** | **~12s** |

## Deployment (Coolify / Docker)

RescueForge uses no fixed ports (except frontend:3000) and is ready for platforms like Coolify:

```bash
# Production deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Set these environment variables:
- `OPENROUTER_API_KEY` (required)
- `CORS_ORIGINS` (set to your domain, e.g. `https://rescueforge.example.com`)
- `BACKEND_URL` (optional, defaults to `http://backend:8000`)

The frontend proxies all API requests internally via Next.js rewrites. No backend port needs to be exposed to the internet. Docker containers run as non-root users in production.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: celery` | Run tests inside Docker: `docker compose exec backend uv run pytest` |
| Upload returns 413 | File exceeds `MAX_UPLOAD_SIZE_MB` (default 50MB) |
| Vision API timeout | Check `OPENROUTER_API_KEY` in `.env`. Automatic retry (3x) + heuristic fallback. |
| LibreDWG not found | Only needed for DWG files. DXF files work without it. |
| Frontend can't reach backend | API is proxied via Next.js rewrites. Check `BACKEND_URL` env var. |
| WebSocket not connecting | Falls back to HTTP polling automatically (2s interval) |
| Cover sheet 404 | Restart worker after code changes: `docker compose restart worker` |
| Rate limit errors (429) | Adjust rate limit in middleware config or wait for window reset |

## AutoCAD Plugin

See [autocad-plugin/](autocad-plugin/) for the Web-first integration concept. The plugin connects AutoCAD directly to the RescueForge REST API, sending DWG/DXF files through the existing pipeline without duplicating any processing logic.

## Test Data

15 DXF/DWG test files in `testdata/`:
- 10 sample files from various sources — see [testdata/SOURCES.md](testdata/SOURCES.md) for origins and licenses
- 5 synthetic DXFs generated by `testdata/generate_test_dxfs.py` covering mm/m/cm units, multilingual layers (EN/DE/FR/ES/VI), fire safety elements, and anonymized layer names

## License

[Business Source License 1.1](LICENSE) — Free for non-commercial use. Converts to Apache 2.0 on 2029-03-11.

---

## Deutsch

> KI-Tool zur Umwandlung von CAD-Gebäudeplänen (DWG/DXF) in DIN 14095 / FKS-konforme Feuerwehr-Orientierungspläne mit automatischer Massstabserkennung, Brandschutz-Elementerkennung, Korridormittellinien-Fluchtwegen und mehrsprachiger Unterstützung.

**Siemens Hackathon 2025 | Track: Industrial AI** &middot; v0.5.0

### Was RescueForge macht

1. **Hochladen** eines DWG- oder DXF-Gebäudeplans (einzeln oder Batch)
2. **Automatische Bereinigung** — entfernt irrelevante Details (Möbel, Vermassung, Annotationen)
3. **Wandextraktion** — erkennt Wände, Türen, Brandwände, Brandschutztüren, Fenster, Treppen und Sprinkleranlagen
4. **Einheiten-Autoerkennung** — korrigiert falsch deklarierte DXF-Einheiten (mm, cm, m, Zoll, Fuss)
5. **Raumerkennung** — erzeugt Raumpolygone aus geschlossenen Wandstrukturen mittels Computational Geometry (Shapely + STRtree)
6. **Raumklassifikation** — KI-gestützte Klassifikation (16 Raumtypen) via OpenRouter Vision API mit Retry-Logik und heuristischem Fallback
7. **DIN 14095 Planset** — erstellt Geschossplan, Deckblatt, Situationsplan und Konformitätsbericht als SVG + PDF + DOCX
8. **Fluchtweg-Berechnung** — Korridormittellinien-Routing via Voronoi + NetworkX, graphbasierte BFS mit Fallback (Treppenhaus → Lobby → Korridor)
9. **Symbolkollisionsvermeidung** — automatische Platzierungsanpassung verhindert Überlappungen in kleinen Räumen

### Hackathon-Ergebnisse

| Ergebnis | Status |
|----------|--------|
| Funktionierender Prototyp (Docker Compose) | Fertig |
| KI-gestützte Raumklassifikation (Vision API) | Fertig |
| DIN 14095 / FKS-konforme Planausgabe (SVG + PDF) | Fertig |
| Deckblatt + Situationsplan + Konformitätsbericht | Fertig |
| Interaktiver Raumeditor (Umklassifizieren & Neu generieren) | Fertig |
| Batch-Upload (Mehrgeschoss-Verarbeitung) | Fertig |
| WebSocket Echtzeit-Fortschritt | Fertig |
| 340 automatisierte Tests (19 Testsuiten) | Fertig |
| CI/CD Pipeline (GitHub Actions) | Fertig |
| 13-Folien-Präsentation (PPTX) | Fertig |
| AutoCAD-Plugin-Konzept (Web-first Architektur) | Fertig |
| Mehrsprachige Unterstützung (EN/DE) | Fertig |
| DIN-Massstabserkennung (1:50 – 1:1000) | Fertig |
| Brandschutz-Elementerkennung (Wände, Türen, Sprinkler) | Fertig |

### Features

- **DIN 14095 Konformität** — gefüllte Wände, RAL-Farben, 10m-Raster, DIN-Schriftfeld
- **18 Brandschutzsymbole** — Rauchmelder, Handfeuermelder, BMA/BMZ, Schlüsseldepot, Absperrorgane, u.v.m.
- **Automatische Massstabserkennung** — DIN-Standardmassstäbe (1:50 bis 1:1000)
- **Tastaturkürzel** — Ctrl+S (SVG-Download), Ctrl+P (PDF-Download)
- **Ladeanimation** — Skeleton-Platzhalter während der Plangenerierung
- **Korridormittellinien-Fluchtwege** — Voronoi + NetworkX Routing entlang Korridorgeometrie
- **Symbolkollisionsvermeidung** — AABB-Überlappungserkennung mit 4-Richtungs-Verschiebung
- **Dunkelmodus** und **EN/DE Sprachwechsel** (localStorage-persistent)
- **Sicherheit** — SecurityHeaders, Rate-Limiting, CSP, Eingabevalidierung
- **Fehlerprotokollierung** — error.json bei Pipeline-Fehlern mit Schritt und Zeitangabe
- **Celery-Timeouts** — Hardlimit 600s, Softlimit 550s

### Schnellstart

```bash
# Klonen
git clone https://github.com/your-org/rescueforge.git
cd rescueforge

# Konfigurieren
cp .env.example .env
# .env bearbeiten und OPENROUTER_API_KEY eintragen

# Bauen & Starten (Entwicklung)
docker compose up --build

# Bauen & Starten (Produktion)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Das Frontend ist auf Port 3000 erreichbar. Alle API-Anfragen werden intern über Next.js Rewrites an das Backend weitergeleitet — kein direkter Backend-Zugriff nötig.

### DIN 14095 / FKS-Konformität

Die Ausgabepläne folgen [DIN 14095](https://www.din.de/) und der [FKS Richtlinie Orientierungspläne](https://docs.feukos.ch/richtlinie-orientierungsplane/):

- **Deckblatt:** Gebäudeinformationen, vollständige Legende, 18 Symbolreferenz-Einträge
- **Situationsplan:** Gebäudeumriss mit beschrifteten Seiten (A-D), Feuerwehrzufahrt, Nordpfeil
- **Geschossplan:** A3/A4-Querformat (420x297mm / 297x210mm)
- **Gefüllte Wände:** Doppellinien-Polygone, RAL 9004 Signalschwarz
- **Brandwände:** RAL 3000 Feuerrot, doppelte Stärke
- **Brandschutztüren:** Rote Darstellung mit T-Klassifizierung (T30/T60/T90)
- **10m-Referenzraster:** Graue gestrichelte Linien mit Meter-Beschriftung
- **DIN-Schriftfeld:** ISO 7200-Layout mit DIN 14095 / DIN 14034-6 Referenzen
- **Standardmassstäbe:** 1:50, 1:100, 1:200, 1:250, 1:500, 1:1000
- **Raumnummerierung:** DIN-Format "Typ Geschoss.Zähler" (z.B. "Büro 0.03")
- **Fluchtwege:** Graph-basierte BFS-Berechnung mit Fallback-Kette (Treppenhaus → Lobby → Korridor)
- **Gefahrenbereiche:** Rot hervorgehobene gefährliche Räume (Technik, Server, Garage)
- **Konformitätsbericht:** DOCX mit DIN-Checkliste und manuellen Eingabeanforderungen

### Testen

```bash
# Backend-Tests (in Docker — vollständige Suite)
docker compose exec backend uv run pytest -v
# 340 Tests, 19 Testsuiten

# Lokale Tests (ohne Docker — Kerntests)
cd backend && uv run pytest tests/test_dxf_parser.py tests/test_plan_generator.py \
    tests/test_room_detector.py tests/test_symbols_extended.py tests/test_translations.py \
    tests/test_corridor_routing.py tests/test_symbol_collision.py -v
```

### AutoCAD-Plugin

Siehe [autocad-plugin/](autocad-plugin/) für das Web-first Integrationskonzept. Das Plugin verbindet AutoCAD direkt mit der RescueForge REST-API.

### Lizenz

[Business Source License 1.1](LICENSE) — Frei für nicht-kommerzielle Nutzung. Wird am 11.03.2029 zu Apache 2.0.
