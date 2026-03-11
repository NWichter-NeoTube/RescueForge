"""Centralized translation system for fire department orientation plans.

Supports English (EN) and German (DE) for all plan text, labels,
and filenames per DIN 14095 / FKS-Richtlinie requirements.
"""

from typing import Literal

Locale = Literal["en", "de"]

# ---------------------------------------------------------------------------
# Master translation table: key -> {locale: text}
# ---------------------------------------------------------------------------
PLAN_TEXT: dict[str, dict[str, str]] = {
    # ── Title block (Schriftfeld) ─────────────────────────────────
    "title.orientation_plan": {
        "de": "Orientierungsplan",
        "en": "Orientation Plan",
    },
    "title.cover_sheet": {
        "de": "Deckblatt",
        "en": "Cover Sheet",
    },
    "title.situation_plan": {
        "de": "Situationsplan",
        "en": "Situation Plan",
    },
    "title.object": {
        "de": "Objekt",
        "en": "Building",
    },
    "title.address": {
        "de": "Adresse",
        "en": "Address",
    },
    "title.floor": {
        "de": "Geschoss",
        "en": "Floor",
    },
    "title.scale": {
        "de": "Massstab",
        "en": "Scale",
    },
    "title.created_with": {
        "de": "Erstellt mit RescueForge",
        "en": "Created with RescueForge",
    },
    "title.creation_date": {
        "de": "Erstelldatum",
        "en": "Creation Date",
    },
    "title.revision_date": {
        "de": "Revisionsdatum",
        "en": "Revision Date",
    },
    "title.creator": {
        "de": "Planersteller",
        "en": "Plan Creator",
    },
    "title.registration": {
        "de": "Reg.-Nr.",
        "en": "Reg. No.",
    },
    "title.page": {
        "de": "Seite",
        "en": "Page",
    },
    "title.floors_label": {
        "de": "Geschosse",
        "en": "Floors",
    },

    # ── Legend ─────────────────────────────────────────────────────
    "legend.title": {
        "de": "Legende",
        "en": "Legend",
    },
    "legend.vertical_escape": {
        "de": "Vertikaler Fluchtweg",
        "en": "Vertical Escape Route",
    },
    "legend.horizontal_escape": {
        "de": "Horizontaler Fluchtweg",
        "en": "Horizontal Escape Route",
    },
    "legend.danger_zone": {
        "de": "Gefahrenbereich",
        "en": "Danger Zone",
    },
    "legend.fire_wall": {
        "de": "Brandwand",
        "en": "Fire Wall",
    },
    "legend.fire_door": {
        "de": "Brandschutzt\u00fcr",
        "en": "Fire Door",
    },
    "legend.non_passable": {
        "de": "Nicht begehbar",
        "en": "Non-passable Area",
    },
    "legend.symbols": {
        "de": "Symbole",
        "en": "Symbols",
    },

    # ── Symbol labels ─────────────────────────────────────────────
    "symbol.smoke_detector": {
        "de": "Rauchmelder",
        "en": "Smoke Detector",
    },
    "symbol.manual_call_point": {
        "de": "Handfeuermelder",
        "en": "Manual Call Point",
    },
    "symbol.bma": {
        "de": "Brandmeldezentrale",
        "en": "Fire Alarm Panel",
    },
    "symbol.escape_route": {
        "de": "Fluchtweg",
        "en": "Escape Route",
    },
    "symbol.fire_access": {
        "de": "Feuerwehrzugang",
        "en": "Fire Access",
    },
    "symbol.key_depot": {
        "de": "Schl\u00fcsseldepot",
        "en": "Key Depot",
    },
    "symbol.north_arrow": {
        "de": "Nordpfeil",
        "en": "North Arrow",
    },
    "symbol.scale_bar": {
        "de": "Massstabsbalken",
        "en": "Scale Bar",
    },
    "symbol.gas_shutoff": {
        "de": "Gasabsperrung",
        "en": "Gas Shutoff",
    },
    "symbol.water_shutoff": {
        "de": "Wasserabsperrung",
        "en": "Water Shutoff",
    },
    "symbol.electricity_shutoff": {
        "de": "Elektrohauptschalter",
        "en": "Main Power Switch",
    },
    "symbol.wall_hydrant": {
        "de": "Wandhydrant",
        "en": "Wall Hydrant",
    },
    "symbol.sprinkler": {
        "de": "Sprinkleranlage",
        "en": "Sprinkler System",
    },
    "symbol.elevator": {
        "de": "Aufzug",
        "en": "Elevator",
    },
    "symbol.stair_direction": {
        "de": "Treppenlaufrichtung",
        "en": "Stair Direction",
    },
    "symbol.rwa": {
        "de": "Rauch-/W\u00e4rmeabzug",
        "en": "Smoke/Heat Extraction",
    },
    "symbol.assembly_point": {
        "de": "Sammelplatz",
        "en": "Assembly Point",
    },
    "symbol.erstinfo": {
        "de": "Erstinformationsstelle",
        "en": "First Information Point",
    },
    "symbol.fire_door_sym": {
        "de": "Brandschutzt\u00fcr",
        "en": "Fire Door",
    },

    # ── Room type labels ──────────────────────────────────────────
    "room.office": {
        "de": "B\u00fcro",
        "en": "Office",
    },
    "room.corridor": {
        "de": "Korridor",
        "en": "Corridor",
    },
    "room.stairwell": {
        "de": "Treppenhaus",
        "en": "Stairwell",
    },
    "room.elevator": {
        "de": "Aufzug",
        "en": "Elevator",
    },
    "room.bathroom": {
        "de": "WC/Nassraum",
        "en": "Bathroom",
    },
    "room.kitchen": {
        "de": "K\u00fcche",
        "en": "Kitchen",
    },
    "room.storage": {
        "de": "Lager",
        "en": "Storage",
    },
    "room.technical": {
        "de": "Technik",
        "en": "Technical",
    },
    "room.server_room": {
        "de": "Serverraum",
        "en": "Server Room",
    },
    "room.garage": {
        "de": "Garage",
        "en": "Garage",
    },
    "room.lobby": {
        "de": "Halle/Empfang",
        "en": "Lobby/Reception",
    },
    "room.conference": {
        "de": "Sitzungszimmer",
        "en": "Conference Room",
    },
    "room.residential": {
        "de": "Wohnraum",
        "en": "Residential",
    },
    "room.bedroom": {
        "de": "Schlafzimmer",
        "en": "Bedroom",
    },
    "room.living_room": {
        "de": "Wohnzimmer",
        "en": "Living Room",
    },
    "room.balcony": {
        "de": "Balkon",
        "en": "Balcony",
    },
    "room.unknown": {
        "de": "Unbekannt",
        "en": "Unknown",
    },

    # ── Cover sheet ───────────────────────────────────────────────
    "cover.header": {
        "de": "Orientierungsplan \u2013 Deckblatt",
        "en": "Orientation Plan \u2013 Cover Sheet",
    },
    "cover.object_definition": {
        "de": "Objektdefinition",
        "en": "Building Definition",
    },
    "cover.usage": {
        "de": "Nutzung",
        "en": "Usage",
    },
    "cover.usage_residential": {
        "de": "Wohngeb\u00e4ude",
        "en": "Residential Building",
    },
    "cover.usage_commercial": {
        "de": "Gewerbe / Industrie",
        "en": "Commercial / Industrial",
    },
    "cover.usage_office": {
        "de": "B\u00fcro- / Verwaltungsgeb\u00e4ude",
        "en": "Office / Administrative Building",
    },
    "cover.plans": {
        "de": "Pl\u00e4ne",
        "en": "Plans",
    },
    "cover.room_types": {
        "de": "Legende \u2013 Raumtypen",
        "en": "Legend \u2013 Room Types",
    },
    "cover.symbols": {
        "de": "Legende \u2013 Symbole",
        "en": "Legend \u2013 Symbols",
    },
    "cover.colors": {
        "de": "Farbgebung",
        "en": "Color Scheme",
    },
    "cover.escape_direction": {
        "de": "Fluchtweg-Richtung",
        "en": "Escape Route Direction",
    },
    "cover.pv_present": {
        "de": "PV-Anlage vorhanden",
        "en": "PV System Present",
    },

    # ── Situation plan ────────────────────────────────────────────
    "situation.header": {
        "de": "Situationsplan",
        "en": "Situation Plan",
    },
    "situation.street": {
        "de": "Strasse",
        "en": "Street",
    },
    "situation.fire_access": {
        "de": "Feuerwehrzufahrt",
        "en": "Fire Dept. Access",
    },
    "situation.key_depot": {
        "de": "Schl\u00fcsseldepot",
        "en": "Key Depot",
    },
    "situation.side_a": {
        "de": "Seite A (Nord)",
        "en": "Side A (North)",
    },
    "situation.side_b": {
        "de": "Seite B (Ost)",
        "en": "Side B (East)",
    },
    "situation.side_c": {
        "de": "Seite C (S\u00fcd)",
        "en": "Side C (South)",
    },
    "situation.side_d": {
        "de": "Seite D (West)",
        "en": "Side D (West)",
    },

    # ── Filename suffixes ─────────────────────────────────────────
    "filename.orientation_plan": {
        "de": "orientierungsplan",
        "en": "orientation_plan",
    },
    "filename.cover_sheet": {
        "de": "deckblatt",
        "en": "cover_sheet",
    },
    "filename.situation_plan": {
        "de": "situationsplan",
        "en": "situation_plan",
    },
    "filename.compliance_report": {
        "de": "konformitaetsbericht",
        "en": "compliance_report",
    },

    # ── WebSocket progress labels ─────────────────────────────────
    "progress.converting": {
        "de": "DWG wird konvertiert...",
        "en": "Converting DWG...",
    },
    "progress.parsing": {
        "de": "DXF wird analysiert...",
        "en": "Parsing DXF...",
    },
    "progress.detecting_rooms": {
        "de": "R\u00e4ume werden erkannt...",
        "en": "Detecting rooms...",
    },
    "progress.classifying": {
        "de": "AI klassifiziert R\u00e4ume...",
        "en": "AI classifying rooms...",
    },
    "progress.generating": {
        "de": "Orientierungsplan wird erstellt...",
        "en": "Generating orientation plan...",
    },
    "progress.exporting": {
        "de": "PDF wird exportiert...",
        "en": "Exporting PDF...",
    },
    "progress.processing": {
        "de": "Verarbeitung ({step})...",
        "en": "Processing ({step})...",
    },

    # ── Color legend entries ──────────────────────────────────────
    "color.vertical_escape": {
        "de": "Vertikale Fluchtw.",
        "en": "Vertical Escape R.",
    },
    "color.horizontal_escape": {
        "de": "Horizontale Fluchtw.",
        "en": "Horizontal Escape R.",
    },
    "color.walls": {
        "de": "W\u00e4nde",
        "en": "Walls",
    },
    "color.doors": {
        "de": "T\u00fcren",
        "en": "Doors",
    },
    "color.fire_walls": {
        "de": "Brandw\u00e4nde",
        "en": "Fire Walls",
    },

    # ── Compliance document ───────────────────────────────────────
    "compliance.title": {
        "de": "DIN 14095 / FKS Konformit\u00e4tsbericht",
        "en": "DIN 14095 / FKS Compliance Report",
    },
    "compliance.standards": {
        "de": "Eingehaltene Normen",
        "en": "Standards Adhered To",
    },
    "compliance.elements": {
        "de": "Generierte Elemente und Konformit\u00e4tsgrad",
        "en": "Generated Elements and Compliance Level",
    },
    "compliance.manual_input": {
        "de": "Elemente die manuelle Eingabe erfordern",
        "en": "Elements Requiring Manual Input",
    },
    "compliance.element": {
        "de": "Element",
        "en": "Element",
    },
    "compliance.din_reference": {
        "de": "DIN-Referenz",
        "en": "DIN Reference",
    },
    "compliance.status": {
        "de": "Status",
        "en": "Status",
    },
    "compliance.implemented": {
        "de": "Umgesetzt",
        "en": "Implemented",
    },
    "compliance.partial": {
        "de": "Teilweise",
        "en": "Partial",
    },
    "compliance.not_available": {
        "de": "Nicht verf\u00fcgbar",
        "en": "Not Available",
    },
    "compliance.manual_required": {
        "de": "Manuelle Eingabe erforderlich",
        "en": "Manual Input Required",
    },
    "compliance.description": {
        "de": "Beschreibung",
        "en": "Description",
    },
    "compliance.reason": {
        "de": "Begr\u00fcndung",
        "en": "Reason",
    },
}

# ---------------------------------------------------------------------------
# Room-type enum value -> translation key mapping
# ---------------------------------------------------------------------------
ROOM_TYPE_KEYS: dict[str, str] = {
    "office": "room.office",
    "corridor": "room.corridor",
    "stairwell": "room.stairwell",
    "elevator": "room.elevator",
    "bathroom": "room.bathroom",
    "kitchen": "room.kitchen",
    "storage": "room.storage",
    "technical": "room.technical",
    "server_room": "room.server_room",
    "garage": "room.garage",
    "lobby": "room.lobby",
    "conference": "room.conference",
    "residential": "room.residential",
    "bedroom": "room.bedroom",
    "living_room": "room.living_room",
    "balcony": "room.balcony",
    "unknown": "room.unknown",
}


def t(key: str, locale: Locale = "en") -> str:
    """Return the localized string for *key*. Falls back to English, then key."""
    entry = PLAN_TEXT.get(key)
    if not entry:
        return key
    return entry.get(locale, entry.get("en", key))


def room_label(room_type_value: str, locale: Locale = "en") -> str:
    """Get the localized display name for a room-type enum value."""
    key = ROOM_TYPE_KEYS.get(room_type_value, "room.unknown")
    return t(key, locale)
