"""Tests for the CLI entry point in main.py."""

import json

import pytest

import main


def _write_deck(tmp_path):
    deck = [{"front": "CPU", "back": "Central Processing Unit"}]
    filepath = tmp_path / "deck.json"
    filepath.write_text(json.dumps(deck), encoding="utf-8")
    return str(filepath)


def test_run_returns_error_code_for_missing_file(capsys, tmp_path):
    exit_code = main.run(["-f", str(tmp_path / "missing.json")])
    assert exit_code == 1
    assert "Error" in capsys.readouterr().err


def test_run_completes_a_session_and_prints_stats(monkeypatch, tmp_path, capsys):
    filepath = _write_deck(tmp_path)
    monkeypatch.setattr(main.ui, "ask_answer", lambda card: "Central Processing Unit")

    exit_code = main.run(["-f", filepath, "-m", "sequential"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Total Questions : 1" in out


def test_run_writes_stats_file_when_requested(monkeypatch, tmp_path):
    filepath = _write_deck(tmp_path)
    monkeypatch.setattr(main.ui, "ask_answer", lambda card: "Central Processing Unit")
    stats_path = tmp_path / "out.json"

    main.run(["-f", filepath, "--stats", str(stats_path)])

    saved = json.loads(stats_path.read_text(encoding="utf-8"))
    assert saved["total_questions"] == 1
    assert saved["correct"] == 1


def test_help_flag_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main.run(["--help"])
    assert exc_info.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_invalid_mode_choice_is_rejected_by_argparse(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main.run(["-f", "irrelevant.json", "-m", "bogus"])
    assert exc_info.value.code == 2
