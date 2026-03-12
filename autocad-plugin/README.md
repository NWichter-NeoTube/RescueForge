# RescueForge AutoCAD Plugin — Concept

> Web-first integration strategy: AutoCAD connects to the existing RescueForge REST API.

## Why Web-First?

| Approach | Effort | Maintenance | Reach |
|----------|--------|-------------|-------|
| **Web App (current)** | Low | Low | Any browser, any device |
| AutoCAD Plugin (.NET) | High | High (version-locked) | AutoCAD Desktop only |
| Revit Add-in | Very High | Very High | Revit only |

**Decision:** The Hackathon prototype focuses on the Web App. The AutoCAD plugin is designed as a thin client that calls the same REST API — zero duplicated processing logic.

## Architecture

```
AutoCAD Desktop
  |
  |  [C# .NET Plugin / AutoLISP]
  |  - File > Export current drawing as DXF
  |  - POST /api/upload  (multipart/form-data)
  |  - WS /api/ws/{job_id}  (progress)
  |  - GET /api/jobs/{job_id}/svg  (result)
  |
  v
RescueForge REST API (existing)
  |
  v
Pipeline: DXF -> Rooms -> AI Classify -> FKS SVG -> PDF
```

### Data Flow

1. User clicks **"RescueForge > Generate FKS Plan"** in AutoCAD ribbon
2. Plugin exports current drawing as temporary DXF file
3. DXF is uploaded to RescueForge API (`POST /api/upload`)
4. Plugin shows progress bar (WebSocket `WS /api/ws/{job_id}`)
5. On completion: SVG/PDF is downloaded and opened in viewer or inserted as xref
6. Optional: Room classifications displayed as AutoCAD hatches

### API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/upload` | Send DXF from AutoCAD |
| `WS /api/ws/{job_id}` | Real-time progress |
| `GET /api/jobs/{job_id}/svg` | Download FKS plan |
| `GET /api/jobs/{job_id}/pdf` | Download PDF version |
| `GET /api/jobs/{job_id}/data` | Room data for AutoCAD hatching |
| `GET /api/jobs/{job_id}/metrics` | Pipeline metrics display |

## Plugin Design

### Technology Options

| Option | Language | Pros | Cons |
|--------|----------|------|------|
| **.NET Plugin** (recommended) | C# | Full AutoCAD API, ribbon UI, modeless dialogs | Requires .NET, version-specific |
| **AutoLISP Script** | LISP | No compilation, works across versions | Limited UI, no async/WebSocket |
| **ObjectARX** | C++ | Maximum performance | Complex, version-locked DLLs |

### Recommended: .NET Plugin (C#)

```
autocad-plugin/
├── RescueForge.AutoCAD/
│   ├── RescueForge.AutoCAD.csproj
│   ├── Commands/
│   │   ├── GeneratePlanCommand.cs    # Main command
│   │   └── ConfigureCommand.cs       # Server URL settings
│   ├── Services/
│   │   ├── ApiClient.cs              # HTTP + WebSocket client
│   │   └── DxfExporter.cs            # AutoCAD -> temp DXF
│   ├── UI/
│   │   ├── ProgressDialog.xaml       # WPF progress bar
│   │   ├── ResultViewer.xaml         # SVG/PDF preview
│   │   └── RibbonTab.cs             # AutoCAD ribbon integration
│   └── PackageContents.xml           # AutoCAD plugin manifest
└── README.md                         # This file
```

### Key Command

```csharp
// Pseudocode for the main command
[CommandMethod("RESCUEFORGE")]
public async void GenerateFksPlan()
{
    // 1. Export current drawing
    string dxfPath = ExportCurrentDrawingAsDxf();

    // 2. Upload to RescueForge API
    var response = await _apiClient.UploadAsync(dxfPath);

    // 3. Show progress dialog (WebSocket)
    var dialog = new ProgressDialog(response.JobId);
    dialog.Show();

    // 4. Wait for completion
    var result = await _apiClient.WatchProgressAsync(response.JobId);

    // 5. Download and open result
    string pdfPath = await _apiClient.DownloadPdfAsync(result.JobId);
    Process.Start(pdfPath);
}
```

## Configuration

The plugin stores server settings in the user profile:

| Setting | Default | Description |
|---------|---------|-------------|
| `ServerUrl` | `http://localhost:3000` | RescueForge frontend URL |
| `AutoOpenPdf` | `true` | Open PDF after generation |
| `ShowProgress` | `true` | Show progress dialog |
| `Language` | `de` | UI language (en/de) |

For cloud deployment, `ServerUrl` points to the production instance (e.g. `https://rescueforge.example.com`).

## Roadmap

### Phase 1: Hackathon (current)
- Web App with full pipeline
- This concept document

### Phase 2: Proof of Concept (2-4 weeks)
- AutoLISP script for basic DXF export + upload
- Command-line progress display
- PDF download and open

### Phase 3: Full Plugin (2-3 months)
- .NET plugin with ribbon UI
- WPF progress dialog with WebSocket
- Result viewer (SVG preview in AutoCAD)
- Room classification overlay (hatches)
- Batch processing for multi-floor buildings
- Settings dialog (server URL, language)

### Phase 4: Enterprise (6+ months)
- Revit add-in (similar architecture)
- On-premise deployment option
- SSO / Active Directory integration
- Audit trail and version history
- Custom symbol libraries per fire department

## Why This Architecture Works

1. **No duplicated logic** — The plugin is a thin client. All processing happens on the server.
2. **Version independent** — API is stable. Plugin updates are independent of pipeline changes.
3. **Multi-platform** — Same API serves Web, AutoCAD, Revit, and future integrations.
4. **Offline capable** — For air-gapped environments, deploy RescueForge on-premise.
5. **Testable** — Plugin tests mock the API. Pipeline tests are independent.

## Comparison: Plugin vs. Web

| Feature | Web App | AutoCAD Plugin |
|---------|---------|---------------|
| Upload file | Drag & drop | Auto-export current drawing |
| Progress | WebSocket + skeleton UI | WebSocket + WPF dialog |
| Result | In-browser SVG viewer | PDF viewer / xref insert |
| Room editing | Interactive React editor | AutoCAD hatches + properties |
| Batch | Multi-file upload | Multi-layout export |
| Setup | Open browser | Install .bundle package |

Both use the **same REST API** and **same processing pipeline**.
