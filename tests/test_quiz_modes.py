"""Tests for the quiz mode strategies (Strategy pattern) and their Factory."""

import random

import pytest

from models import Flashcard
from quiz_engine import AdaptiveMode, QuizModeFactory, RandomMode, SequentialMode

CARDS = [
    Flashcard(front="CPU", back="Central Processing Unit"),
    Flashcard(front="RAM", back="Random Access Memory"),
    Flashcard(front="SSD", back="Solid State Drive"),
]


class TestQuizModeFactory:
    def test_quiz_mode_factory_sequential(self):
        mode = QuizModeFactory.create("sequential", CARDS)
        assert isinstance(mode, SequentialMode)

    def test_quiz_mode_factory_random(self):
        mode = QuizModeFactory.create("random", CARDS)
        assert isinstance(mode, RandomMode)

    def test_quiz_mode_factory_adaptive(self):
        mode = QuizModeFactory.create("adaptive", CARDS)
        assert isinstance(mode, AdaptiveMode)

    def test_quiz_mode_factory_is_case_insensitive(self):
        mode = QuizModeFactory.create("SEQUENTIAL", CARDS)
        assert isinstance(mode, SequentialMode)

    def test_quiz_mode_factory_rejects_unknown_mode(self):
        with pytest.raises(ValueError, match="Unknown quiz mode"):
            QuizModeFactory.create("chaotic", CARDS)


class TestSequentialMode:
    def test_serves_cards_in_original_order(self):
        mode = SequentialMode(CARDS)
        order = []
        while mode.has_next():
            order.append(mode.get_next_card())
        assert order == CARDS

    def test_exhausted_after_all_cards_served(self):
        mode = SequentialMode(CARDS)
        for _ in CARDS:
            mode.get_next_card()
        assert not mode.has_next()
        assert mode.get_next_card() is None

    def test_record_result_is_a_no_op(self):
        mode = SequentialMode(CARDS)
        card = mode.get_next_card()
        mode.record_result(card, correct=False)
        remaining = []
        while mode.has_next():
            remaining.append(mode.get_next_card())
        assert card not in remaining


class TestRandomMode:
    def test_serves_every_card_exactly_once(self):
        mode = RandomMode(CARDS, rng=random.Random(42))
        served = []
        while mode.has_next():
            served.append(mode.get_next_card())
        assert sorted(served, key=lambda c: c.front) == sorted(CARDS, key=lambda c: c.front)

    def test_shuffles_deterministically_with_seeded_rng(self):
        order_a = [c.front for c in RandomMode(CARDS, rng=random.Random(1))._queue]
        order_b = [c.front for c in RandomMode(CARDS, rng=random.Random(1))._queue]
        assert order_a == order_b


class TestAdaptiveMode:
    def test_adaptive_mode_behavior_repeats_wrong_answers(self):
        cards = [Flashcard(front="A", back="1"), Flashcard(front="B", back="2")]
        mode = AdaptiveMode(cards, max_retries=2)

        first = mode.get_next_card()
        assert first.front == "A"
        mode.record_result(first, correct=False)

        second = mode.get_next_card()
        assert second.front == "B"
        mode.record_result(second, correct=True)

        third = mode.get_next_card()
        assert third.front == "A"

    def test_adaptive_mode_stops_retrying_after_max_retries(self):
        card = Flashcard(front="A", back="1")
        mode = AdaptiveMode([card], max_retries=1)

        mode.record_result(mode.get_next_card(), correct=False)
        second = mode.get_next_card()
        assert second.front == "A"

        mode.record_result(second, correct=False)
        assert not mode.has_next()

    def test_correct_answer_does_not_requeue(self):
        card = Flashcard(front="A", back="1")
        mode = AdaptiveMode([card])
        mode.record_result(mode.get_next_card(), correct=True)
        assert not mode.has_next()
