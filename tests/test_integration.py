"""End-to-end tests exercising the loader, factory, and engine together."""

import json

import pytest

from models import Flashcard
from quiz_engine import QuizEngine, QuizModeFactory
from utils.file_handler import load_flashcards


def test_full_session(tmp_path):
    """Simulate a user answering 3 questions and check the final stats."""
    deck = [
        {"front": "CPU", "back": "Central Processing Unit"},
        {"front": "RAM", "back": "Random Access Memory"},
        {"front": "SSD", "back": "Solid State Drive"},
    ]
    filepath = tmp_path / "deck.json"
    filepath.write_text(json.dumps(deck), encoding="utf-8")

    cards = load_flashcards(str(filepath))
    mode = QuizModeFactory.create("sequential", cards)
    engine = QuizEngine(mode)

    answers = iter(["Central Processing Unit", "wrong answer", "solid state drive"])
    feedback_log = []

    stats = engine.run(
        ask_answer=lambda card: next(answers),
        report_feedback=lambda card, correct: feedback_log.append((card.front, correct)),
    )

    assert stats.total_questions == 3
    assert stats.correct == 2
    assert stats.missed_terms == ["RAM"]
    assert stats.accuracy == pytest.approx(66.666, rel=1e-3)
    assert feedback_log == [("CPU", True), ("RAM", False), ("SSD", True)]


def test_session_stops_early_when_user_exits():
    cards = [Flashcard(front="A", back="1"), Flashcard(front="B", back="2")]
    mode = QuizModeFactory.create("sequential", cards)
    engine = QuizEngine(mode)

    answers = iter(["1", None])
    stats = engine.run(
        ask_answer=lambda card: next(answers),
        report_feedback=lambda card, correct: None,
    )

    assert stats.total_questions == 1
    assert stats.correct == 1


def test_full_session_with_adaptive_mode_scores_first_attempt_only():
    """Adaptive mode re-asks missed cards, but scoring counts first tries."""
    cards = [Flashcard(front="A", back="1"), Flashcard(front="B", back="2")]
    mode = QuizModeFactory.create("adaptive", cards)
    engine = QuizEngine(mode)

    # First attempt at A is wrong, B is right, then A is retried and gotten right.
    answers = iter(["wrong", "2", "1"])
    stats = engine.run(
        ask_answer=lambda card: next(answers),
        report_feedback=lambda card, correct: None,
    )

    assert stats.total_questions == 2
    assert stats.correct == 1
    assert stats.missed_terms == ["A"]
