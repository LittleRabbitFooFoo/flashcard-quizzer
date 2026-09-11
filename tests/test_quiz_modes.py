"""Tests for the quiz mode strategies (Strategy pattern) and their Factory."""

import random

import pytest

from models import Flashcard
from quiz_engine import AdaptiveMode, QuizMode, QuizModeFactory, RandomMode, SequentialMode

CARDS = [
    Flashcard(front="CPU", back="Central Processing Unit"),
    Flashcard(front="RAM", back="Random Access Memory"),
    Flashcard(front="SSD", back="Solid State Drive"),
]


def next_card(mode: QuizMode) -> Flashcard:
    """Pull the next card, failing the test if the deck was unexpectedly empty."""
    card = mode.get_next_card()
    assert card is not None, "expected another card, but the deck was exhausted"
    return card


class TestQuizModeFactory:
    def test_quiz_mode_factory(self) -> None:
        """The factory returns the correct class object for every mode name."""
        expected = {
            "sequential": SequentialMode,
            "random": RandomMode,
            "adaptive": AdaptiveMode,
        }
        for mode_name, expected_class in expected.items():
            assert type(QuizModeFactory.create(mode_name, CARDS)) is expected_class

    def test_quiz_mode_factory_sequential(self) -> None:
        mode = QuizModeFactory.create("sequential", CARDS)
        assert isinstance(mode, SequentialMode)

    def test_quiz_mode_factory_random(self) -> None:
        mode = QuizModeFactory.create("random", CARDS)
        assert isinstance(mode, RandomMode)

    def test_quiz_mode_factory_adaptive(self) -> None:
        mode = QuizModeFactory.create("adaptive", CARDS)
        assert isinstance(mode, AdaptiveMode)

    def test_quiz_mode_factory_is_case_insensitive(self) -> None:
        mode = QuizModeFactory.create("SEQUENTIAL", CARDS)
        assert isinstance(mode, SequentialMode)

    def test_quiz_mode_factory_rejects_unknown_mode(self) -> None:
        with pytest.raises(ValueError, match="Unknown quiz mode"):
            QuizModeFactory.create("chaotic", CARDS)


class TestSequentialMode:
    def test_serves_cards_in_original_order(self) -> None:
        mode = SequentialMode(CARDS)
        order = []
        while mode.has_next():
            order.append(mode.get_next_card())
        assert order == CARDS

    def test_exhausted_after_all_cards_served(self) -> None:
        mode = SequentialMode(CARDS)
        for _ in CARDS:
            mode.get_next_card()
        assert not mode.has_next()
        assert mode.get_next_card() is None

    def test_record_result_is_a_no_op(self) -> None:
        mode = SequentialMode(CARDS)
        card = next_card(mode)
        mode.record_result(card, correct=False)
        remaining = []
        while mode.has_next():
            remaining.append(mode.get_next_card())
        assert card not in remaining


class TestRandomMode:
    def test_serves_every_card_exactly_once(self) -> None:
        mode = RandomMode(CARDS, rng=random.Random(42))
        served = []
        while mode.has_next():
            served.append(next_card(mode))
        assert sorted(served, key=lambda c: c.front) == sorted(CARDS, key=lambda c: c.front)

    def test_shuffles_deterministically_with_seeded_rng(self) -> None:
        order_a = [c.front for c in RandomMode(CARDS, rng=random.Random(1))._queue]
        order_b = [c.front for c in RandomMode(CARDS, rng=random.Random(1))._queue]
        assert order_a == order_b


class TestAdaptiveMode:
    def test_adaptive_mode_behavior(self) -> None:
        """A card answered incorrectly is served again later in the session."""
        cards = [Flashcard(front="A", back="1"), Flashcard(front="B", back="2")]
        mode = AdaptiveMode(cards, max_retries=2)

        first = next_card(mode)
        assert first.front == "A"
        mode.record_result(first, correct=False)

        second = next_card(mode)
        assert second.front == "B"
        mode.record_result(second, correct=True)

        third = next_card(mode)
        assert third.front == "A"

    def test_adaptive_mode_stops_retrying_after_max_retries(self) -> None:
        card = Flashcard(front="A", back="1")
        mode = AdaptiveMode([card], max_retries=1)

        mode.record_result(next_card(mode), correct=False)
        second = next_card(mode)
        assert second.front == "A"

        mode.record_result(second, correct=False)
        assert not mode.has_next()

    def test_correct_answer_does_not_requeue(self) -> None:
        card = Flashcard(front="A", back="1")
        mode = AdaptiveMode([card])
        mode.record_result(next_card(mode), correct=True)
        assert not mode.has_next()
