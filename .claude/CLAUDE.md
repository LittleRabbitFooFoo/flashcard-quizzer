# Claude Configuration — Flashcard Quizzer

This project is the Flashcard Quizzer CLI, built for the AI-Assisted
Development course. It is a terminal app that loads flashcards from a JSON
file and quizzes the user on them in Sequential, Random, or Adaptive mode.

## Architecture

- `main.py` — argparse-based CLI entry point.
- `models.py` — the `Flashcard` dataclass.
- `utils/file_handler.py` — loads and validates flashcard JSON (array or
  `{"cards": [...]}` object format), raising `FlashcardLoadError` with a
  user-facing message instead of letting exceptions propagate as tracebacks.
- `quiz_engine.py` — `QuizMode` (Strategy pattern) with `SequentialMode`,
  `RandomMode`, `AdaptiveMode`; `QuizModeFactory` (Factory pattern) to build
  one from a mode name; `QuizEngine` drives the session and produces
  `SessionStats`.
- `ui.py` — terminal I/O: prompts, colored feedback, the stats summary.
- `tests/` — pytest suite, target >80% coverage (currently ~95%+ on source).

## Development Tools

- `pytest` / `pytest-cov` for testing and coverage.
- `black` for formatting (line length 100, see `pyproject.toml`).
- `flake8` for linting (`setup.cfg`).
- `mypy` for static type checking (`setup.cfg`); all functions carry type
  hints, and `disallow_untyped_defs` is relaxed only for `tests/`.

## Common Commands

```bash
source venv/bin/activate
python main.py -m adaptive -f data/python_basics.json
pytest
pytest --cov=main --cov=models --cov=quiz_engine --cov=ui --cov=utils --cov-report=html
black . && flake8 . && mypy .
```

## Working Conventions

- Keep `QuizMode` implementations swappable — adding a new mode (e.g. spaced
  repetition) should mean adding one class + one factory registry entry, not
  touching `QuizEngine` or `main.py`.
- Every new failure path from file loading must raise `FlashcardLoadError`
  with a message safe to print directly to a user, never a bare exception.
- Log meaningful AI interactions (prompts, what was accepted/rejected, why)
  in `docs/ai_edit_log.md`, and see `ai_guidance/` for prompting and review
  checklists used during development.
