const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// Icon imports
const { FaUpload, FaBuilding, FaBrain, FaFileAlt, FaCheckCircle, FaCog, FaShieldAlt, FaRoute, FaFlask, FaRocket, FaCode, FaDocker, FaFire, FaClipboardCheck } = require("react-icons/fa");
const { MdArchitecture, MdAutoFixHigh, MdSpeed, MdLanguage } = require("react-icons/md");

// ── Color Palette (Fire Safety / Professional) ──
const C = {
  navy:       "1B2838",
  darkNavy:   "0F1923",
  charcoal:   "2C3E50",
  slate:      "34495E",
  fireRed:    "C0392B",
  safetyRed:  "E74C3C",
  escapeGreen:"27AE60",
  lightGreen: "2ECC71",
  dinGreen:   "006400",
  gold:       "F39C12",
  amber:      "E67E22",
  white:      "FFFFFF",
  offWhite:   "F8F9FA",
  lightGray:  "ECF0F1",
  medGray:    "95A5A6",
  darkText:   "2C3E50",
  subtleText: "7F8C8D",
};

function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.2 });
const makeCardShadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.15 });

async function buildPresentation() {
  let pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "RescueForge Team";
  pres.title = "RescueForge - Siemens Hackathon 2025";

  // Pre-render icons
  const icons = {
    upload:    await iconToBase64Png(FaUpload, "#FFFFFF"),
    building:  await iconToBase64Png(FaBuilding, "#FFFFFF"),
    brain:     await iconToBase64Png(FaBrain, "#FFFFFF"),
    file:      await iconToBase64Png(FaFileAlt, "#FFFFFF"),
    check:     await iconToBase64Png(FaCheckCircle, "#27AE60"),
    checkW:    await iconToBase64Png(FaCheckCircle, "#FFFFFF"),
    cog:       await iconToBase64Png(FaCog, "#FFFFFF"),
    shield:    await iconToBase64Png(FaShieldAlt, "#FFFFFF"),
    route:     await iconToBase64Png(FaRoute, "#FFFFFF"),
    flask:     await iconToBase64Png(FaFlask, "#FFFFFF"),
    rocket:    await iconToBase64Png(FaRocket, "#FFFFFF"),
    code:      await iconToBase64Png(FaCode, "#FFFFFF"),
    docker:    await iconToBase64Png(FaDocker, "#FFFFFF"),
    fire:      await iconToBase64Png(FaFire, "#E74C3C"),
    fireW:     await iconToBase64Png(FaFire, "#FFFFFF"),
    clipboard: await iconToBase64Png(FaClipboardCheck, "#FFFFFF"),
    arch:      await iconToBase64Png(MdArchitecture, "#FFFFFF"),
    autofix:   await iconToBase64Png(MdAutoFixHigh, "#FFFFFF"),
    speed:     await iconToBase64Png(MdSpeed, "#FFFFFF"),
    lang:      await iconToBase64Png(MdLanguage, "#FFFFFF"),
  };

  // ══════════════════════════════════════════════════════════════
  // SLIDE 1: Title Slide
  // ══════════════════════════════════════════════════════════════
  let s1 = pres.addSlide();
  s1.background = { color: C.darkNavy };

  // Top accent bar
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.fireRed }
  });

  // Fire icon
  s1.addImage({ data: icons.fire, x: 4.25, y: 0.8, w: 0.7, h: 0.7 });

  // Title
  s1.addText("RescueForge", {
    x: 0.5, y: 1.6, w: 9, h: 1.0,
    fontSize: 48, fontFace: "Arial Black", color: C.white,
    align: "center", bold: true, margin: 0
  });

  // Subtitle
  s1.addText("CAD to DIN 14095 Fire Safety Plans — Powered by AI", {
    x: 0.5, y: 2.6, w: 9, h: 0.5,
    fontSize: 18, fontFace: "Calibri", color: C.medGray,
    align: "center", margin: 0
  });

  // Divider line
  s1.addShape(pres.shapes.LINE, {
    x: 3.5, y: 3.3, w: 3, h: 0,
    line: { color: C.fireRed, width: 2 }
  });

  // Hackathon badge
  s1.addText("Siemens Hackathon 2025  |  Industrial AI Track", {
    x: 0.5, y: 3.6, w: 9, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: C.gold,
    align: "center", bold: true, margin: 0
  });

  // Version
  s1.addText("v0.5.0", {
    x: 0.5, y: 4.2, w: 9, h: 0.35,
    fontSize: 13, fontFace: "Calibri", color: C.medGray,
    align: "center", margin: 0
  });

  // Bottom bar
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.navy }
  });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 2: The Problem
  // ══════════════════════════════════════════════════════════════
  let s2 = pres.addSlide();
  s2.background = { color: C.offWhite };

  // Title bar
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }
  });
  s2.addText("The Challenge", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Problem statement
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 9, h: 1.2,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 0.08, h: 1.2, fill: { color: C.fireRed }
  });
  s2.addText("Fire departments need standardized orientation plans (DIN 14095 / FKS) for every building. Creating these manually from CAD drawings is time-consuming, error-prone, and requires specialized knowledge.", {
    x: 0.85, y: 1.35, w: 8.4, h: 1.1,
    fontSize: 14, fontFace: "Calibri", color: C.darkText, margin: 0
  });

  // Pain points as cards
  const painPoints = [
    { title: "Manual Process", desc: "Hours of work per floor plan", icon: icons.cog },
    { title: "Expert Required", desc: "DIN 14095 knowledge needed", icon: icons.clipboard },
    { title: "Error-Prone", desc: "Missing symbols, wrong colors", icon: icons.shield },
  ];

  for (let i = 0; i < painPoints.length; i++) {
    const x = 0.5 + i * 3.1;
    s2.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 2.85, w: 2.8, h: 2.3,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    // Red top accent
    s2.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 2.85, w: 2.8, h: 0.06, fill: { color: C.safetyRed }
    });
    // Icon circle
    s2.addShape(pres.shapes.OVAL, {
      x: x + 0.95, y: 3.15, w: 0.7, h: 0.7,
      fill: { color: C.safetyRed }
    });
    s2.addImage({ data: painPoints[i].icon, x: x + 1.07, y: 3.27, w: 0.45, h: 0.45 });
    // Title
    s2.addText(painPoints[i].title, {
      x: x + 0.15, y: 4.0, w: 2.5, h: 0.4,
      fontSize: 15, fontFace: "Calibri", color: C.darkText, bold: true, align: "center", margin: 0
    });
    // Description
    s2.addText(painPoints[i].desc, {
      x: x + 0.15, y: 4.4, w: 2.5, h: 0.4,
      fontSize: 12, fontFace: "Calibri", color: C.subtleText, align: "center", margin: 0
    });
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 3: The Solution
  // ══════════════════════════════════════════════════════════════
  let s3 = pres.addSlide();
  s3.background = { color: C.offWhite };

  s3.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }
  });
  s3.addText("Our Solution", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Solution cards - 3 columns
  const solutions = [
    { title: "Upload", desc: "DWG/DXF building plan\nSingle or batch upload", icon: icons.upload, color: C.charcoal },
    { title: "AI Processes", desc: "Automatic cleanup, room\ndetection & classification", icon: icons.brain, color: C.fireRed },
    { title: "DIN 14095 Plan", desc: "FKS-compliant SVG + PDF\nwith all required symbols", icon: icons.file, color: C.escapeGreen },
  ];

  for (let i = 0; i < solutions.length; i++) {
    const x = 0.5 + i * 3.1;
    s3.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.3, w: 2.8, h: 3.8,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    // Color header
    s3.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.3, w: 2.8, h: 1.3, fill: { color: solutions[i].color }
    });
    // Step number
    s3.addText(`Step ${i + 1}`, {
      x: x + 0.15, y: 1.35, w: 2.5, h: 0.35,
      fontSize: 11, fontFace: "Calibri", color: C.white, align: "center", margin: 0, italic: true
    });
    // Icon
    s3.addImage({ data: solutions[i].icon, x: x + 0.95, y: 1.75, w: 0.7, h: 0.7 });
    // Title
    s3.addText(solutions[i].title, {
      x: x + 0.15, y: 2.85, w: 2.5, h: 0.45,
      fontSize: 18, fontFace: "Calibri", color: C.darkText, bold: true, align: "center", margin: 0
    });
    // Description
    s3.addText(solutions[i].desc, {
      x: x + 0.15, y: 3.4, w: 2.5, h: 1.0,
      fontSize: 13, fontFace: "Calibri", color: C.subtleText, align: "center", margin: 0
    });
  }

  // Arrow connectors between cards
  s3.addText("\u2192", { x: 3.15, y: 2.3, w: 0.5, h: 0.5, fontSize: 28, color: C.gold, align: "center", margin: 0 });
  s3.addText("\u2192", { x: 6.25, y: 2.3, w: 0.5, h: 0.5, fontSize: 28, color: C.gold, align: "center", margin: 0 });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 4: Pipeline Architecture
  // ══════════════════════════════════════════════════════════════
  let s4 = pres.addSlide();
  s4.background = { color: C.darkNavy };

  s4.addText("Processing Pipeline", {
    x: 0.5, y: 0.2, w: 9, h: 0.6,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });
  s4.addText("10-step automated pipeline from CAD to DIN 14095 plan", {
    x: 0.5, y: 0.8, w: 9, h: 0.35,
    fontSize: 13, fontFace: "Calibri", color: C.medGray, margin: 0
  });

  // Pipeline steps - 2 rows of 5
  const pipeSteps = [
    { label: "DWG\nConvert", sub: "ODA", color: C.charcoal },
    { label: "DXF\nParse", sub: "ezdxf", color: C.slate },
    { label: "Unit\nDetect", sub: "Heuristic", color: C.charcoal },
    { label: "Room\nDetect", sub: "Shapely", color: C.slate },
    { label: "AI\nClassify", sub: "Gemini", color: C.fireRed },
    { label: "Corridor\nRoute", sub: "Voronoi", color: C.escapeGreen },
    { label: "SVG\nGenerate", sub: "svgwrite", color: C.charcoal },
    { label: "Symbol\nPlace", sub: "Collision", color: C.slate },
    { label: "PDF\nExport", sub: "WeasyPrint", color: C.charcoal },
    { label: "Suppl.\nDocs", sub: "Cover+Sit", color: C.escapeGreen },
  ];

  for (let i = 0; i < 5; i++) {
    const x = 0.3 + i * 1.95;
    // Row 1
    s4.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.4, w: 1.7, h: 1.5,
      fill: { color: pipeSteps[i].color }, shadow: makeCardShadow()
    });
    s4.addText(pipeSteps[i].label, {
      x: x, y: 1.5, w: 1.7, h: 0.8,
      fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
    s4.addText(pipeSteps[i].sub, {
      x: x, y: 2.35, w: 1.7, h: 0.35,
      fontSize: 10, fontFace: "Calibri", color: C.medGray, align: "center", margin: 0, italic: true
    });
    // Arrow between boxes (row 1)
    if (i < 4) {
      s4.addText("\u2192", { x: x + 1.6, y: 1.75, w: 0.4, h: 0.4, fontSize: 18, color: C.gold, align: "center", margin: 0 });
    }
  }

  for (let i = 0; i < 5; i++) {
    const x = 0.3 + i * 1.95;
    const step = pipeSteps[i + 5];
    // Row 2
    s4.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 3.3, w: 1.7, h: 1.5,
      fill: { color: step.color }, shadow: makeCardShadow()
    });
    s4.addText(step.label, {
      x: x, y: 3.4, w: 1.7, h: 0.8,
      fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
    s4.addText(step.sub, {
      x: x, y: 4.25, w: 1.7, h: 0.35,
      fontSize: 10, fontFace: "Calibri", color: C.medGray, align: "center", margin: 0, italic: true
    });
    if (i < 4) {
      s4.addText("\u2192", { x: x + 1.6, y: 3.65, w: 0.4, h: 0.4, fontSize: 18, color: C.gold, align: "center", margin: 0 });
    }
  }

  // Connecting arrow between rows
  s4.addText("\u2193", { x: 4.7, y: 2.85, w: 0.5, h: 0.4, fontSize: 20, color: C.gold, align: "center", margin: 0 });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 5: AI Classification
  // ══════════════════════════════════════════════════════════════
  let s5 = pres.addSlide();
  s5.background = { color: C.offWhite };

  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }
  });
  s5.addText("AI-Powered Room Classification", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 28, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Left: How it works
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.5, h: 3.9,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s5.addText("How It Works", {
    x: 0.75, y: 1.4, w: 4, h: 0.4,
    fontSize: 18, fontFace: "Calibri", color: C.darkText, bold: true, margin: 0
  });

  const aiSteps = [
    "Floor plan rendered as PNG with numbered rooms",
    "Image sent to Vision API (Gemini 2.5 Flash)",
    "AI returns room type + label for each room",
    "Automatic retry (3x) on API failure",
    "Heuristic fallback if AI unavailable"
  ];
  const aiStepTexts = aiSteps.map((s, i) => ({
    text: `${i + 1}.  ${s}`,
    options: { breakLine: true, fontSize: 13, color: C.darkText, paraSpaceAfter: 6 }
  }));
  s5.addText(aiStepTexts, {
    x: 0.75, y: 1.9, w: 4, h: 3.0,
    fontFace: "Calibri", margin: 0
  });

  // Right: Room types
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.2, h: 3.9,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s5.addText("17 Room Types", {
    x: 5.55, y: 1.4, w: 3.7, h: 0.4,
    fontSize: 18, fontFace: "Calibri", color: C.darkText, bold: true, margin: 0
  });

  const roomTypes = [
    "Office, Corridor, Stairwell",
    "Elevator, Bathroom, Kitchen",
    "Storage, Technical, Server Room",
    "Garage, Lobby, Conference",
    "Residential, Bedroom, Living Room",
    "Balcony, Unknown"
  ];
  const roomTexts = roomTypes.map((r, i) => ({
    text: r,
    options: { breakLine: true, fontSize: 12, color: C.subtleText, bullet: true, paraSpaceAfter: 5 }
  }));
  s5.addText(roomTexts, {
    x: 5.55, y: 1.9, w: 3.7, h: 3.0,
    fontFace: "Calibri", margin: 0
  });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 6: DIN 14095 Compliance
  // ══════════════════════════════════════════════════════════════
  let s6 = pres.addSlide();
  s6.background = { color: C.offWhite };

  s6.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.fireRed }
  });
  s6.addImage({ data: icons.fireW, x: 0.5, y: 0.2, w: 0.5, h: 0.5 });
  s6.addText("DIN 14095 / FKS Compliance", {
    x: 1.1, y: 0.15, w: 8, h: 0.7,
    fontSize: 28, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Compliance features in 2x3 grid
  const compliance = [
    { title: "Filled Walls", desc: "Double-line polygons\nRAL 9004 Signalschwarz" },
    { title: "Fire Walls", desc: "RAL 3000 Feuerrot\n2x normal thickness" },
    { title: "18 FKS Symbols", desc: "DIN 14034-6 compliant\nSmoke, call, exits, etc." },
    { title: "Escape Routes", desc: "Corridor centerline routing\nVoronoi + NetworkX" },
    { title: "DIN Title Block", desc: "ISO 7200 layout\nScale, date, references" },
    { title: "Color Coding", desc: "RAL standard colors\nGreen corridors, red fire" },
  ];

  for (let row = 0; row < 2; row++) {
    for (let col = 0; col < 3; col++) {
      const i = row * 3 + col;
      const x = 0.5 + col * 3.1;
      const y = 1.25 + row * 2.1;
      s6.addShape(pres.shapes.RECTANGLE, {
        x: x, y: y, w: 2.8, h: 1.8,
        fill: { color: C.white }, shadow: makeCardShadow()
      });
      s6.addShape(pres.shapes.RECTANGLE, {
        x: x, y: y, w: 2.8, h: 0.06, fill: { color: C.escapeGreen }
      });
      s6.addImage({ data: icons.check, x: x + 0.15, y: y + 0.2, w: 0.35, h: 0.35 });
      s6.addText(compliance[i].title, {
        x: x + 0.55, y: y + 0.2, w: 2.1, h: 0.35,
        fontSize: 14, fontFace: "Calibri", color: C.darkText, bold: true, margin: 0
      });
      s6.addText(compliance[i].desc, {
        x: x + 0.15, y: y + 0.7, w: 2.5, h: 0.9,
        fontSize: 11, fontFace: "Calibri", color: C.subtleText, margin: 0
      });
    }
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 7: Key Algorithms
  // ══════════════════════════════════════════════════════════════
  let s7 = pres.addSlide();
  s7.background = { color: C.darkNavy };

  s7.addText("Key Algorithms", {
    x: 0.5, y: 0.2, w: 9, h: 0.6,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  const algorithms = [
    { title: "Voronoi Medial Axis", desc: "SciPy Voronoi on corridor boundary points. Filter ridges inside polygon to extract centerline for escape routes.", icon: icons.route },
    { title: "Unit Auto-Detection", desc: "Try all unit conversions, pick one giving 5-500m building size. Corrects wrong $INSUNITS headers.", icon: icons.autofix },
    { title: "Symbol Collision Avoidance", desc: "AABB overlap detection with 4-direction shift. Label-aware placement prevents overlapping in small rooms.", icon: icons.shield },
    { title: "Door Deduplication", desc: "Merge arc + layer + INSERT + wall-gap detections. Sort by position, merge within tolerance, prefer standard widths.", icon: icons.cog },
  ];

  for (let i = 0; i < algorithms.length; i++) {
    const y = 1.05 + i * 1.1;
    s7.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 9, h: 0.95,
      fill: { color: C.navy }, shadow: makeCardShadow()
    });
    s7.addShape(pres.shapes.OVAL, {
      x: 0.7, y: y + 0.15, w: 0.6, h: 0.6,
      fill: { color: C.fireRed }
    });
    s7.addImage({ data: algorithms[i].icon, x: 0.82, y: y + 0.27, w: 0.35, h: 0.35 });
    s7.addText(algorithms[i].title, {
      x: 1.5, y: y + 0.1, w: 7.8, h: 0.35,
      fontSize: 15, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    s7.addText(algorithms[i].desc, {
      x: 1.5, y: y + 0.45, w: 7.8, h: 0.4,
      fontSize: 11, fontFace: "Calibri", color: C.medGray, margin: 0
    });
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 8: Tech Stack
  // ══════════════════════════════════════════════════════════════
  let s8 = pres.addSlide();
  s8.background = { color: C.offWhite };

  s8.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }
  });
  s8.addText("Tech Stack", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Left column - Backend
  s8.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.3, h: 4.0,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s8.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.3, h: 0.5, fill: { color: C.charcoal }
  });
  s8.addText("Backend", {
    x: 0.7, y: 1.32, w: 3.8, h: 0.45,
    fontSize: 16, fontFace: "Calibri", color: C.white, bold: true, margin: 0
  });

  const backendStack = [
    "Python 3.12 + FastAPI",
    "ezdxf (CAD parsing)",
    "ODA File Converter (DWG)",
    "Shapely + STRtree (geometry)",
    "SciPy Voronoi + NetworkX",
    "OpenRouter API (Gemini 2.5 Flash)",
    "svgwrite + WeasyPrint",
    "ThreadPoolExecutor + JobStore",
  ];
  const bTexts = backendStack.map((t) => ({
    text: t, options: { bullet: true, breakLine: true, fontSize: 12, color: C.darkText, paraSpaceAfter: 4 }
  }));
  s8.addText(bTexts, { x: 0.8, y: 1.95, w: 3.7, h: 3.2, fontFace: "Calibri", margin: 0 });

  // Right column - Frontend + Infra
  s8.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.3, h: 4.0,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s8.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.3, h: 0.5, fill: { color: C.escapeGreen }
  });
  s8.addText("Frontend & Infrastructure", {
    x: 5.4, y: 1.32, w: 3.8, h: 0.45,
    fontSize: 16, fontFace: "Calibri", color: C.white, bold: true, margin: 0
  });

  const frontendStack = [
    "Next.js 15 + React 19",
    "Tailwind CSS + lucide-react",
    "WebSocket + HTTP polling fallback",
    "Cypress E2E tests",
    "Docker Compose (non-root)",
    "GitHub Actions CI/CD",
    "Coolify deployment",
    "EN/DE i18n (localStorage)",
  ];
  const fTexts = frontendStack.map((t) => ({
    text: t, options: { bullet: true, breakLine: true, fontSize: 12, color: C.darkText, paraSpaceAfter: 4 }
  }));
  s8.addText(fTexts, { x: 5.5, y: 1.95, w: 3.7, h: 3.2, fontFace: "Calibri", margin: 0 });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 9: Features Overview
  // ══════════════════════════════════════════════════════════════
  let s9 = pres.addSlide();
  s9.background = { color: C.darkNavy };

  s9.addText("Features", {
    x: 0.5, y: 0.2, w: 9, h: 0.6,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  const features = [
    { title: "Interactive Room Editor", desc: "Reclassify rooms, regenerate plans instantly", icon: icons.arch },
    { title: "Batch Upload", desc: "Process multi-floor buildings at once", icon: icons.upload },
    { title: "Real-Time Progress", desc: "WebSocket updates with auto HTTP fallback", icon: icons.speed },
    { title: "Multi-Language", desc: "Full EN/DE support, German as default", icon: icons.lang },
    { title: "Comparison View", desc: "Side-by-side original DXF vs FKS plan", icon: icons.autofix },
    { title: "Complete Plan Set", desc: "Floor plan + cover sheet + situation plan + compliance report", icon: icons.file },
  ];

  for (let row = 0; row < 2; row++) {
    for (let col = 0; col < 3; col++) {
      const i = row * 3 + col;
      const x = 0.3 + col * 3.2;
      const y = 1.05 + row * 2.2;

      s9.addShape(pres.shapes.RECTANGLE, {
        x: x, y: y, w: 2.95, h: 1.9,
        fill: { color: C.navy }, shadow: makeCardShadow()
      });

      // Icon circle
      s9.addShape(pres.shapes.OVAL, {
        x: x + 0.15, y: y + 0.2, w: 0.55, h: 0.55,
        fill: { color: C.fireRed }
      });
      s9.addImage({ data: features[i].icon, x: x + 0.25, y: y + 0.3, w: 0.35, h: 0.35 });

      s9.addText(features[i].title, {
        x: x + 0.85, y: y + 0.15, w: 1.9, h: 0.55,
        fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, margin: 0
      });
      s9.addText(features[i].desc, {
        x: x + 0.15, y: y + 0.95, w: 2.6, h: 0.7,
        fontSize: 11, fontFace: "Calibri", color: C.medGray, margin: 0
      });
    }
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 10: Testing & Quality
  // ══════════════════════════════════════════════════════════════
  let s10 = pres.addSlide();
  s10.background = { color: C.offWhite };

  s10.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }
  });
  s10.addText("Testing & Quality Assurance", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 28, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Big stats
  const stats = [
    { num: "328+", label: "Backend Tests" },
    { num: "19", label: "Test Suites" },
    { num: "E2E", label: "Cypress Tests" },
  ];
  for (let i = 0; i < stats.length; i++) {
    const x = 0.5 + i * 3.1;
    s10.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.25, w: 2.8, h: 1.3,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    s10.addText(stats[i].num, {
      x: x, y: 1.3, w: 2.8, h: 0.7,
      fontSize: 36, fontFace: "Arial Black", color: C.fireRed, bold: true, align: "center", margin: 0
    });
    s10.addText(stats[i].label, {
      x: x, y: 2.05, w: 2.8, h: 0.35,
      fontSize: 13, fontFace: "Calibri", color: C.subtleText, align: "center", margin: 0
    });
  }

  // Test types table
  s10.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.85, w: 9, h: 2.5,
    fill: { color: C.white }, shadow: makeCardShadow()
  });

  const testRows = [
    [
      { text: "Test Category", options: { bold: true, color: C.white, fill: { color: C.charcoal }, fontSize: 11 } },
      { text: "Coverage", options: { bold: true, color: C.white, fill: { color: C.charcoal }, fontSize: 11 } },
    ],
    [
      { text: "Plan Generator (50 tests)", options: { fontSize: 10 } },
      { text: "SVG output, DIN title block, walls, fire features, escape routes, languages", options: { fontSize: 10 } },
    ],
    [
      { text: "DXF Parser (39 tests)", options: { fontSize: 10 } },
      { text: "Layer classification, multilingual (EN/DE/FR/ES/VI), fire safety patterns", options: { fontSize: 10 } },
    ],
    [
      { text: "Visual Regression (24 tests)", options: { fontSize: 10 } },
      { text: "SVG fingerprint baselines + CairoSVG pixel-based comparison (7 scenarios)", options: { fontSize: 10 } },
    ],
    [
      { text: "API Routes (44 tests)", options: { fontSize: 10 } },
      { text: "Upload, batch, status, download, metrics, room update, error endpoints", options: { fontSize: 10 } },
    ],
    [
      { text: "Corridor Routing (8 tests)", options: { fontSize: 10 } },
      { text: "Voronoi medial axis, corridor graph, NetworkX pathfinding", options: { fontSize: 10 } },
    ],
  ];

  s10.addTable(testRows, {
    x: 0.7, y: 2.95, w: 8.6,
    colW: [3.0, 5.6],
    border: { pt: 0.5, color: C.lightGray },
    rowH: [0.32, 0.32, 0.32, 0.32, 0.32, 0.32],
    fontFace: "Calibri",
    color: C.darkText,
  });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 11: Performance
  // ══════════════════════════════════════════════════════════════
  let s11 = pres.addSlide();
  s11.background = { color: C.offWhite };

  s11.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }
  });
  s11.addText("Performance & Architecture", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 28, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  // Left: Performance bar chart
  s11.addChart(pres.charts.BAR, [{
    name: "Duration (ms)",
    labels: ["DXF Parse", "Room Detect", "AI Classify", "SVG Generate", "PDF Export", "Supplementary"],
    values: [500, 300, 5000, 100, 2000, 20]
  }], {
    x: 0.5, y: 1.2, w: 5.0, h: 3.5,
    barDir: "bar",
    showTitle: true,
    title: "Pipeline Duration (~12s total)",
    titleColor: C.darkText,
    titleFontSize: 13,
    chartColors: [C.fireRed],
    chartArea: { fill: { color: C.white }, roundedCorners: true },
    catAxisLabelColor: C.darkText,
    catAxisLabelFontSize: 10,
    valAxisLabelColor: C.subtleText,
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.darkText,
    dataLabelFontSize: 9,
    showLegend: false,
    shadow: makeCardShadow(),
  });

  // Right: Architecture diagram
  s11.addShape(pres.shapes.RECTANGLE, {
    x: 5.8, y: 1.2, w: 3.8, h: 3.5,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s11.addText("2-Service Architecture", {
    x: 6.0, y: 1.35, w: 3.4, h: 0.35,
    fontSize: 15, fontFace: "Calibri", color: C.darkText, bold: true, margin: 0
  });

  // Frontend box
  s11.addShape(pres.shapes.RECTANGLE, {
    x: 6.2, y: 1.9, w: 3.2, h: 0.7, fill: { color: C.escapeGreen }
  });
  s11.addText("Frontend (Next.js 15)\nPort 3000", {
    x: 6.2, y: 1.9, w: 3.2, h: 0.7,
    fontSize: 11, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
  });

  // Arrow
  s11.addText("\u2195 HTTP/WS", {
    x: 6.2, y: 2.65, w: 3.2, h: 0.35,
    fontSize: 10, fontFace: "Calibri", color: C.subtleText, align: "center", margin: 0
  });

  // Backend box
  s11.addShape(pres.shapes.RECTANGLE, {
    x: 6.2, y: 3.05, w: 3.2, h: 0.7, fill: { color: C.charcoal }
  });
  s11.addText("Backend (FastAPI)\nThreadPool + JobStore", {
    x: 6.2, y: 3.05, w: 3.2, h: 0.7,
    fontSize: 11, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
  });

  // Docker note
  s11.addText("Docker Compose  |  Non-root  |  Coolify Deploy", {
    x: 6.0, y: 3.95, w: 3.4, h: 0.5,
    fontSize: 9, fontFace: "Calibri", color: C.subtleText, align: "center", margin: 0
  });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 12: Security
  // ══════════════════════════════════════════════════════════════
  let s12 = pres.addSlide();
  s12.background = { color: C.darkNavy };

  s12.addText("Security & Reliability", {
    x: 0.5, y: 0.2, w: 9, h: 0.6,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  const secFeatures = [
    { title: "Security Headers", desc: "X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy" },
    { title: "Rate Limiting", desc: "20 req/60s per IP on upload endpoints, auto memory cleanup" },
    { title: "Input Validation", desc: "Only .dwg/.dxf accepted, UUID job IDs, room type enum checks" },
    { title: "CORS Configuration", desc: "Configurable origins, credentials only with explicit origins" },
    { title: "Error Persistence", desc: "Detailed error.json on failure with step, elapsed time, error type" },
    { title: "Non-Root Containers", desc: "Production-hardened Docker with dedicated app user (UID 1000)" },
  ];

  for (let i = 0; i < secFeatures.length; i++) {
    const y = 1.0 + i * 0.72;
    s12.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 9, h: 0.62,
      fill: { color: C.navy }
    });
    s12.addImage({ data: icons.checkW, x: 0.7, y: y + 0.12, w: 0.35, h: 0.35 });
    s12.addText(secFeatures[i].title, {
      x: 1.2, y: y + 0.05, w: 2.5, h: 0.5,
      fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    s12.addText(secFeatures[i].desc, {
      x: 3.8, y: y + 0.05, w: 5.5, h: 0.5,
      fontSize: 12, fontFace: "Calibri", color: C.medGray, margin: 0
    });
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 13: Hackathon Deliverables
  // ══════════════════════════════════════════════════════════════
  let s13 = pres.addSlide();
  s13.background = { color: C.offWhite };

  s13.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.escapeGreen }
  });
  s13.addText("Hackathon Deliverables", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 28, fontFace: "Arial Black", color: C.white, bold: true, margin: 0
  });

  const deliverables = [
    "Working prototype (Docker Compose, live at resuceforge.skimu.de)",
    "AI-powered room classification (Gemini 2.5 Flash Vision API)",
    "DIN 14095 / FKS-compliant plan output (SVG + PDF)",
    "Complete plan set: Floor plan + Cover sheet + Situation plan + Compliance report",
    "Interactive room editor with live regeneration",
    "Batch upload for multi-floor processing",
    "328+ automated tests (19 suites) + Cypress E2E",
    "CI/CD pipeline (GitHub Actions)",
    "Multi-language support (EN/DE)",
    "Corridor-centerline escape routes (Voronoi + NetworkX)",
    "Symbol collision avoidance + fire safety element recognition",
    "DIN-standard scale detection (1:50 to 1:1000)",
  ];

  const delivTexts = deliverables.map((d) => ({
    text: d,
    options: { bullet: true, breakLine: true, fontSize: 12, color: C.darkText, paraSpaceAfter: 3 }
  }));
  s13.addText(delivTexts, {
    x: 0.8, y: 1.2, w: 8.4, h: 4.2,
    fontFace: "Calibri", margin: 0
  });

  // ══════════════════════════════════════════════════════════════
  // SLIDE 14: Closing
  // ══════════════════════════════════════════════════════════════
  let s14 = pres.addSlide();
  s14.background = { color: C.darkNavy };

  // Top accent
  s14.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.fireRed }
  });

  s14.addImage({ data: icons.fire, x: 4.25, y: 0.8, w: 0.7, h: 0.7 });

  s14.addText("RescueForge", {
    x: 0.5, y: 1.6, w: 9, h: 0.8,
    fontSize: 44, fontFace: "Arial Black", color: C.white, bold: true, align: "center", margin: 0
  });

  s14.addText("From CAD to Fire Safety Plan in Seconds", {
    x: 0.5, y: 2.4, w: 9, h: 0.5,
    fontSize: 18, fontFace: "Calibri", color: C.medGray, align: "center", italic: true, margin: 0
  });

  s14.addShape(pres.shapes.LINE, {
    x: 3.5, y: 3.1, w: 3, h: 0,
    line: { color: C.fireRed, width: 2 }
  });

  // Links
  s14.addText([
    { text: "github.com/NWichter-NeoTube/RescueForge", options: { breakLine: true, fontSize: 14, color: C.gold } },
    { text: "resuceforge.skimu.de", options: { fontSize: 14, color: C.gold } },
  ], {
    x: 0.5, y: 3.4, w: 9, h: 1.0,
    fontFace: "Calibri", align: "center", margin: 0
  });

  s14.addText("Siemens Hackathon 2025  |  Industrial AI Track", {
    x: 0.5, y: 4.5, w: 9, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.subtleText, align: "center", margin: 0
  });

  // Bottom bar
  s14.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.navy }
  });

  // ── Save ──
  const outPath = "RescueForge_Final.pptx";
  await pres.writeFile({ fileName: outPath });
  console.log(`Presentation saved: ${outPath}`);
}

buildPresentation().catch(console.error);
