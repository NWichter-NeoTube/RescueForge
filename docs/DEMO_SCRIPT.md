# RescueForge Demo Script

Empfohlene Dauer: **3-5 Minuten**

---

## Szene 1: Intro (30s)

**Zeigen:** Landing Page mit Upload-Bereich

**Sagen:**
> "RescueForge konvertiert CAD-Gebäudepläne automatisch in normkonforme Feuerwehr-Orientierungspläne nach Schweizer FKS-Richtlinie.
> Der gesamte Prozess dauert unter 15 Sekunden."

---

## Szene 2: Upload + Pipeline (30s)

**Aktion:** DXF-Datei per Drag & Drop hochladen (`testdata/office_building.dxf`)

**Zeigen:** Echtzeit-Fortschrittsbalken mit Pipeline-Schritten

**Sagen:**
> "Wir laden einen DXF-Gebäudeplan hoch. Die Pipeline läuft automatisch:
> DXF-Parsing, Raumerkennung via Shapely, AI-Raumklassifikation via Vision API,
> SVG-Generierung und PDF-Export."

---

## Szene 3: Geschossplan (45s)

**Zeigen:** Fertiger Orientierungsplan im Viewer

**Hervorheben:**
- Raumpolygone mit Farbkodierung (Büro, Korridor, Treppenhaus)
- Grüne Fluchtwege (graph-basiert, nicht Luftlinie)
- Rote Gefahrenbereiche (Technik-Räume)
- FKS-Symbole (Nordpfeil, Massstabsbalken, Geschosslage)
- Legende mit allen erkannten Raumtypen
- Titelblock

**Sagen:**
> "Der generierte Plan ist FKS-konform: Fluchtwege werden graph-basiert berechnet,
> Gefahrenbereiche rot markiert, alle FKS-Symbole automatisch platziert."

---

## Szene 4: Deckblatt + Situationsplan (30s)

**Aktion:** Tab "Deckblatt" klicken

**Zeigen:** Cover Sheet mit Legende und Symbolreferenz

**Aktion:** Tab "Situationsplan" klicken

**Zeigen:** Gebäudeumriss mit Seiten A-D, Feuerwehrzufahrt

**Sagen:**
> "Das komplette FKS-Plan-Set wird automatisch generiert:
> Deckblatt mit Legende, Situationsplan mit Gebäudeumriss und Zufahrten."

---

## Szene 5: Vorher/Nachher-Vergleich (15s)

**Aktion:** Tab "Vergleich" klicken

**Zeigen:** Side-by-side Original DXF vs. FKS-Plan

**Sagen:**
> "Im Vergleich sieht man: Links die rohe CAD-Datei, rechts der normkonforme Plan."

---

## Szene 6: Human-in-the-Loop (30s)

**Aktion:** Im Raum-Editor einen Raum von "Büro" auf "Lager" ändern

**Zeigen:** Plan wird sofort regeneriert

**Sagen:**
> "Die AI-Klassifikation kann jederzeit manuell korrigiert werden.
> Der Plan regeneriert sich sofort mit den neuen Zuweisungen."

---

## Szene 7: Layer-Toggle + Zoom (15s)

**Aktion:** Layer-Panel: Türen/Treppen ein-/ausschalten

**Aktion:** In den Plan hineinzoomen

**Sagen:**
> "Layer lassen sich einzeln ein- und ausblenden.
> Der Viewer unterstützt Zoom und Pan für detaillierte Inspektion."

---

## Szene 8: Export + Metriken (20s)

**Aktion:** Export-Dropdown öffnen

**Zeigen:** Alle 4 Download-Optionen (SVG, PDF, Deckblatt, Situationsplan)

**Aktion:** Metriken-Panel zeigen

**Sagen:**
> "Alle Pläne können als SVG oder PDF exportiert werden.
> Performance-Metriken zeigen die Dauer jedes Pipeline-Schritts."

---

## Szene 9: Tests + Architektur (20s)

**Zeigen:** Terminal mit `pytest` Ausgabe (66 Tests, 100% passing)

**Sagen:**
> "66 Unit- und Integrationstests in 5 Suiten sichern die Qualität.
> Das Backend läuft mit FastAPI + Celery, das Frontend mit Next.js 15."

---

## Szene 10: Dark Mode + Abschluss (15s)

**Aktion:** Dark Mode Toggle klicken

**Zeigen:** Gesamtes Interface im Dark Mode

**Sagen:**
> "RescueForge – von der CAD-Datei zum normkonformen Feuerwehr-Orientierungsplan in Sekunden."

---

## Tipps für die Aufnahme

1. **Browser:** Chrome, vollständig sichtbar, keine anderen Tabs
2. **Terminal:** Für Pytest-Output ein Terminal-Fenster daneben
3. **Auflösung:** 1920x1080 oder höher
4. **Testdatei:** `testdata/office_building.dxf` (14 Räume, ~12s)
5. **Docker vorher starten:** `docker compose up -d` und warten bis Backend healthy
6. **API-URL:** In `.env` sicherstellen: `NEXT_PUBLIC_API_URL=http://localhost:<backend-port>`
7. **Screen Recorder:** OBS Studio oder Windows Snipping Tool (Win+G)
