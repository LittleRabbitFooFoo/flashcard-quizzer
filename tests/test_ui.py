"""Tests for terminal presentation helpers in ui.py."""

import builtins

import ui
from models import Flashcard
from quiz_engine import SessionStats

CARD = Flashcard(front="CPU", back="Central Processing Unit")


def test_ask_answer_returns_user_input(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt: "Central Processing Unit")
    assert ui.ask_answer(CARD) == "Central Processing Unit"


def test_ask_answer_returns_none_on_exit_command(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt: "exit")
    assert ui.ask_answer(CARD) is None


def test_ask_answer_returns_none_on_keyboard_interrupt(monkeypatch):
    def raise_interrupt(prompt):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", raise_interrupt)
    assert ui.ask_answer(CARD) is None


def test_ask_answer_returns_none_on_eof(monkeypatch):
    def raise_eof(prompt):
        raise EOFError

    monkeypatch.setattr(builtins, "input", raise_eof)
    assert ui.ask_answer(CARD) is None


def test_report_feedback_correct(capsys):
    ui.report_feedback(CARD, True)
    out = capsys.readouterr().out
    assert "Correct" in out


def test_report_feedback_incorrect_shows_answer(capsys):
    ui.report_feedback(CARD, False)
    out = capsys.readouterr().out
    assert "Incorrect" in out
    assert CARD.back in out


def test_show_stats_lists_missed_terms(capsys):
    stats = SessionStats(total_questions=2, correct=1, missed_terms=["RAM"])
    ui.show_stats(stats)
    out = capsys.readouterr().out
    assert "Total Questions : 2" in out
    assert "RAM" in out


def test_show_stats_no_missed_terms(capsys):
    stats = SessionStats(total_questions=1, correct=1, missed_terms=[])
    ui.show_stats(stats)
    out = capsys.readouterr().out
    assert "none" in out
