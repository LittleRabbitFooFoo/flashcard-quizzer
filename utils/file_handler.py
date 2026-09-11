"""Loading and validation of flashcard decks from JSON files.

Supports two JSON shapes:
    * Array format:  [{"front": "...", "back": "..."}, ...]
    * Object format: {"cards": [{"front": "...", "back": "..."}, ...]}

Every failure mode (missing file, bad JSON, missing fields) raises
FlashcardLoadError with a message written to be shown directly to a user,
never a raw Python traceback.
"""

import json
from pathlib import Path
from typing import Any, List

from models import Flashcard


class FlashcardLoadError(Exception):
    """Raised when a flashcard deck cannot be loaded or fails validation."""


def _extract_raw_cards(payload: Any, source: str) -> List[Any]:
    """Pull the list of raw card entries out of either supported JSON shape."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("cards"), list):
        return payload["cards"]
    raise FlashcardLoadError(
        f"'{source}' must contain either a JSON array of cards or an object "
        'with a top-level "cards" array.'
    )


def _parse_card(raw: Any, index: int, source: str) -> Flashcard:
    """Validate and convert one raw JSON entry into a Flashcard."""
    if not isinstance(raw, dict):
        raise FlashcardLoadError(f"Card #{index + 1} in '{source}' must be a JSON object.")

    front = raw.get("front", raw.get("Front"))
    back = raw.get("back", raw.get("Back"))

    if not isinstance(front, str) or not front.strip():
        raise FlashcardLoadError(
            f"Card #{index + 1} in '{source}' is missing a valid \"front\" field."
        )
    if not isinstance(back, str) or not back.strip():
        raise FlashcardLoadError(
            f"Card #{index + 1} in '{source}' is missing a valid \"back\" field."
        )

    return Flashcard(front=front.strip(), back=back.strip())


def load_flashcards(filepath: str) -> List[Flashcard]:
    """Load and validate a flashcard deck from a JSON file.

    Raises:
        FlashcardLoadError: if the file is missing, unreadable, malformed
            JSON, or fails structural validation.
    """
    path = Path(filepath)

    if not path.exists():
        raise FlashcardLoadError(f"Could not find flashcard file: '{filepath}'.")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FlashcardLoadError(f"Could not read '{filepath}': {exc}") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FlashcardLoadError(
            f"'{filepath}' is not valid JSON (line {exc.lineno}, column {exc.colno}): {exc.msg}."
        ) from exc

    raw_cards = _extract_raw_cards(payload, filepath)
    if not raw_cards:
        raise FlashcardLoadError(f"'{filepath}' does not contain any flashcards.")

    return [_parse_card(raw, i, filepath) for i, raw in enumerate(raw_cards)]
