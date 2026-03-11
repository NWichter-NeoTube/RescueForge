"""Tests for the centralized translation system (app/utils/translations.py).

Focuses on: t() fallback logic, room_label() behaviour, structural invariants.
Does NOT snapshot every single translation string — those break on any text edit.
"""

import pytest

from app.utils.translations import PLAN_TEXT, ROOM_TYPE_KEYS, room_label, t


class TestTFunction:
    """Tests for t(key, locale) translation helper logic."""

    def test_default_locale_is_english(self) -> None:
        assert t("title.orientation_plan") == "Orientation Plan"

    def test_returns_german_when_requested(self) -> None:
        assert t("title.orientation_plan", "de") == "Orientierungsplan"

    def test_fallback_to_english_for_unknown_locale(self) -> None:
        result = t("title.floor", "fr")  # type: ignore[arg-type]
        assert result == "Floor"

    def test_returns_key_for_missing_key(self) -> None:
        assert t("nonexistent.key") == "nonexistent.key"
        assert t("nonexistent.key", "de") == "nonexistent.key"

    def test_returns_key_for_empty_string(self) -> None:
        assert t("") == ""


class TestRoomLabel:
    """Tests for room_label(room_type_value, locale)."""

    def test_default_locale_is_english(self) -> None:
        assert room_label("office") == "Office"

    def test_english_sample(self) -> None:
        assert room_label("corridor", "en") == "Corridor"
        assert room_label("stairwell", "en") == "Stairwell"

    def test_german_sample(self) -> None:
        assert room_label("office", "de") == "Büro"
        assert room_label("bathroom", "de") == "WC/Nassraum"

    def test_unknown_type_falls_back_en(self) -> None:
        assert room_label("nonexistent", "en") == "Unknown"
        assert room_label("", "en") == "Unknown"

    def test_unknown_type_falls_back_de(self) -> None:
        assert room_label("nonexistent", "de") == "Unbekannt"


class TestCoverageCompleteness:
    """Structural invariants — catch missing translations or broken mappings."""

    def test_every_key_has_en_and_de(self) -> None:
        """Every PLAN_TEXT entry must have both 'en' and 'de'."""
        missing = [k for k, v in PLAN_TEXT.items() if "en" not in v or "de" not in v]
        assert missing == [], f"Keys missing a locale: {missing}"

    def test_no_empty_values(self) -> None:
        """All translation values must be non-empty strings."""
        empty = [
            f"{k}[{loc}]"
            for k, v in PLAN_TEXT.items()
            for loc, txt in v.items()
            if not isinstance(txt, str) or not txt.strip()
        ]
        assert empty == [], f"Empty translations: {empty}"

    def test_room_type_keys_count(self) -> None:
        assert len(ROOM_TYPE_KEYS) == 17

    def test_room_type_keys_map_to_valid_plan_text(self) -> None:
        invalid = [f"{rt}->{k}" for rt, k in ROOM_TYPE_KEYS.items() if k not in PLAN_TEXT]
        assert invalid == [], f"Invalid mappings: {invalid}"

    def test_all_room_keys_are_mapped(self) -> None:
        """Every room.* key in PLAN_TEXT should be referenced by ROOM_TYPE_KEYS."""
        room_keys = {k for k in PLAN_TEXT if k.startswith("room.")}
        mapped = set(ROOM_TYPE_KEYS.values())
        assert room_keys == mapped
