"""Data model for a single flashcard."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Flashcard:
    """A single question/answer pair.

    Attributes:
        front: The prompt shown to the user.
        back: The expected answer, compared case-insensitively.
    """

    front: str
    back: str
