# RescueForge - Architektur-Dokumentation

## Übersicht

RescueForge ist eine webbasierte Lösung zur automatischen Transformation von CAD-Gebäudeplänen (DWG/DXF) in DIN 14095 / FKS-konforme Feuerwehr-Orientierungspläne mit Korridormittellinien-Fluchtwegen, Symbolkollisionsvermeidung und mehrsprachiger Unterstützung (EN/DE).

## Systemarchitektur

```
┌─────────────────┐     HTTP/WS      ┌──────────────────┐
│                 │ ◄──────────────► │                  │
│   Frontend      │                  │   Backend API    │
│   (Next.js 15)  │                  │   (FastAPI)      │
│   Port 3000     │                  │   Port 8000      │
│                 │                  │                  │
└─────────────────┘                  └────────┬─────────┘
                                              │
                                    Celery Task Queue
                                              │
                                     ┌────────▼─────────┐
                                     │                  │
                                     │  Celery Worker   │
                                     │  (Pipeline)      │
                                     │                  │
                                     └────────┬─────────┘
                                              │
                                     ┌────────▼─────────┐
                                     │                  │
                                     │     Redis        │
                                     │  (Broker + Cache)│
                                     │                  │
                                     └──────────────────┘
```

## Container-Architektur (Docker Compose)

| Service | Image | Funktion | Ports |
|---------|-------|----------|-------|
| `backend` | rescueforge-backend | FastAPI REST API | 8000 (dynamisch) |
| `worker` | rescueforge-backend | Celery Worker (Pipeline) | - |
| `frontend` | rescueforge-frontend | Next.js Web UI | 3000 (dynamisch) |
| `redis` | redis:7-alpine | Task Queue + Result Backend | 6379 (dynamisch) |

Shared Volumes:
- `upload_data` - Hochgeladene DWG/DXF-Dateien
- `output_data` - Generierte SVG/PDF-Outputs
- `redis_data` - Redis Persistenz

## Verarbeitungs-Pipeline

```
 Upload (DWG/DXF)
       │
       ▼
 ┌─────────────────────┐
 │ 1. DWG Converter    │  LibreDWG (dwg2dxf)
 │    DWG → DXF        │  Nur falls .dwg Input
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 2. DXF Parser       │  ezdxf
 │    → Wände          │  Layer-basierte Klassifikation
 │    → Türen          │  Pattern Matching (WALL, DOOR, ...)
 │    → Treppen        │  Fallback: Linienstärke-Heuristik
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 3. Room Detector    │  Shapely
 │    → Raumpolygone   │  polygonize() + Gap Closing
 │    → Flächen        │  Buffer/Unbuffer-Technik
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 4. Room Classifier  │  OpenRouter Vision API
 │    → Büro           │  Plan als PNG rendern
 │    → Korridor       │  Gemini 2.5 Flash klassifiziert
 │    → Treppenhaus    │  Fallback: Geometrie-Heuristik
 │    → WC, Lager ...  │
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 5. Corridor Routing │  SciPy Voronoi + NetworkX
 │    → Medial Axis    │  Korridormittellinien-Extraktion
 │    → Fluchtwege     │  Graph-basierte Wegfindung
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 6. Plan Generator   │  svgwrite + SymbolPlacer
 │    → FKS SVG        │  Farbgebung nach Richtlinie
 │    → Kollisionsfrei │  AABB-Überlappungserkennung
 │    → Titelblock     │  A3/A4 Querformat
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 7. PDF Exporter     │  WeasyPrint
 │    → Druckfertig    │  SVG in HTML eingebettet
 └──────────┬──────────┘
            ▼
 ┌─────────────────────┐
 │ 8. Supplementary    │  Cover Sheet, Situation Plan
 │    → Deckblatt      │  Legende + Symbolreferenz
 │    → Situationsplan │  Gebäudeumriss (A-D)
 │    → Konformität    │  DIN-Checkliste (DOCX)
 └─────────────────────┘
```

## API-Design

### REST Endpoints

| Method | Path | Funktion |
|--------|------|----------|
| GET | `/health` | Health Check (Version, Status) |
| POST | `/api/upload` | DWG/DXF Upload (einzeln) |
| POST | `/api/upload/batch` | Batch Upload (max 10 Dateien) |
| GET | `/api/jobs/{id}` | Job Status (Celery) |
| GET | `/api/jobs/{id}/svg` | FKS-Orientierungsplan (SVG) |
| GET | `/api/jobs/{id}/pdf` | FKS-Orientierungsplan (PDF) |
| GET | `/api/jobs/{id}/cover-sheet` | Deckblatt (SVG) |
| GET | `/api/jobs/{id}/situation-plan` | Situationsplan (SVG) |
| GET | `/api/jobs/{id}/compliance` | DIN-Konformitätsbericht (DOCX) |
| GET | `/api/jobs/{id}/original-svg` | Original DXF Vorschau |
| GET | `/api/jobs/{id}/data` | Grundrissdaten (JSON) |
| GET | `/api/jobs/{id}/metrics` | Pipeline-Leistungsmetriken |
| GET | `/api/jobs/{id}/error` | Fehlerdetails |
| PUT | `/api/jobs/{id}/rooms` | Raumklassifikation aktualisieren |
| WS | `/api/ws/{id}` | Live Progress Updates |

### WebSocket Protocol

```json
// Server → Client (Progress Update)
{
  "type": "progress",
  "step": "classifying",
  "progress": 0.6,
  "message": "AI klassifiziert Räume..."
}

// Server → Client (Completion)
{
  "type": "complete",
  "svg_url": "/api/jobs/{id}/svg",
  "pdf_url": "/api/jobs/{id}/pdf"
}
```

## Datenmodell

```
FloorPlanData
├── filename: str
├── walls: [WallSegment]        # start/end Points
├── doors: [DoorInfo]           # position, width
├── stairs: [StairInfo]         # polygon, direction
├── rooms: [RoomPolygon]        # points, type, label, area
├── bounds: (minx, miny, maxx, maxy)
├── scale: float
└── unit: str (mm/cm/m)

RoomType (Enum)
├── office, corridor, stairwell, elevator
├── bathroom, kitchen, storage, technical
├── garage, lobby, conference
├── residential, bedroom, living_room, balcony
└── unknown
```

## Layer-Klassifikation

DXF-Dateien verwenden keine standardisierten Layer-Namen. Die Pipeline verwendet Pattern Matching:

| Pattern | Klassifikation | Aktion |
|---------|---------------|--------|
| wall, wand, mauer | Wand | Behalten |
| door, tür, tuer | Tür | Behalten |
| stair, treppe | Treppe | Behalten |
| furn, möbel | Möbel | Entfernen |
| dim, mass, anno | Vermassung | Entfernen |
| hatch, schraffur | Schraffur | Entfernen |
| (unbekannt) | Prüfe Linienstärke | ≥0.3mm → Wand |

## AI-Klassifikation

### Ansatz
1. Floor Plan mit nummerierten Räumen als PNG rendern (Matplotlib)
2. Bild an Vision API senden (OpenRouter → Gemini 2.5 Flash)
3. JSON-Response parsen: `[{"id": 1, "type": "office", "label": "Büro"}]`

### Fallback (Heuristik)
Wenn AI nicht verfügbar, geometrische Regeln:
- Seitenverhältnis > 4 → Korridor
- Fläche < 20% Median → WC
- Fläche < 40% Median → Lager
- Fläche < 200% Median → Büro
- Fläche > 200% Median → Halle

## FKS-Richtlinie Konformität

| Anforderung | Umsetzung |
|-------------|-----------|
| A3/A4 Querformat | SVG viewBox + PDF @page |
| Max. Massstab 1:300 | Automatische DIN-Skalierung (1:50–1:1000) |
| Fluchtwege grün | Dunkelgrün/Hellgrün, Korridormittellinien-Routing |
| Raumbeschriftung | AI-generierte Labels (EN/DE) |
| Legende | Automatisch aus Raumtypen |
| Titelblock | ISO 7200-Layout mit DIN 14095 Referenzen |
| Nordpfeil | Im SVG-Output |
| Gefüllte Wände | Doppellinien-Polygone, RAL 9004 |
| Brandwände | RAL 3000, doppelte Stärke |
| 10m-Referenzraster | Graue gestrichelte Linien |
| 20 FKS-Symbole | DIN 14034-6 konform |
| Symbolkollisionsfrei | AABB-basierte Platzierung |
| Fluchtweg-Distanzvalidierung | Max. 35m, rote Markierung bei Überschreitung |
| Brandabschnitte | Polygonize aus Brandwänden, BA-Nummerierung |
| Notausgang-Symbole | An Türen nahe Treppenhäusern (DIN 14034-6) |
| Feuerlöscher-Symbole | In Korridoren/Lobbys (§7 DIN 14095) |
| Geschosserkennung | Aus DXF-Layouts und Dateinamen |
| 20 FKS-Symbole | DIN 14034-6 konform inkl. Notausgang + Feuerlöscher |

## Technologie-Entscheide

| Entscheid | Begründung |
|-----------|-----------|
| Vektor-first (ezdxf) | Präziser als Bild-Umweg, behält Geometrie |
| Vision API statt eigenes ML | Kein Training nötig, flexibel, einfach |
| Celery + Redis | Langläufer im Hintergrund, skalierbar |
| SciPy Voronoi + NetworkX | Korridormittellinien-Extraktion, gewichtete Wegfindung |
| uv statt pip | 10x schneller, reproduzierbarer lockfile |
| Docker Compose | Einfaches Setup, LibreDWG nativ kompiliert |
| WeasyPrint | CSS-basiert, SVG-Support, kein Headless-Browser |
| CairoSVG | Pixel-basierte visuelle Regressionstests |

## Sicherheit

- SecurityHeadersMiddleware (X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy)
- RateLimitMiddleware mit automatischer Bereinigung (Memory-Leak-frei)
- CORS-Konfiguration (credentials nur mit expliziten Origins)
- Dateigrössen-Limit (50MB)
- Nur .dwg/.dxf akzeptiert
- Job-ID UUID-Validierung am WebSocket
- API Keys via .env (nicht committed)
- DSG/GDPR-konform: Keine personenbezogenen Daten gespeichert
- Non-Root Docker Container in Produktion
- Celery Task-Timeouts (Hardlimit 600s, Softlimit 550s)
