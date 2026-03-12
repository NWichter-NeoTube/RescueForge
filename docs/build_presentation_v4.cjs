const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

pres.layout = "LAYOUT_16x9";
pres.author = "RescueForge Team";
pres.title = "RescueForge - Siemens Hackathon 2025";

// ── Color Palette: Cherry Bold (fire theme) ──
const C = {
  cherry: "990011",
  offWhite: "FCF6F5",
  navy: "2F3C7E",
  darkBg: "1A1A2E",
  white: "FFFFFF",
  gray100: "F5F5F5",
  gray300: "D1D5DB",
  gray500: "6B7280",
  gray700: "374151",
  gray900: "111827",
  green: "006400",
  greenLight: "90EE90",
  red: "FF0000",
  amber: "D97706",
};

const makeShadow = () => ({
  type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12,
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 1 – Title
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.darkBg };

  // RF logo square
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 1.2, w: 1.0, h: 1.0,
    fill: { color: C.cherry }, rectRadius: 0.12,
  });
  s.addText("RF", {
    x: 0.7, y: 1.2, w: 1.0, h: 1.0,
    fontSize: 32, fontFace: "Arial Black", color: C.white,
    align: "center", valign: "middle", bold: true,
  });

  // Title
  s.addText("RescueForge", {
    x: 2.0, y: 1.0, w: 7.5, h: 0.8,
    fontSize: 44, fontFace: "Arial Black", color: C.white,
    bold: true, margin: 0,
  });
  s.addText("AI-Powered CAD to Fire Department Floor Plans", {
    x: 2.0, y: 1.75, w: 7.5, h: 0.5,
    fontSize: 18, fontFace: "Calibri", color: C.gray300, italic: true, margin: 0,
  });

  // Tagline
  s.addText("Von der CAD-Datei zum normkonformen Feuerwehr-Orientierungsplan in Sekunden.", {
    x: 2.0, y: 2.6, w: 7.5, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.gray500, margin: 0,
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 4.9, w: 10, h: 0.725,
    fill: { color: C.cherry },
  });
  s.addText("Siemens Hackathon 2025  |  Track: Industrial AI  |  FKS-Richtlinie konform", {
    x: 0.5, y: 4.95, w: 9, h: 0.6,
    fontSize: 13, fontFace: "Calibri", color: C.white, align: "center", valign: "middle",
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 2 – Problem
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("Das Problem", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  const problems = [
    { num: "01", title: "Manueller Prozess", desc: "Feuerwehr-Orientierungspläne werden heute manuell aus CAD-Daten erstellt - zeitaufwendig und fehleranfällig." },
    { num: "02", title: "Fehlende Standardisierung", desc: "Unterschiedliche Interpretationen der FKS-Richtlinien führen zu inkonsistenten Plänen." },
    { num: "03", title: "Hohe Kosten", desc: "Spezialisierte Ingenieurbüros verlangen hohe Honorare für die Planerstellung." },
  ];

  problems.forEach((p, i) => {
    const y = 1.4 + i * 1.3;
    // Number
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y, w: 0.7, h: 0.7,
      fill: { color: C.cherry },
    });
    s.addText(p.num, {
      x: 0.7, y, w: 0.7, h: 0.7,
      fontSize: 20, fontFace: "Arial Black", color: C.white,
      align: "center", valign: "middle", bold: true,
    });
    // Text
    s.addText(p.title, {
      x: 1.65, y, w: 7.5, h: 0.35,
      fontSize: 18, fontFace: "Calibri", color: C.gray900, bold: true, margin: 0,
    });
    s.addText(p.desc, {
      x: 1.65, y: y + 0.35, w: 7.5, h: 0.35,
      fontSize: 12, fontFace: "Calibri", color: C.gray500, margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 3 – Solution
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.gray100 };

  s.addText("Unsere Lösung", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  // Flow: Upload → Pipeline → Plans
  const steps = [
    { label: "DWG/DXF\nUpload", color: C.gray700 },
    { label: "AI\nPipeline", color: C.cherry },
    { label: "FKS\nPläne", color: C.green },
  ];

  steps.forEach((st, i) => {
    const x = 1.0 + i * 3.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 2.2, h: 1.0,
      fill: { color: st.color }, shadow: makeShadow(),
    });
    s.addText(st.label, {
      x, y: 1.4, w: 2.2, h: 1.0,
      fontSize: 16, fontFace: "Calibri", color: C.white,
      align: "center", valign: "middle", bold: true,
    });
    if (i < 2) {
      s.addText("\u2192", {
        x: x + 2.2, y: 1.4, w: 0.8, h: 1.0,
        fontSize: 28, color: C.gray500, align: "center", valign: "middle",
      });
    }
  });

  // Features
  const features = [
    "Vollautomatische Konvertierung von CAD zu FKS-Plan",
    "AI-gestützte Raumklassifikation via Vision API (16 Raumtypen)",
    "Deckblatt + Situationsplan + Geschossplan als Komplett-Set",
    "Graph-basierte Fluchtwegberechnung mit BFS-Algorithmus",
    "Interaktiver Editor zur Nachbearbeitung mit sofortiger Regenerierung",
  ];

  features.forEach((f, i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.0, y: 2.85 + i * 0.48, w: 0.15, h: 0.15,
      fill: { color: C.cherry },
    });
    s.addText(f, {
      x: 1.35, y: 2.8 + i * 0.48, w: 8, h: 0.4,
      fontSize: 12, fontFace: "Calibri", color: C.gray700, margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 4 – Architecture
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("Architektur", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  const cols = [
    { title: "Backend", items: ["FastAPI + Celery", "Python 3.12, uv"], color: C.navy },
    { title: "Frontend", items: ["Next.js 15", "React 19, TypeScript"], color: C.cherry },
    { title: "AI / ML", items: ["OpenRouter Vision API", "Gemini 2.0 Flash"], color: C.green },
  ];

  cols.forEach((col, i) => {
    const x = 0.7 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.3, w: 2.8, h: 1.4,
      fill: { color: C.gray100 }, shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.3, w: 2.8, h: 0.06,
      fill: { color: col.color },
    });
    s.addText(col.title, {
      x, y: 1.4, w: 2.8, h: 0.4,
      fontSize: 16, fontFace: "Calibri", color: col.color, bold: true, align: "center",
    });
    s.addText(col.items.map(t => ({ text: t, options: { breakLine: true } })), {
      x: x + 0.15, y: 1.85, w: 2.5, h: 0.7,
      fontSize: 11, fontFace: "Calibri", color: C.gray700, align: "center",
    });
  });

  // Second row
  const cols2 = [
    { title: "CAD Parsing", items: ["ezdxf + LibreDWG", "Shapely Polygonize"] },
    { title: "Rendering", items: ["svgwrite (SVG)", "WeasyPrint (PDF)"] },
    { title: "Infra", items: ["Docker Compose", "Redis + Celery Worker"] },
  ];

  cols2.forEach((col, i) => {
    const x = 0.7 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.1, w: 2.8, h: 1.2,
      fill: { color: C.gray100 }, shadow: makeShadow(),
    });
    s.addText(col.title, {
      x, y: 3.2, w: 2.8, h: 0.35,
      fontSize: 14, fontFace: "Calibri", color: C.gray900, bold: true, align: "center",
    });
    s.addText(col.items.map(t => ({ text: t, options: { breakLine: true } })), {
      x: x + 0.15, y: 3.55, w: 2.5, h: 0.6,
      fontSize: 11, fontFace: "Calibri", color: C.gray500, align: "center",
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 5 – Pipeline
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.darkBg };

  s.addText("Processing Pipeline", {
    x: 0.7, y: 0.3, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
  });

  const steps = [
    { num: "1", label: "DWG \u2192 DXF", tool: "LibreDWG", time: "<1s" },
    { num: "2", label: "DXF Parsing", tool: "ezdxf", time: "~0.5s" },
    { num: "3", label: "Raumerkennung", tool: "Shapely", time: "~0.3s" },
    { num: "4", label: "AI Klassifikation", tool: "Vision API", time: "~5s" },
    { num: "5", label: "SVG Erzeugung", tool: "svgwrite", time: "~0.1s" },
    { num: "6", label: "PDF Export", tool: "WeasyPrint", time: "~2s" },
    { num: "7", label: "Zusatzpläne", tool: "Deckblatt + Sit.", time: "~0.02s" },
  ];

  steps.forEach((st, i) => {
    const row = Math.floor(i / 4);
    const col = i % 4;
    const x = 0.5 + col * 2.35;
    const y = 1.3 + row * 2.0;

    // Number circle
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.7, y: y - 0.05, w: 0.55, h: 0.55,
      fill: { color: C.cherry },
    });
    s.addText(st.num, {
      x: x + 0.7, y: y - 0.05, w: 0.55, h: 0.55,
      fontSize: 16, fontFace: "Arial Black", color: C.white,
      align: "center", valign: "middle", bold: true,
    });
    // Label
    s.addText(st.label, {
      x, y: y + 0.6, w: 1.95, h: 0.35,
      fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", margin: 0,
    });
    s.addText(st.tool, {
      x, y: y + 0.95, w: 1.95, h: 0.25,
      fontSize: 10, fontFace: "Calibri", color: C.gray500, align: "center", margin: 0,
    });
    s.addText(st.time, {
      x, y: y + 1.2, w: 1.95, h: 0.25,
      fontSize: 10, fontFace: "Calibri", color: C.amber, align: "center", margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 6 – AI Room Classification
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("AI Raumklassifikation", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  // Left: How it works
  s.addText("Wie es funktioniert", {
    x: 0.7, y: 1.3, w: 4, h: 0.4,
    fontSize: 18, fontFace: "Calibri", color: C.cherry, bold: true, margin: 0,
  });

  const howSteps = [
    "Grundriss wird als Bild gerendert",
    "Vision API analysiert Raumgeometrien",
    "Heuristik-Fallback bei API-Ausfall",
    "16 Raumtypen werden erkannt",
    "Farbkodierung nach FKS-Standard",
  ];

  howSteps.forEach((h, i) => {
    s.addText(h, {
      x: 0.7, y: 1.85 + i * 0.45, w: 4.5, h: 0.35,
      fontSize: 12, fontFace: "Calibri", color: C.gray700, margin: 0,
      bullet: true,
    });
  });

  // Right: Room types grid
  s.addText("Erkannte Raumtypen", {
    x: 5.5, y: 1.3, w: 4, h: 0.4,
    fontSize: 18, fontFace: "Calibri", color: C.cherry, bold: true, margin: 0,
  });

  const types = [
    "Treppenhaus", "Korridor", "Aufzug", "WC / Nassraum",
    "Büro", "Küche", "Lager", "Technik",
    "Serverraum", "Garage", "Lobby", "Sitzungszimmer",
    "Empfang", "Archiv", "Labor", "Unbekannt",
  ];

  types.forEach((t, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 5.5 + col * 2.2;
    const y = 1.85 + row * 0.4;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: y + 0.05, w: 0.12, h: 0.12,
      fill: { color: i >= 14 ? C.gray500 : i >= 7 ? C.cherry : C.navy },
    });
    s.addText(t, {
      x: x + 0.2, y, w: 1.9, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: C.gray700, margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 7 – FKS Compliance
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.gray100 };

  s.addText("FKS-Richtlinie Konformität", {
    x: 0.7, y: 0.3, w: 9, h: 0.6,
    fontSize: 32, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  const items = [
    { title: "Farbkodierung Fluchtwege", desc: "Dunkelgrün (vertikal), Hellgrün (horizontal)", color: C.green },
    { title: "Gefahrenbereiche", desc: "Rote Umrandung für Technik, Server, Garage", color: C.cherry },
    { title: "Graph-Fluchtwege", desc: "BFS über Raumadjazenzgraph (nicht Luftlinie)", color: C.green },
    { title: "Deckblatt (Cover Sheet)", desc: "Objektdefinition, Legende, Symbolreferenz", color: C.navy },
    { title: "Situationsplan", desc: "Gebäudeumriss, Seiten A-D, Feuerwehrzufahrt", color: C.navy },
    { title: "Geschosslage & Nordpfeil", desc: "Querschnitt-Indikator + Richtungsanzeiger", color: C.gray700 },
    { title: "FKS-Symbole", desc: "Rauchmelder, Handfeuermelder, Schlüsseldepot", color: C.gray700 },
    { title: "A3/A4 + Massstab", desc: "Normgerechte Abmessungen, Massstabsbalken", color: C.gray700 },
    { title: "Flächen-Labels", desc: "Raumfläche (A = X m²) für grosse Räume", color: C.amber },
    { title: "Automatische Legende", desc: "Generiert aus erkannten Raumtypen + Farben", color: C.gray700 },
  ];

  items.forEach((item, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 0.5 + col * 4.7;
    const y = 1.1 + row * 0.85;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.4, h: 0.7,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    // Left accent
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.07, h: 0.7,
      fill: { color: item.color },
    });
    s.addText(item.title, {
      x: x + 0.2, y, w: 4.0, h: 0.35,
      fontSize: 12, fontFace: "Calibri", color: C.gray900, bold: true, margin: 0, valign: "bottom",
    });
    s.addText(item.desc, {
      x: x + 0.2, y: y + 0.35, w: 4.0, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: C.gray500, margin: 0, valign: "top",
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 8 – FKS Plan-Set (NEW)
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("FKS-konformes Plan-Set", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  s.addText("Drei Pläne werden automatisch generiert:", {
    x: 0.7, y: 1.0, w: 8, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.gray500, margin: 0,
  });

  const plans = [
    {
      title: "Deckblatt",
      items: ["Gebäudeinformationen", "Vollständige Farb-Legende", "FKS-Symbolreferenz (8 Symbole)", "Objektdefinition mit Adresse"],
      color: C.navy,
    },
    {
      title: "Situationsplan",
      items: ["Gebäudeumriss mit Seiten A-D", "Feuerwehrzufahrt + Schlüsseldepot", "Nordpfeil + Strassenlage", "Umgebungsübersicht"],
      color: C.green,
    },
    {
      title: "Geschossplan",
      items: ["Raumpolygone mit Farbkodierung", "Fluchtwege (BFS-Graph)", "Gefahrenbereiche (rot)", "Titelblock + Massstab + Legende"],
      color: C.cherry,
    },
  ];

  plans.forEach((plan, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.6, w: 2.9, h: 3.2,
      fill: { color: C.gray100 }, shadow: makeShadow(),
    });
    // Top accent
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.6, w: 2.9, h: 0.06,
      fill: { color: plan.color },
    });
    s.addText(plan.title, {
      x, y: 1.75, w: 2.9, h: 0.5,
      fontSize: 20, fontFace: "Arial Black", color: plan.color,
      bold: true, align: "center",
    });
    plan.items.forEach((item, j) => {
      s.addText(item, {
        x: x + 0.2, y: 2.4 + j * 0.5, w: 2.5, h: 0.4,
        fontSize: 11, fontFace: "Calibri", color: C.gray700, bullet: true, margin: 0,
      });
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 9 – Web Interface
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("Web-Interface", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  const features = [
    { title: "Drag & Drop Upload", desc: "DWG/DXF-Dateien hochladen. Echtzeit-Fortschritt via WebSocket. Batch-Upload bis 10 Dateien." },
    { title: "Interaktiver Viewer", desc: "Zoom, Pan und Layer-Toggle im SVG-Viewer. Wände, Türen, Treppen separat ein-/ausblenden." },
    { title: "Plan-Tabs", desc: "Geschossplan, Deckblatt, Situationsplan und Vorher/Nachher-Vergleich als separate Tabs." },
    { title: "Raum-Editor", desc: "AI-Klassifikationen manuell korrigieren. Plan wird sofort mit neuen Zuweisungen regeneriert." },
    { title: "Export-Dropdown", desc: "SVG + PDF Orientierungsplan, Deckblatt SVG, Situationsplan SVG. Alles mit einem Klick." },
    { title: "Dark Mode", desc: "Vollständiger Dark Mode mit Tailwind CSS. Performance-Metriken pro Pipeline-Schritt einsehbar." },
  ];

  features.forEach((f, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 0.5 + col * 4.7;
    const y = 1.3 + row * 1.3;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.4, h: 1.1,
      fill: { color: C.gray100 }, shadow: makeShadow(),
    });
    s.addText(f.title, {
      x: x + 0.2, y: y + 0.08, w: 4.0, h: 0.35,
      fontSize: 14, fontFace: "Calibri", color: C.cherry, bold: true, margin: 0,
    });
    s.addText(f.desc, {
      x: x + 0.2, y: y + 0.45, w: 4.0, h: 0.55,
      fontSize: 10, fontFace: "Calibri", color: C.gray500, margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 10 – Performance
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.darkBg };

  s.addText("Performance", {
    x: 0.7, y: 0.3, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
  });

  // Big stats
  const stats = [
    { value: "~12s", label: "Gesamte Pipeline\n(inkl. AI-Klassifikation)" },
    { value: "14/14", label: "Räume korrekt\nklassifiziert" },
    { value: "248", label: "Wände erkannt\n(Testgebäude)" },
  ];

  stats.forEach((st, i) => {
    const x = 0.7 + i * 3.1;
    s.addText(st.value, {
      x, y: 1.15, w: 2.8, h: 0.8,
      fontSize: 44, fontFace: "Arial Black", color: C.cherry, bold: true, align: "center", margin: 0,
    });
    s.addText(st.label, {
      x, y: 2.0, w: 2.8, h: 0.6,
      fontSize: 11, fontFace: "Calibri", color: C.gray500, align: "center", margin: 0,
    });
  });

  // Pipeline table
  const tableData = [
    [
      { text: "Pipeline-Schritt", options: { bold: true, color: C.white, fill: { color: C.cherry }, fontSize: 11, fontFace: "Calibri" } },
      { text: "Dauer", options: { bold: true, color: C.white, fill: { color: C.cherry }, fontSize: 11, fontFace: "Calibri" } },
    ],
    [{ text: "DXF Parsing", options: { fontSize: 10, color: C.white } }, { text: "~500ms", options: { fontSize: 10, color: C.white } }],
    [{ text: "Raumerkennung (Shapely)", options: { fontSize: 10, color: C.white } }, { text: "~300ms", options: { fontSize: 10, color: C.white } }],
    [{ text: "AI Raumklassifikation", options: { fontSize: 10, color: C.white } }, { text: "~5000ms", options: { fontSize: 10, color: C.white } }],
    [{ text: "SVG Erzeugung + Fluchtwege", options: { fontSize: 10, color: C.white } }, { text: "~100ms", options: { fontSize: 10, color: C.white } }],
    [{ text: "PDF Export", options: { fontSize: 10, color: C.white } }, { text: "~2000ms", options: { fontSize: 10, color: C.white } }],
    [{ text: "Deckblatt + Situationsplan", options: { fontSize: 10, color: C.white } }, { text: "~20ms", options: { fontSize: 10, color: C.white } }],
  ];

  s.addTable(tableData, {
    x: 1.5, y: 2.9, w: 7, colW: [5, 2],
    border: { pt: 0.5, color: "444444" },
    fill: { color: "2A2A3E" },
    fontFace: "Calibri",
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 11 – Test Results
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("Testergebnisse", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  // Big stats
  const tstats = [
    { value: "66", label: "Unit + Integration Tests" },
    { value: "100%", label: "Passing" },
    { value: "5", label: "Test-Suiten" },
  ];

  tstats.forEach((st, i) => {
    const x = 0.7 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.2, w: 2.8, h: 1.3,
      fill: { color: C.gray100 }, shadow: makeShadow(),
    });
    s.addText(st.value, {
      x, y: 1.25, w: 2.8, h: 0.7,
      fontSize: 40, fontFace: "Arial Black", color: C.cherry, bold: true, align: "center",
    });
    s.addText(st.label, {
      x, y: 1.95, w: 2.8, h: 0.4,
      fontSize: 12, fontFace: "Calibri", color: C.gray500, align: "center",
    });
  });

  // Test suites
  const suites = [
    { name: "test_dxf_parser.py", count: "13 Tests", desc: "Layer-Klassifikation, DXF-Parsing, Entity-Extraktion" },
    { name: "test_room_detector.py", count: "8 Tests", desc: "Einzel-/Mehrraum, Shared Walls, IDs, Flächen" },
    { name: "test_plan_generator.py", count: "26 Tests", desc: "SVG, Fluchtwege, Gefahrenbereiche, Deckblatt, Situationsplan" },
    { name: "test_room_classifier.py", count: "9 Tests", desc: "Heuristik, Vision API Mock, Markdown-Parsing, Fallback" },
    { name: "test_api_routes.py", count: "10 Tests", desc: "Upload, Batch, Status, Download, Metrics-Endpunkte" },
  ];

  suites.forEach((suite, i) => {
    const y = 2.75 + i * 0.52;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y, w: 8.6, h: 0.42,
      fill: { color: i % 2 === 0 ? C.gray100 : C.white },
    });
    s.addText(suite.name, {
      x: 0.9, y, w: 2.8, h: 0.42,
      fontSize: 11, fontFace: "Consolas", color: C.gray900, valign: "middle", margin: 0,
    });
    s.addText(suite.count, {
      x: 3.7, y, w: 1.2, h: 0.42,
      fontSize: 11, fontFace: "Calibri", color: C.cherry, bold: true, valign: "middle", margin: 0,
    });
    s.addText(suite.desc, {
      x: 4.9, y, w: 4.2, h: 0.42,
      fontSize: 10, fontFace: "Calibri", color: C.gray500, valign: "middle", margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 12 – Differentiators
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.gray100 };

  s.addText("Was uns unterscheidet", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  const diffs = [
    { title: "End-to-End Automatisierung", desc: "Keine manuellen Zwischenschritte - von der CAD-Datei zum fertigen Plan-Set (3 Pläne + PDF)" },
    { title: "Human-in-the-Loop", desc: "AI klassifiziert, Benutzer korrigiert. Plan wird sofort regeneriert. Best of both worlds." },
    { title: "Normkonform by Design", desc: "FKS-Richtlinien sind in die Pipeline eingebaut. Gefahrenbereiche, Fluchtwege, Symbole - alles automatisch." },
    { title: "Transparent & Messbar", desc: "Performance-Metriken pro Schritt. 66 Tests. Jeder Lauf ist reproduzierbar und verifizierbar." },
  ];

  diffs.forEach((d, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 0.5 + col * 4.7;
    const y = 1.3 + row * 1.9;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.4, h: 1.6,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    // Left accent
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.07, h: 1.6,
      fill: { color: C.cherry },
    });
    s.addText(d.title, {
      x: x + 0.25, y: y + 0.15, w: 3.9, h: 0.4,
      fontSize: 16, fontFace: "Calibri", color: C.gray900, bold: true, margin: 0,
    });
    s.addText(d.desc, {
      x: x + 0.25, y: y + 0.6, w: 3.9, h: 0.8,
      fontSize: 12, fontFace: "Calibri", color: C.gray500, margin: 0,
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 13 – Roadmap
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("Ausblick", {
    x: 0.7, y: 0.4, w: 8, h: 0.7,
    fontSize: 36, fontFace: "Arial Black", color: C.gray900, bold: true, margin: 0,
  });

  const phases = [
    { phase: "Phase 1", title: "Multi-Geschoss", desc: "Automatische Erkennung und Verarbeitung aller Stockwerke eines Gebäudes", color: C.cherry },
    { phase: "Phase 2", title: "BIM Integration", desc: "IFC/Revit-Import für noch reichhaltigere Gebäudedaten und 3D-Modelle", color: C.navy },
    { phase: "Phase 3", title: "Erweiterte Analyse", desc: "Brandlast-Bewertung, Evakuierungssimulation und Kapazitätsplanung", color: C.green },
    { phase: "Phase 4", title: "SaaS Platform", desc: "Cloud-basierte Lösung für Ingenieurbüros und Feuerwehren mit API-Zugang", color: C.gray700 },
  ];

  phases.forEach((p, i) => {
    const y = 1.3 + i * 1.0;
    // Phase tag
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y, w: 1.0, h: 0.35,
      fill: { color: p.color },
    });
    s.addText(p.phase, {
      x: 0.7, y, w: 1.0, h: 0.35,
      fontSize: 10, fontFace: "Calibri", color: C.white, bold: true,
      align: "center", valign: "middle",
    });
    // Title + desc
    s.addText(p.title, {
      x: 1.95, y, w: 7, h: 0.35,
      fontSize: 16, fontFace: "Calibri", color: C.gray900, bold: true, margin: 0, valign: "middle",
    });
    s.addText(p.desc, {
      x: 1.95, y: y + 0.35, w: 7, h: 0.35,
      fontSize: 11, fontFace: "Calibri", color: C.gray500, margin: 0,
    });
    // Connector line
    if (i < phases.length - 1) {
      s.addShape(pres.shapes.LINE, {
        x: 1.2, y: y + 0.7, w: 0, h: 0.3,
        line: { color: C.gray300, width: 1.5, dashType: "dash" },
      });
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 14 – Thank You
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.darkBg };

  // RF logo
  s.addShape(pres.shapes.RECTANGLE, {
    x: 4.25, y: 1.0, w: 1.5, h: 1.5,
    fill: { color: C.cherry },
  });
  s.addText("RF", {
    x: 4.25, y: 1.0, w: 1.5, h: 1.5,
    fontSize: 48, fontFace: "Arial Black", color: C.white,
    align: "center", valign: "middle", bold: true,
  });

  s.addText("Vielen Dank!", {
    x: 1, y: 2.8, w: 8, h: 0.8,
    fontSize: 40, fontFace: "Arial Black", color: C.white, bold: true, align: "center",
  });

  s.addText("RescueForge \u2014 Von CAD zu FKS in Sekunden", {
    x: 1, y: 3.5, w: 8, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: C.gray300, italic: true, align: "center",
  });

  s.addText("Fragen?", {
    x: 1, y: 4.2, w: 8, h: 0.5,
    fontSize: 20, fontFace: "Calibri", color: C.cherry, bold: true, align: "center",
  });

  s.addText("Siemens Hackathon 2025  |  66 Tests  |  14 Räume  |  ~12s Pipeline", {
    x: 1, y: 4.8, w: 8, h: 0.4,
    fontSize: 11, fontFace: "Calibri", color: C.gray500, align: "center",
  });
}

// ── Write file ──
const outPath = "C:\\Users\\nikla\\Desktop\\Sonstiges\\Projekte\\RescueForge\\docs\\RescueForge_Presentation.pptx";
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("Presentation v4 written to:", outPath);
}).catch((err) => {
  console.error("Failed:", err);
  process.exit(1);
});
