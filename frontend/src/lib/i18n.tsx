"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type Locale = "en" | "de";

const translations = {
  // Header
  "app.subtitle": { en: "CAD to Fire Department Orientation Plans", de: "CAD zu Feuerwehr-Orientierungsplänen" },
  "app.badge": { en: "FKS Compliant", de: "FKS-konform" },
  "darkMode.light": { en: "Switch to light mode", de: "Zu hellem Modus wechseln" },
  "darkMode.dark": { en: "Switch to dark mode", de: "Zu dunklem Modus wechseln" },

  // Upload section
  "upload.title": { en: "Upload Building Plan", de: "Gebäudeplan hochladen" },
  "upload.description": {
    en: "Upload a CAD building plan (DWG/DXF) and automatically receive a standards-compliant fire department orientation plan.",
    de: "Laden Sie einen CAD-Gebäudeplan (DWG/DXF) hoch und erhalten Sie automatisch einen normkonformen Feuerwehr-Orientierungsplan.",
  },
  "upload.dropzone.aria": { en: "Upload DWG or DXF file via drag & drop or click", de: "DWG oder DXF Datei hochladen per Drag & Drop oder Klick" },
  "upload.dropzone.active": { en: "Drop file here...", de: "Datei hier ablegen..." },
  "upload.dropzone.text": { en: "Drag DWG or DXF file here", de: "DWG oder DXF Datei hierher ziehen" },
  "upload.dropzone.hint": { en: "or click to select (max. 50 MB)", de: "oder klicken zum Auswählen (max. 50 MB)" },
  "upload.dropzone.multi": { en: " — multiple files for floor processing", de: " — mehrere Dateien für Geschossverarbeitung" },
  "upload.failed": { en: "Upload failed", de: "Upload fehlgeschlagen" },
  "upload.batchFailed": { en: "Batch upload failed", de: "Batch-Upload fehlgeschlagen" },
  "upload.allFailed": { en: "All files could not be processed", de: "Alle Dateien konnten nicht verarbeitet werden" },

  // Features
  "feature.cleanup.title": { en: "Automatic Cleanup", de: "Automatische Bereinigung" },
  "feature.cleanup.desc": { en: "Removes irrelevant layers such as furniture and dimensions", de: "Entfernt irrelevante Layer wie Möbel und Vermassung" },
  "feature.ai.title": { en: "AI Room Classification", de: "AI Raumklassifikation" },
  "feature.ai.desc": { en: "Detects and classifies rooms automatically", de: "Erkennt und klassifiziert Räume automatisch" },
  "feature.fks.title": { en: "FKS Compliant", de: "FKS-konform" },
  "feature.fks.desc": { en: "Output according to Swiss guideline for orientation plans", de: "Ausgabe nach Schweizer Richtlinie für Orientierungspläne" },

  // Progress
  "progress.queued": { en: "Queued...", de: "In Warteschlange..." },
  "progress.dwg": { en: "Converting DWG...", de: "DWG wird konvertiert..." },
  "progress.dxf": { en: "Analyzing DXF...", de: "DXF wird analysiert..." },
  "progress.rooms": { en: "Detecting rooms...", de: "Räume werden erkannt..." },
  "progress.classify": { en: "AI classifying rooms...", de: "AI klassifiziert Räume..." },
  "progress.svg": { en: "Generating orientation plan...", de: "Orientierungsplan wird erstellt..." },
  "progress.pdf": { en: "Exporting PDF...", de: "PDF wird exportiert..." },
  "progress.done": { en: "Done!", de: "Fertig!" },
  "progress.error": { en: "Error occurred", de: "Fehler aufgetreten" },
  "progress.processing": { en: "Processing...", de: "Verarbeitung..." },
  "progress.batch": { en: "Batch Processing", de: "Batch-Verarbeitung" },

  // Plan viewer
  "plan.title": { en: "Orientation Plan", de: "Orientierungsplan" },
  "plan.tab.floor": { en: "Floor Plan", de: "Geschossplan" },
  "plan.tab.cover": { en: "Cover Sheet", de: "Deckblatt" },
  "plan.tab.situation": { en: "Situation Plan", de: "Situationsplan" },
  "plan.tab.compare": { en: "Comparison", de: "Vergleich" },
  "plan.newPlan": { en: "New Plan", de: "Neuer Plan" },
  "plan.newPlan.aria": { en: "Create new plan", de: "Neuen Plan erstellen" },
  "plan.selectFloor": { en: "Select floor", de: "Geschoss auswählen" },
  "plan.loading": { en: "Loading plan...", de: "Plan wird geladen..." },
  "plan.svgError": { en: "Failed to load SVG", de: "SVG konnte nicht geladen werden" },
  "plan.networkError": { en: "Network error", de: "Netzwerkfehler" },
  "plan.zoomHint": { en: "Scroll to zoom, click and drag to pan", de: "Mausrad zum Zoomen, Klicken+Ziehen zum Verschieben" },

  // Cover sheet / Situation plan
  "cover.title": { en: "Cover Sheet", de: "Deckblatt" },
  "cover.desc": { en: "FKS cover sheet with object definition, complete legend and symbol reference", de: "FKS-Deckblatt mit Objektdefinition, vollständiger Legende und Symbolreferenz" },
  "situation.title": { en: "Situation Plan", de: "Situationsplan" },
  "situation.desc": { en: "Building outline with labeled sides (A-D), fire department access route and north arrow", de: "Gebäudeumriss mit beschrifteten Seiten (A-D), Feuerwehrzufahrt und Nordpfeil" },

  // Comparison view
  "compare.loading": { en: "Loading comparison view...", de: "Vergleichsansicht wird geladen..." },
  "compare.original": { en: "Original (DXF)", de: "Original (DXF)" },
  "compare.generated": { en: "FKS Orientation Plan", de: "FKS-Orientierungsplan" },
  "compare.unavailable": { en: "Not available", de: "Nicht verfügbar" },

  // Supplementary viewer
  "supp.loading": { en: "Loading {title}...", de: "{title} wird geladen..." },
  "supp.error": { en: "{title} not available", de: "{title} nicht verfügbar" },
  "supp.download": { en: "Download SVG", de: "SVG herunterladen" },
  "supp.noPreview": { en: "No preview available", de: "Keine Vorschau verfügbar" },
  "supp.loadFailed": { en: "Loading failed", de: "Laden fehlgeschlagen" },

  // Layers
  "layer.title": { en: "Layers", de: "Ebenen" },
  "layer.rooms": { en: "Rooms", de: "Räume" },
  "layer.walls": { en: "Walls", de: "Wände" },
  "layer.doors": { en: "Doors", de: "Türen" },
  "layer.stairs": { en: "Stairs", de: "Treppen" },

  // Room editor
  "rooms.title": { en: "Rooms", de: "Räume" },
  "rooms.save": { en: "Save", de: "Speichern" },
  "rooms.saving": { en: "Saving...", de: "Speichern..." },
  "rooms.loading": { en: "Loading room data...", de: "Raumdaten werden geladen..." },
  "rooms.saved": { en: "Room classification saved, regenerating plan", de: "Raumklassifikation gespeichert, Plan wird neu generiert" },
  "rooms.saveError": { en: "Error saving room data", de: "Fehler beim Speichern der Raumdaten" },

  // Room types
  "room.office": { en: "Office", de: "Büro" },
  "room.corridor": { en: "Corridor", de: "Korridor" },
  "room.stairwell": { en: "Stairwell", de: "Treppenhaus" },
  "room.elevator": { en: "Elevator", de: "Aufzug" },
  "room.bathroom": { en: "Bathroom", de: "WC" },
  "room.kitchen": { en: "Kitchen", de: "Küche" },
  "room.storage": { en: "Storage", de: "Lager" },
  "room.technical": { en: "Technical", de: "Technik" },
  "room.garage": { en: "Garage", de: "Garage" },
  "room.lobby": { en: "Lobby / Reception", de: "Halle/Empfang" },
  "room.conference": { en: "Conference Room", de: "Sitzungszimmer" },
  "room.residential": { en: "Residential", de: "Wohnraum" },
  "room.bedroom": { en: "Bedroom", de: "Schlafzimmer" },
  "room.living_room": { en: "Living Room", de: "Wohnzimmer" },
  "room.balcony": { en: "Balcony", de: "Balkon" },
  "room.unknown": { en: "Unknown", de: "Unbekannt" },

  // Export
  "export.button": { en: "Export", de: "Exportieren" },
  "export.floorPlan": { en: "Floor Plan", de: "Geschossplan" },
  "export.svgLabel": { en: "Orientation Plan (SVG)", de: "Orientierungsplan (SVG)" },
  "export.pdfLabel": { en: "Orientation Plan (PDF)", de: "Orientierungsplan (PDF)" },
  "export.supplementary": { en: "FKS Supplementary Plans", de: "FKS-Zusatzpläne" },
  "export.coverSvg": { en: "Cover Sheet (SVG)", de: "Deckblatt (SVG)" },
  "export.situationSvg": { en: "Situation Plan (SVG)", de: "Situationsplan (SVG)" },

  // Metrics
  "metrics.title": { en: "Performance", de: "Leistung" },
  "metrics.unavailable": { en: "Metrics not available", de: "Metriken nicht verfügbar" },
  "metrics.dxfParsing": { en: "DXF Parsing", de: "DXF Analyse" },
  "metrics.roomDetection": { en: "Room Detection", de: "Raumerkennung" },
  "metrics.aiClassification": { en: "AI Classification", de: "AI Klassifikation" },
  "metrics.svgGeneration": { en: "SVG Generation", de: "SVG Erzeugung" },
  "metrics.pdfExport": { en: "PDF Export", de: "PDF Export" },
  "metrics.total": { en: "Total", de: "Gesamt" },
  "metrics.walls": { en: "Walls", de: "Wände" },
  "metrics.doors": { en: "Doors", de: "Türen" },
  "metrics.rooms": { en: "Rooms", de: "Räume" },
  "metrics.detected": { en: "detected", de: "erkannt" },
  "metrics.classified": { en: "classified", de: "klassifiziert" },

  // Error
  "error.title": { en: "An error occurred", de: "Ein Fehler ist aufgetreten" },
  "error.unknown": { en: "Unknown error", de: "Unbekannter Fehler" },
  "error.retry": { en: "Try Again", de: "Erneut versuchen" },
  "error.close": { en: "Close error message", de: "Fehlermeldung schließen" },

  // Keyboard shortcuts
  "shortcut.svgDownload": { en: "SVG download started (Ctrl+S)", de: "SVG-Download gestartet (Ctrl+S)" },
  "shortcut.pdfDownload": { en: "PDF download started (Ctrl+P)", de: "PDF-Download gestartet (Ctrl+P)" },

  // Toast
  "toast.close": { en: "Close notification", de: "Benachrichtigung schließen" },

  // API messages
  "api.complete": { en: "Processing completed", de: "Verarbeitung abgeschlossen" },
  "api.failed": { en: "Processing failed", de: "Verarbeitung fehlgeschlagen" },
} as const;

export type TranslationKey = keyof typeof translations;

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, replacements?: Record<string, string>) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("rescueforge-locale");
      if (saved === "en" || saved === "de") return saved;
    }
    return "de";
  });

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") {
      localStorage.setItem("rescueforge-locale", l);
    }
  }, []);

  const t = useCallback(
    (key: TranslationKey, replacements?: Record<string, string>): string => {
      const entry = translations[key];
      if (!entry) return key;
      let text: string = entry[locale] || entry.en;
      if (replacements) {
        for (const [k, v] of Object.entries(replacements)) {
          text = text.replace(`{${k}}`, v);
        }
      }
      return text;
    },
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
