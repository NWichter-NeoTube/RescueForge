# RescueForge API Documentation

Base URL: `http://localhost:<port>` (check `docker compose ps` for assigned port)

## Authentication

No authentication required (prototype). Production deployments should add API key or OAuth2.

## Rate Limiting

Upload endpoints (`/api/upload`, `/api/upload/batch`) are rate-limited to **20 requests per 60 seconds** per client IP. Exceeding this limit returns:

```json
HTTP 429 Too Many Requests
{
  "detail": "Too many requests. Please try again later."
}
```

## Endpoints

### Health Check

```
GET /health
```

**Response** `200 OK`
```json
{
  "status": "ok",
  "service": "rescueforge",
  "version": "0.2.0"
}
```

### Upload Floor Plan

```
POST /api/upload
Content-Type: multipart/form-data
```

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | yes | DWG or DXF file (max 50 MB) |

**Response** `200 OK`
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "floor_plan.dxf",
  "status": "pending"
}
```

**Errors**
- `400` — No filename provided
- `400` — Unsupported file format (must be `.dwg` or `.dxf`)
- `400` — Empty file
- `413` — File too large (exceeds 50 MB)
- `429` — Rate limit exceeded

### Batch Upload

```
POST /api/upload/batch
Content-Type: multipart/form-data
```

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | yes | Up to 10 DWG/DXF files |

**Response** `200 OK`
```json
{
  "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "jobs": [
    { "job_id": "...", "filename": "eg.dxf" },
    { "job_id": "...", "filename": "og1.dxf" }
  ],
  "count": 2,
  "skipped": ["readme.txt"]
}
```

**Errors**
- `400` — No files provided
- `400` — More than 10 files
- `400` — No valid DWG/DXF files in batch
- `429` — Rate limit exceeded

### Job Status

```
GET /api/jobs/{job_id}
```

Returns the current processing status. Uses Celery/Redis as single source of truth.

**Response** `200 OK`
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "classifying",
  "progress": 0.6,
  "message": "Processing: classifying"
}
```

When completed:
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "completed",
  "progress": 1.0,
  "message": "Processing complete",
  "result_svg": "/outputs/{job_id}/floor_plan_orientierungsplan.svg",
  "result_pdf": "/outputs/{job_id}/floor_plan_orientierungsplan.pdf"
}
```

**Status values** (enum `ProcessingStatus`):

| Value | Description |
|-------|-------------|
| `pending` | Queued, waiting for worker |
| `converting` | DWG → DXF conversion |
| `parsing` | DXF entity extraction |
| `detecting_rooms` | Room polygon detection |
| `classifying` | AI room classification |
| `generating` | SVG plan generation |
| `exporting` | PDF export |
| `completed` | All done |
| `failed` | Pipeline error |

**Errors**
- `400` — Invalid job ID format (must be UUID)
- `404` — Job not found

### Download Orientation Plan

```
GET /api/jobs/{job_id}/svg
GET /api/jobs/{job_id}/pdf
```

**Response**: File download with appropriate Content-Type header (`image/svg+xml` or `application/pdf`).

**Errors**
- `400` — Invalid job ID format
- `404` — Output not found (job may not be complete)

### Download Cover Sheet (Deckblatt)

```
GET /api/jobs/{job_id}/cover-sheet
```

**Response**: FKS Deckblatt SVG with building info, complete legend, and symbol reference.

### Download Situation Plan

```
GET /api/jobs/{job_id}/situation-plan
```

**Response**: Situationsplan SVG with building outline, labeled sides, access points.

### Original DXF Preview

```
GET /api/jobs/{job_id}/original-svg
```

**Response**: Dynamically generated SVG preview of the uploaded DXF (before FKS processing). Renders walls, doors, and stairs from the raw geometry.

### Floor Plan Data

```
GET /api/jobs/{job_id}/data
```

**Response** `200 OK`: Full floor plan JSON including rooms, walls, doors, stairs, bounds, scale, and unit.

```json
{
  "filename": "floor_plan.dxf",
  "floor_label": "EG",
  "walls": [{ "start": {"x": 0, "y": 0}, "end": {"x": 10, "y": 0}, "thickness": 0.2 }],
  "doors": [{ "position": {"x": 5, "y": 0}, "width": 1.0, "angle": 90.0 }],
  "stairs": [{ "polygon": [{"x": 0, "y": 0}, {"x": 2, "y": 0}, {"x": 2, "y": 3}], "direction": "up" }],
  "rooms": [
    {
      "id": 1,
      "points": [{"x": 0, "y": 0}, {"x": 5, "y": 0}, {"x": 5, "y": 5}, {"x": 0, "y": 5}],
      "room_type": "office",
      "label": "Büro 1",
      "area": 25.0
    }
  ],
  "bounds": [0, 0, 50, 30],
  "scale": 1.0,
  "unit": "mm"
}
```

### Pipeline Metrics

```
GET /api/jobs/{job_id}/metrics
```

**Response** `200 OK`: Performance metrics per pipeline step (duration in ms, file sizes, entity counts).

### Update Room Classifications

```
PUT /api/jobs/{job_id}/rooms
Content-Type: application/json
```

**Body**: Array of room updates. Only `id` is required; include `room_type` and/or `label` to change.

```json
[
  { "id": 1, "room_type": "office", "label": "Büro 1" },
  { "id": 2, "room_type": "corridor" }
]
```

**Effect**: Updates classifications in `floor_plan_data.json`, then regenerates all outputs:
- Orientation plan (SVG + PDF)
- Cover sheet (Deckblatt SVG)
- Situation plan (Situationsplan SVG)

**Response** `200 OK`
```json
{
  "status": "regenerated",
  "rooms_updated": 2
}
```

## Room Types

| Value | Description (DE) |
|-------|-----------------|
| `office` | Büro |
| `corridor` | Flur / Gang |
| `stairwell` | Treppenhaus |
| `elevator` | Aufzug |
| `bathroom` | Sanitärraum |
| `kitchen` | Küche |
| `storage` | Lager |
| `technical` | Technikraum |
| `server_room` | Serverraum |
| `garage` | Garage |
| `lobby` | Empfang / Foyer |
| `conference` | Besprechungsraum |
| `residential` | Wohnraum |
| `bedroom` | Schlafzimmer |
| `living_room` | Wohnzimmer |
| `balcony` | Balkon |
| `unknown` | Unbekannt |

## Pipeline Stages

| Stage | Description | Duration (typical) |
|-------|-------------|-------------------|
| `converting` | Convert DWG to DXF via LibreDWG | < 1 s |
| `parsing` | Extract entities (walls, doors, stairs) via ezdxf | ~500 ms |
| `detecting_rooms` | Detect room polygons via Shapely polygonize | ~300 ms |
| `classifying` | Classify rooms via OpenRouter Vision API | ~5 s |
| `generating` | Generate FKS-compliant SVG + symbols + escape routes | ~100 ms |
| `exporting` | Export to PDF via WeasyPrint | ~2 s |
| supplementary | Generate cover sheet + situation plan | ~50 ms |

## WebSocket (Real-Time Progress)

```
WS /api/ws/{job_id}
```

Connect after uploading a file to receive real-time progress updates. The server polls Celery every 500 ms and sends updates only when state or progress changes.

### Progress Message

```json
{
  "type": "progress",
  "step": "classifying",
  "status": "classifying",
  "progress": 0.6,
  "message": "AI klassifiziert Räume..."
}
```

### Completion Message

```json
{
  "type": "complete",
  "status": "completed",
  "progress": 1.0,
  "svg_url": "/outputs/{job_id}/..._orientierungsplan.svg",
  "pdf_url": "/outputs/{job_id}/..._orientierungsplan.pdf",
  "rooms_count": 8,
  "walls_count": 42
}
```

### Error Message

```json
{
  "type": "error",
  "status": "failed",
  "progress": 0.0,
  "message": "Human-readable error description"
}
```

## Error Handling

All REST errors return JSON with a `detail` field:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Status | Cause |
|-------------|-------|
| 400 | Invalid file format, empty file, invalid job ID (not UUID) |
| 404 | Job not found, output file not available yet |
| 413 | File exceeds 50 MB size limit |
| 422 | Floor plan has zero dimensions (degenerate geometry) |
| 429 | Rate limit exceeded on upload endpoints |
| 500 | Internal server error (conversion, parsing, classification) |

## Security

- **CORS**: Configurable via `CORS_ORIGINS` env var (comma-separated origins, default `*`)
- **Rate limiting**: 20 req/60 s per IP on upload endpoints
- **Path traversal**: Job IDs validated as UUID format before filesystem access
- **File validation**: Only `.dwg`/`.dxf` accepted, empty files rejected
- **Job cleanup**: Directories older than 24 hours automatically removed on startup
