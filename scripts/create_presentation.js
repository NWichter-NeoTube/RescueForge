const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

pres.layout = "LAYOUT_16x9";
pres.author = "RescueForge Team";
pres.title = "RescueForge - AI-Powered Fire Department Floor Plans";

// ── Color Palette (Fire Department theme) ──
const C = {
  darkRed: "B91C1C",
  red: "DC2626",
  darkBg: "111827",
  darkCard: "1F2937",
  charcoal: "374151",
  gray: "6B7280",
  lightGray: "E5E7EB",
  offWhite: "F9FAFB",
  white: "FFFFFF",
  gold: "F59E0B",
  green: "059669",
  blue: "2563EB",
};

const FONT_TITLE = "Georgia";
const FONT_BODY = "Calibri";

const makeShadow = () => ({
  type: "outer",
  blur: 6,
  offset: 2,
  angle: 135,
  color: "000000",
  opacity: 0.2,
});

// ══════════════════════════════════════════════════
// SLIDE 1: Title
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  // Red accent bar at top
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.red },
  });

  // RF Logo square
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.2, w: 0.9, h: 0.9,
    fill: { color: C.red },
    shadow: makeShadow(),
  });
  slide.addText("RF", {
    x: 0.8, y: 1.2, w: 0.9, h: 0.9,
    fontSize: 28, fontFace: FONT_TITLE, bold: true,
    color: C.white, align: "center", valign: "middle",
  });

  // Title
  slide.addText("RescueForge", {
    x: 2.0, y: 1.1, w: 7, h: 0.7,
    fontSize: 44, fontFace: FONT_TITLE, bold: true,
    color: C.white, margin: 0,
  });
  slide.addText("KI-gestützte Feuerwehr-Orientierungspläne aus CAD-Daten", {
    x: 2.0, y: 1.75, w: 7, h: 0.5,
    fontSize: 18, fontFace: FONT_BODY,
    color: C.gold, italic: true, margin: 0,
  });

  // Tagline
  slide.addText("Von der CAD-Datei zum normkonformen Feuerwehr-Orientierungsplan in Sekunden.", {
    x: 0.8, y: 3.0, w: 8, h: 0.5,
    fontSize: 16, fontFace: FONT_BODY,
    color: C.lightGray, margin: 0,
  });

  // Footer
  slide.addText("Siemens Hackathon 2025  |  Track: Industrial AI", {
    x: 0.8, y: 4.8, w: 5, h: 0.4,
    fontSize: 11, fontFace: FONT_BODY,
    color: C.gray,
  });
  slide.addText("FKS-Richtlinie konform", {
    x: 7.2, y: 4.8, w: 2.3, h: 0.35,
    fontSize: 10, fontFace: FONT_BODY, align: "center",
    color: C.lightGray,
    shape: pres.shapes.ROUNDED_RECTANGLE,
    fill: { color: C.darkCard },
  });
}

// ══════════════════════════════════════════════════
// SLIDE 2: Problem
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addText("Das Problem", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.darkBg, margin: 0,
  });

  // Problem cards
  const problems = [
    { num: "01", title: "Manueller Prozess", desc: "Feuerwehr-Orientierungspläne werden heute manuell aus CAD-Daten erstellt - zeitaufwendig und fehleranfällig." },
    { num: "02", title: "Fehlende Standardisierung", desc: "Unterschiedliche Interpretationen der FKS-Richtlinien führen zu inkonsistenten Plänen." },
    { num: "03", title: "Hohe Kosten", desc: "Spezialisierte Ingenieurbüros verlangen hohe Honorare für die Planerstellung." },
  ];

  problems.forEach((p, i) => {
    const y = 1.35 + i * 1.3;
    // Card background
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y, w: 8.4, h: 1.1,
      fill: { color: C.white },
      shadow: makeShadow(),
    });
    // Red left accent
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y, w: 0.07, h: 1.1,
      fill: { color: C.red },
    });
    // Number
    slide.addText(p.num, {
      x: 1.1, y, w: 0.5, h: 1.1,
      fontSize: 24, fontFace: FONT_TITLE, bold: true,
      color: C.red, valign: "middle", margin: 0,
    });
    // Title
    slide.addText(p.title, {
      x: 1.7, y: y + 0.15, w: 7, h: 0.35,
      fontSize: 16, fontFace: FONT_BODY, bold: true,
      color: C.darkBg, margin: 0,
    });
    // Description
    slide.addText(p.desc, {
      x: 1.7, y: y + 0.5, w: 7, h: 0.45,
      fontSize: 12, fontFace: FONT_BODY,
      color: C.gray, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 3: Solution Overview
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText("Unsere Lösung", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.white, margin: 0,
  });

  // Central flow: DWG/DXF → AI Pipeline → FKS Plan
  const flowItems = [
    { label: "DWG/DXF\nUpload", color: C.blue },
    { label: "AI\nPipeline", color: C.gold },
    { label: "FKS\nPlan", color: C.green },
  ];

  flowItems.forEach((item, i) => {
    const x = 1.5 + i * 3;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 2.2, h: 1.5,
      fill: { color: C.darkCard },
      shadow: makeShadow(),
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 2.2, h: 0.06,
      fill: { color: item.color },
    });
    slide.addText(item.label, {
      x, y: 1.4, w: 2.2, h: 1.5,
      fontSize: 18, fontFace: FONT_BODY, bold: true,
      color: C.white, align: "center", valign: "middle",
    });

    // Arrow between items
    if (i < 2) {
      slide.addText("→", {
        x: x + 2.2, y: 1.7, w: 0.8, h: 0.7,
        fontSize: 28, fontFace: FONT_BODY,
        color: C.gold, align: "center", valign: "middle",
      });
    }
  });

  // Feature bullets
  const features = [
    "Vollautomatische Konvertierung von CAD zu FKS-Plan",
    "AI-gestützte Raumklassifikation via Vision API",
    "Normkonforme Ausgabe als SVG + PDF",
    "Interaktiver Editor zur Nachbearbeitung",
  ];

  features.forEach((f, i) => {
    slide.addText(f, {
      x: 1.5, y: 3.4 + i * 0.4, w: 7, h: 0.35,
      fontSize: 13, fontFace: FONT_BODY,
      color: C.lightGray, bullet: true, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 4: Tech Stack / Architecture
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addText("Architektur", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.darkBg, margin: 0,
  });

  // 2x3 grid of tech cards
  const techCards = [
    { title: "Backend", items: "FastAPI + Celery\nPython 3.12, uv", accent: C.blue },
    { title: "Frontend", items: "Next.js 15\nReact 19, TypeScript", accent: C.green },
    { title: "AI / ML", items: "OpenRouter Vision API\nGPT-4o / Gemini", accent: C.gold },
    { title: "CAD Parsing", items: "ezdxf + LibreDWG\nShapely Polygonize", accent: C.red },
    { title: "Rendering", items: "svgwrite (SVG)\nWeasyPrint (PDF)", accent: C.darkRed },
    { title: "Infra", items: "Docker Compose\nRedis + Celery Worker", accent: C.charcoal },
  ];

  techCards.forEach((card, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 3;
    const y = 1.3 + row * 2;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.7, h: 1.7,
      fill: { color: C.white },
      shadow: makeShadow(),
    });
    // Accent bar top
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.7, h: 0.06,
      fill: { color: card.accent },
    });
    slide.addText(card.title, {
      x: x + 0.2, y: y + 0.15, w: 2.3, h: 0.35,
      fontSize: 15, fontFace: FONT_BODY, bold: true,
      color: C.darkBg, margin: 0,
    });
    slide.addText(card.items, {
      x: x + 0.2, y: y + 0.55, w: 2.3, h: 0.9,
      fontSize: 11, fontFace: FONT_BODY,
      color: C.gray, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 5: Pipeline Flow
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText("Verarbeitungs-Pipeline", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.white, margin: 0,
  });

  const steps = [
    { step: "1", label: "DWG → DXF", desc: "LibreDWG Konvertierung", time: "<1s" },
    { step: "2", label: "DXF Parsing", desc: "ezdxf Entity-Extraktion", time: "~0.5s" },
    { step: "3", label: "Raumerkennung", desc: "Shapely Polygonize", time: "~0.3s" },
    { step: "4", label: "AI Klassifikation", desc: "Vision API Analyse", time: "~5s" },
    { step: "5", label: "SVG Erzeugung", desc: "FKS-konformes Layout", time: "~0.1s" },
    { step: "6", label: "PDF Export", desc: "WeasyPrint Rendering", time: "~2s" },
  ];

  steps.forEach((s, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 3.1;
    const y = 1.3 + row * 2;

    // Card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.8, h: 1.6,
      fill: { color: C.darkCard },
      shadow: makeShadow(),
    });

    // Step number circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.15, y: y + 0.2, w: 0.45, h: 0.45,
      fill: { color: C.red },
    });
    slide.addText(s.step, {
      x: x + 0.15, y: y + 0.2, w: 0.45, h: 0.45,
      fontSize: 14, fontFace: FONT_BODY, bold: true,
      color: C.white, align: "center", valign: "middle",
    });

    // Label
    slide.addText(s.label, {
      x: x + 0.7, y: y + 0.2, w: 1.9, h: 0.35,
      fontSize: 14, fontFace: FONT_BODY, bold: true,
      color: C.white, margin: 0,
    });
    slide.addText(s.desc, {
      x: x + 0.7, y: y + 0.5, w: 1.9, h: 0.3,
      fontSize: 10, fontFace: FONT_BODY,
      color: C.gray, margin: 0,
    });

    // Time badge
    slide.addText(s.time, {
      x: x + 1.8, y: y + 1.05, w: 0.8, h: 0.35,
      fontSize: 11, fontFace: FONT_BODY, bold: true,
      color: C.gold, align: "center", valign: "middle",
      shape: pres.shapes.ROUNDED_RECTANGLE,
      fill: { color: "292524" },
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 6: AI Room Classification
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addText("AI Raumklassifikation", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.darkBg, margin: 0,
  });

  // Left column: How it works
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.3, w: 4.2, h: 3.7,
    fill: { color: C.white },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.3, w: 4.2, h: 0.06,
    fill: { color: C.gold },
  });

  slide.addText("Wie es funktioniert", {
    x: 1.1, y: 1.5, w: 3.6, h: 0.35,
    fontSize: 16, fontFace: FONT_BODY, bold: true,
    color: C.darkBg, margin: 0,
  });

  const aiSteps = [
    "Grundriss wird als Bild gerendert",
    "Vision API analysiert Raumgeometrien",
    "Heuristik-Fallback bei API-Ausfall",
    "16 Raumtypen werden erkannt",
    "Farbkodierung nach FKS-Standard",
  ];

  aiSteps.forEach((step, i) => {
    slide.addText(step, {
      x: 1.1, y: 2.1 + i * 0.45, w: 3.6, h: 0.35,
      fontSize: 12, fontFace: FONT_BODY, bullet: true,
      color: C.charcoal, margin: 0,
    });
  });

  // Right column: Room types
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.0, h: 3.7,
    fill: { color: C.white },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.0, h: 0.06,
    fill: { color: C.green },
  });

  slide.addText("Erkannte Raumtypen", {
    x: 5.6, y: 1.5, w: 3.4, h: 0.35,
    fontSize: 16, fontFace: FONT_BODY, bold: true,
    color: C.darkBg, margin: 0,
  });

  const roomTypes = [
    { name: "Treppenhaus", color: "006400" },
    { name: "Korridor", color: "90EE90" },
    { name: "Aufzug", color: "B0C4DE" },
    { name: "WC / Nassraum", color: "ADD8E6" },
    { name: "Büro", color: "F0F8FF" },
    { name: "Küche", color: "FFDAB9" },
    { name: "Lager", color: "D2B48C" },
    { name: "Technik", color: "FFB6C1" },
  ];

  roomTypes.forEach((rt, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 5.6 + col * 1.8;
    const y = 2.1 + row * 0.55;

    // Color swatch
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: y + 0.05, w: 0.25, h: 0.25,
      fill: { color: rt.color },
      line: { color: C.charcoal, width: 0.5 },
    });
    slide.addText(rt.name, {
      x: x + 0.35, y, w: 1.3, h: 0.35,
      fontSize: 11, fontFace: FONT_BODY,
      color: C.darkBg, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 7: FKS Compliance
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText("FKS-Richtlinie Konformität", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.white, margin: 0,
  });

  // Compliance checklist
  const compliance = [
    { item: "Farbkodierung Fluchtwege", desc: "Dunkelgrün (vertikal), Hellgrün (horizontal)", status: "check" },
    { item: "Massstabsbalken", desc: "Grafischer Massstabsbalken mit Segmenten", status: "check" },
    { item: "Nordpfeil", desc: "Standardisierter Richtungsanzeiger", status: "check" },
    { item: "Geschosslage", desc: "Querschnitt-Indikator mit aktuellem Geschoss", status: "check" },
    { item: "Legende", desc: "Automatisch generiert aus erkannten Raumtypen", status: "check" },
    { item: "Titelblock", desc: "Objekt, Adresse, Geschoss, Massstab", status: "check" },
    { item: "A3/A4 Papierformat", desc: "Normgerechte Abmessungen und Ränder", status: "check" },
    { item: "FKS Symbole", desc: "Brandmelder, Handfeuermelder, Schlüsseldepot", status: "check" },
  ];

  compliance.forEach((c, i) => {
    const y = 1.2 + i * 0.5;
    // Checkmark
    slide.addText("✓", {
      x: 0.8, y, w: 0.4, h: 0.4,
      fontSize: 16, fontFace: FONT_BODY, bold: true,
      color: C.green, align: "center", valign: "middle",
    });
    slide.addText(c.item, {
      x: 1.3, y, w: 3.5, h: 0.4,
      fontSize: 13, fontFace: FONT_BODY, bold: true,
      color: C.white, valign: "middle", margin: 0,
    });
    slide.addText(c.desc, {
      x: 4.8, y, w: 4.5, h: 0.4,
      fontSize: 11, fontFace: FONT_BODY,
      color: C.gray, valign: "middle", margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 8: UI / Features
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addText("Benutzeroberfläche", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.darkBg, margin: 0,
  });

  // Feature cards in 2x2 grid
  const uiFeatures = [
    { title: "Drag & Drop Upload", desc: "DWG/DXF-Dateien einfach hochladen. Echtzeit-Fortschrittsanzeige während der Verarbeitung.", accent: C.blue },
    { title: "Interaktiver Viewer", desc: "Zoom, Pan und Layer-Toggle im SVG-Viewer. Wände, Türen, Treppen separat ein-/ausblenden.", accent: C.green },
    { title: "Raum-Editor", desc: "AI-Klassifikationen manuell korrigieren. Plan wird sofort mit neuen Zuweisungen regeneriert.", accent: C.gold },
    { title: "Export", desc: "SVG und PDF Download. Performance-Metriken einsehbar (Zeiten pro Pipeline-Schritt).", accent: C.red },
  ];

  uiFeatures.forEach((feat, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.8 + col * 4.5;
    const y = 1.3 + row * 2;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.1, h: 1.7,
      fill: { color: C.white },
      shadow: makeShadow(),
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.07, h: 1.7,
      fill: { color: feat.accent },
    });
    slide.addText(feat.title, {
      x: x + 0.3, y: y + 0.2, w: 3.5, h: 0.35,
      fontSize: 16, fontFace: FONT_BODY, bold: true,
      color: C.darkBg, margin: 0,
    });
    slide.addText(feat.desc, {
      x: x + 0.3, y: y + 0.6, w: 3.5, h: 0.9,
      fontSize: 12, fontFace: FONT_BODY,
      color: C.gray, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 9: Performance Metrics
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText("Leistungsdaten", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.white, margin: 0,
  });

  // Big stat callouts
  const stats = [
    { value: "~13s", label: "Gesamte Pipeline\n(inkl. AI-Klassifikation)", color: C.gold },
    { value: "8/8", label: "Räume korrekt\nklassifiziert", color: C.green },
    { value: "248", label: "Wände erkannt\n(Testgebäude)", color: C.blue },
  ];

  stats.forEach((s, i) => {
    const x = 0.8 + i * 3.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.3, w: 2.8, h: 1.8,
      fill: { color: C.darkCard },
      shadow: makeShadow(),
    });
    slide.addText(s.value, {
      x, y: 1.45, w: 2.8, h: 0.8,
      fontSize: 40, fontFace: FONT_TITLE, bold: true,
      color: s.color, align: "center", valign: "middle",
    });
    slide.addText(s.label, {
      x, y: 2.3, w: 2.8, h: 0.65,
      fontSize: 11, fontFace: FONT_BODY,
      color: C.lightGray, align: "center", valign: "top",
    });
  });

  // Performance breakdown table
  const metrics = [
    ["Pipeline-Schritt", "Dauer"],
    ["DXF Parsing", "~500ms"],
    ["Raumerkennung (Shapely)", "~300ms"],
    ["AI Raumklassifikation", "~5000ms"],
    ["SVG Erzeugung", "~100ms"],
    ["PDF Export", "~2000ms"],
  ];

  slide.addTable(metrics, {
    x: 0.8, y: 3.5, w: 8.4,
    colW: [5, 3.4],
    rowH: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
    border: { pt: 0.5, color: C.charcoal },
    fontSize: 11,
    fontFace: FONT_BODY,
    color: C.lightGray,
    autoPage: false,
  });
}

// ══════════════════════════════════════════════════
// SLIDE 10: Test Results
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addText("Testergebnisse", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.darkBg, margin: 0,
  });

  // Test stats
  const testStats = [
    { value: "33", label: "Unit- & Integrationstests", color: C.green },
    { value: "100%", label: "Bestanden", color: C.green },
    { value: "3", label: "Test-Suiten", color: C.blue },
  ];

  testStats.forEach((s, i) => {
    const x = 0.8 + i * 3.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.2, w: 2.8, h: 1.3,
      fill: { color: C.white },
      shadow: makeShadow(),
    });
    slide.addText(s.value, {
      x, y: 1.25, w: 2.8, h: 0.7,
      fontSize: 36, fontFace: FONT_TITLE, bold: true,
      color: s.color, align: "center", valign: "middle",
    });
    slide.addText(s.label, {
      x, y: 1.95, w: 2.8, h: 0.4,
      fontSize: 11, fontFace: FONT_BODY,
      color: C.gray, align: "center",
    });
  });

  // Test categories
  const categories = [
    { name: "test_dxf_parser.py", tests: "13 Tests", desc: "Layer-Klassifikation, DXF-Parsing, Entity-Extraktion, Fehlerbehandlung" },
    { name: "test_room_detector.py", tests: "8 Tests", desc: "Einzelraum, Mehrraum, Shared Walls, IDs, Flächen, Polygonvalidierung" },
    { name: "test_plan_generator.py", tests: "12 Tests", desc: "SVG-Erzeugung, Raumlabels, FKS-Farben, A3/A4, Titelblock, Integration" },
  ];

  categories.forEach((cat, i) => {
    const y = 2.85 + i * 0.8;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y, w: 8.4, h: 0.65,
      fill: { color: C.white },
      shadow: makeShadow(),
    });
    slide.addText(cat.name, {
      x: 1.0, y, w: 2.5, h: 0.65,
      fontSize: 12, fontFace: "Consolas",
      color: C.darkBg, valign: "middle", margin: 0,
    });
    slide.addText(cat.tests, {
      x: 3.5, y, w: 1.2, h: 0.65,
      fontSize: 12, fontFace: FONT_BODY, bold: true,
      color: C.green, valign: "middle", align: "center",
    });
    slide.addText(cat.desc, {
      x: 4.7, y, w: 4.3, h: 0.65,
      fontSize: 10, fontFace: FONT_BODY,
      color: C.gray, valign: "middle", margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 11: Key Differentiators
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText("Was uns unterscheidet", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.white, margin: 0,
  });

  const diffs = [
    { title: "End-to-End Automatisierung", desc: "Keine manuelle Zwischenschritte - von der CAD-Datei zum fertigen Plan", icon: "→" },
    { title: "Mensch im Regelkreis", desc: "KI klassifiziert, Benutzer korrigiert. Plan wird sofort regeneriert.", icon: "↻" },
    { title: "Normkonform ab Werk", desc: "FKS-Richtlinien sind in die Pipeline eingebaut, nicht nachträglich.", icon: "✓" },
    { title: "Transparent & messbar", desc: "Leistungsmetriken pro Schritt. Jeder Lauf ist reproduzierbar.", icon: "◎" },
  ];

  diffs.forEach((d, i) => {
    const y = 1.2 + i * 1.0;
    // Card
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y, w: 8.4, h: 0.85,
      fill: { color: C.darkCard },
      shadow: makeShadow(),
    });
    // Icon circle
    slide.addShape(pres.shapes.OVAL, {
      x: 1.1, y: y + 0.15, w: 0.55, h: 0.55,
      fill: { color: C.red },
    });
    slide.addText(d.icon, {
      x: 1.1, y: y + 0.15, w: 0.55, h: 0.55,
      fontSize: 16, fontFace: FONT_BODY,
      color: C.white, align: "center", valign: "middle",
    });
    slide.addText(d.title, {
      x: 1.9, y: y + 0.1, w: 6.8, h: 0.35,
      fontSize: 15, fontFace: FONT_BODY, bold: true,
      color: C.white, margin: 0,
    });
    slide.addText(d.desc, {
      x: 1.9, y: y + 0.45, w: 6.8, h: 0.3,
      fontSize: 11, fontFace: FONT_BODY,
      color: C.gray, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 12: Future / Roadmap
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addText("Ausblick", {
    x: 0.8, y: 0.4, w: 8, h: 0.6,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.darkBg, margin: 0,
  });

  const roadmap = [
    { phase: "Phase 1", title: "Multi-Geschoss", desc: "Automatische Erkennung und Verarbeitung aller Stockwerke eines Gebäudes", accent: C.blue },
    { phase: "Phase 2", title: "BIM Integration", desc: "IFC/Revit-Import für noch reichhaltigere Gebäudedaten", accent: C.green },
    { phase: "Phase 3", title: "Fluchtweg-Analyse", desc: "Automatische Berechnung und Markierung optimaler Fluchtwege", accent: C.gold },
    { phase: "Phase 4", title: "SaaS-Plattform", desc: "Cloud-basierte Lösung für Ingenieurbüros und Feuerwehren", accent: C.red },
  ];

  roadmap.forEach((r, i) => {
    const y = 1.2 + i * 1.0;
    // Timeline dot
    slide.addShape(pres.shapes.OVAL, {
      x: 1.0, y: y + 0.15, w: 0.35, h: 0.35,
      fill: { color: r.accent },
    });
    // Timeline line (except last)
    if (i < 3) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 1.15, y: y + 0.5, w: 0.05, h: 0.65,
        fill: { color: C.lightGray },
      });
    }
    // Phase label
    slide.addText(r.phase, {
      x: 1.6, y: y + 0.05, w: 1.2, h: 0.3,
      fontSize: 10, fontFace: FONT_BODY, bold: true,
      color: r.accent, margin: 0,
    });
    // Title
    slide.addText(r.title, {
      x: 1.6, y: y + 0.3, w: 7, h: 0.3,
      fontSize: 16, fontFace: FONT_BODY, bold: true,
      color: C.darkBg, margin: 0,
    });
    // Description
    slide.addText(r.desc, {
      x: 1.6, y: y + 0.6, w: 7, h: 0.3,
      fontSize: 12, fontFace: FONT_BODY,
      color: C.gray, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════
// SLIDE 13: Thank You
// ══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  // Red accent bar at top
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.red },
  });

  // Logo
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.2, y: 1.0, w: 1.0, h: 1.0,
    fill: { color: C.red },
    shadow: makeShadow(),
  });
  slide.addText("RF", {
    x: 4.2, y: 1.0, w: 1.0, h: 1.0,
    fontSize: 32, fontFace: FONT_TITLE, bold: true,
    color: C.white, align: "center", valign: "middle",
  });

  slide.addText("Vielen Dank!", {
    x: 1, y: 2.2, w: 8, h: 0.7,
    fontSize: 40, fontFace: FONT_TITLE, bold: true,
    color: C.white, align: "center",
  });

  slide.addText("Von der CAD-Datei zum FKS-Plan in Sekunden", {
    x: 1, y: 2.9, w: 8, h: 0.5,
    fontSize: 16, fontFace: FONT_BODY, italic: true,
    color: C.gold, align: "center",
  });

  // Divider
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 3.6, w: 3, h: 0.02,
    fill: { color: C.charcoal },
  });

  slide.addText("Fragen?", {
    x: 1, y: 3.8, w: 8, h: 0.5,
    fontSize: 20, fontFace: FONT_BODY,
    color: C.lightGray, align: "center",
  });

  // Footer
  slide.addText("github.com/rescueforge  |  Siemens Hackathon 2025", {
    x: 1, y: 4.8, w: 8, h: 0.4,
    fontSize: 10, fontFace: FONT_BODY,
    color: C.gray, align: "center",
  });
}

// ── Save ──
const outputPath = process.argv[2] || "RescueForge_Presentation.pptx";
pres.writeFile({ fileName: outputPath }).then(() => {
  console.log("Presentation saved to: " + outputPath);
}).catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
