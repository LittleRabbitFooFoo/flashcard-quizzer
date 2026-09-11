"""Tests for utils.file_handler: flashcard loading and validation."""

import json
from pathlib import Path

import pytest

from utils.file_handler import FlashcardLoadError, load_flashcards


def _write(tmp_path: Path, name: str, content: str) -> str:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


class TestLoadValidFlashcards:
    def test_load_valid_flashcards_array(self, tmp_path: Path) -> None:
        content = json.dumps([{"front": "CPU", "back": "Central Processing Unit"}])
        filepath = _write(tmp_path, "deck.json", content)

        cards = load_flashcards(filepath)

        assert len(cards) == 1
        assert cards[0].front == "CPU"
        assert cards[0].back == "Central Processing Unit"

    def test_load_valid_flashcards_object_format(self, tmp_path: Path) -> None:
        content = json.dumps({"cards": [{"front": "RAM", "back": "Random Access Memory"}]})
        filepath = _write(tmp_path, "deck.json", content)

        cards = load_flashcards(filepath)

        assert len(cards) == 1
        assert cards[0].front == "RAM"

    def test_load_strips_whitespace_from_fields(self, tmp_path: Path) -> None:
        content = json.dumps([{"front": "  CPU  ", "back": "  Central Processing Unit  "}])
        filepath = _write(tmp_path, "deck.json", content)

        cards = load_flashcards(filepath)

        assert cards[0].front == "CPU"
        assert cards[0].back == "Central Processing Unit"

    def test_load_accepts_capitalized_keys(self, tmp_path: Path) -> None:
        content = json.dumps([{"Front": "CPU", "Back": "Central Processing Unit"}])
        filepath = _write(tmp_path, "deck.json", content)

        cards = load_flashcards(filepath)

        assert cards[0].front == "CPU"


class TestLoadInvalidInput:
    def test_load_invalid_json(self, tmp_path: Path) -> None:
        filepath = _write(tmp_path, "broken.json", "{not valid json,,,")

        with pytest.raises(FlashcardLoadError):
            load_flashcards(filepath)

    def test_load_missing_file(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "does_not_exist.json")

        with pytest.raises(FlashcardLoadError, match="Could not find"):
            load_flashcards(missing)

    def test_load_missing_required_field(self, tmp_path: Path) -> None:
        content = json.dumps([{"front": "CPU"}])
        filepath = _write(tmp_path, "deck.json", content)

        with pytest.raises(FlashcardLoadError, match="back"):
            load_flashcards(filepath)

    def test_load_missing_front_field(self, tmp_path: Path) -> None:
        content = json.dumps([{"back": "Central Processing Unit"}])
        filepath = _write(tmp_path, "deck.json", content)

        with pytest.raises(FlashcardLoadError, match="front"):
            load_flashcards(filepath)

    def test_load_blank_field_is_rejected(self, tmp_path: Path) -> None:
        content = json.dumps([{"front": "   ", "back": "Central Processing Unit"}])
        filepath = _write(tmp_path, "deck.json", content)

        with pytest.raises(FlashcardLoadError, match="front"):
            load_flashcards(filepath)

    def test_load_empty_deck(self, tmp_path: Path) -> None:
        filepath = _write(tmp_path, "deck.json", "[]")

        with pytest.raises(FlashcardLoadError):
            load_flashcards(filepath)

    def test_load_unsupported_shape(self, tmp_path: Path) -> None:
        filepath = _write(tmp_path, "deck.json", json.dumps({"not_cards": []}))

        with pytest.raises(FlashcardLoadError):
            load_flashcards(filepath)

    def test_load_non_object_card(self, tmp_path: Path) -> None:
        filepath = _write(tmp_path, "deck.json", json.dumps(["just a string"]))

        with pytest.raises(FlashcardLoadError):
            load_flashcards(filepath)
