"""Quiz mode strategies, their factory, and the engine that runs a session.

Design patterns:
    * Strategy  - QuizMode is the strategy interface; Sequential/Random/
      Adaptive are interchangeable algorithms for "what card comes next".
    * Factory   - QuizModeFactory turns a user-supplied mode name into the
      right QuizMode subclass without callers needing to know the classes.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Dict, List, Optional, Set

from models import Flashcard


class QuizMode(ABC):
    """Strategy interface for selecting the order flashcards are served in."""

    @abstractmethod
    def has_next(self) -> bool:
        """Return True while there are more cards left to serve."""

    @abstractmethod
    def get_next_card(self) -> Optional[Flashcard]:
        """Return the next card to ask, or None if the deck is exhausted."""

    @abstractmethod
    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Tell the strategy how the user answered `card`."""


class SequentialMode(QuizMode):
    """Serves cards in the order they were loaded, card 1 through N."""

    def __init__(self, cards: List[Flashcard]) -> None:
        self._queue: Deque[Flashcard] = deque(cards)

    def has_next(self) -> bool:
        return bool(self._queue)

    def get_next_card(self) -> Optional[Flashcard]:
        return self._queue.popleft() if self._queue else None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        return None


class RandomMode(QuizMode):
    """Serves cards in a shuffled order, exactly once each."""

    def __init__(self, cards: List[Flashcard], rng: Optional[random.Random] = None) -> None:
        shuffled = list(cards)
        (rng or random).shuffle(shuffled)
        self._queue: Deque[Flashcard] = deque(shuffled)

    def has_next(self) -> bool:
        return bool(self._queue)

    def get_next_card(self) -> Optional[Flashcard]:
        return self._queue.popleft() if self._queue else None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        return None


class AdaptiveMode(QuizMode):
    """Serves cards in order, but requeues wrong answers so they repeat.

    A card answered incorrectly is pushed to the back of the queue so it
    resurfaces later in the same session, up to `max_retries` extra
    attempts per card. This is a deliberately simple stand-in for full
    spaced repetition, and can be swapped for one later without touching
    QuizEngine, since both are just QuizMode implementations.
    """

    def __init__(self, cards: List[Flashcard], max_retries: int = 2) -> None:
        self._queue: Deque[Flashcard] = deque(cards)
        self._max_retries = max_retries
        self._retry_counts: Dict[str, int] = defaultdict(int)

    def has_next(self) -> bool:
        return bool(self._queue)

    def get_next_card(self) -> Optional[Flashcard]:
        return self._queue.popleft() if self._queue else None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        if not correct and self._retry_counts[card.front] < self._max_retries:
            self._retry_counts[card.front] += 1
            self._queue.append(card)


class QuizModeFactory:
    """Factory that maps a mode name to a configured QuizMode instance."""

    _REGISTRY: Dict[str, Callable[[List[Flashcard]], QuizMode]] = {
        "sequential": SequentialMode,
        "random": RandomMode,
        "adaptive": AdaptiveMode,
    }

    @classmethod
    def create(cls, mode_name: str, cards: List[Flashcard]) -> QuizMode:
        key = mode_name.strip().lower()
        mode_class = cls._REGISTRY.get(key)
        if mode_class is None:
            valid = ", ".join(sorted(cls._REGISTRY))
            raise ValueError(f"Unknown quiz mode '{mode_name}'. Choose from: {valid}.")
        return mode_class(cards)


@dataclass
class SessionStats:
    """Summary statistics for a completed (or aborted) quiz session."""

    total_questions: int = 0
    correct: int = 0
    missed_terms: List[str] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.correct / self.total_questions) * 100


AnswerProvider = Callable[[Flashcard], Optional[str]]
FeedbackReporter = Callable[[Flashcard, bool], None]


class QuizEngine:
    """Runs a quiz session by driving a QuizMode strategy and tracking stats."""

    def __init__(self, mode: QuizMode) -> None:
        self._mode = mode
        self._stats = SessionStats()
        self._seen: Set[str] = set()

    @property
    def stats(self) -> SessionStats:
        return self._stats

    def run(self, ask_answer: AnswerProvider, report_feedback: FeedbackReporter) -> SessionStats:
        """Drive the quiz loop until the mode is exhausted or the user quits.

        `ask_answer` is called with each Flashcard and must return the
        user's answer, or None to signal that the user wants to quit.
        `report_feedback` is called after each answer with the card and
        whether it was correct, so the caller can render feedback.

        Accuracy and missed terms are based on each card's first attempt,
        so a card that adaptive mode repeats does not inflate the score.
        """
        while self._mode.has_next():
            card = self._mode.get_next_card()
            if card is None:
                break

            answer = ask_answer(card)
            if answer is None:
                break

            correct = answer.strip().lower() == card.back.strip().lower()

            if card.front not in self._seen:
                self._seen.add(card.front)
                self._stats.total_questions += 1
                if correct:
                    self._stats.correct += 1
                else:
                    self._stats.missed_terms.append(card.front)

            report_feedback(card, correct)
            self._mode.record_result(card, correct)

        return self._stats
