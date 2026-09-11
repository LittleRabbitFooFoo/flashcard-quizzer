# Flashcard Quizzer

A terminal flashcard quiz app. Load a deck of question/answer pairs from a
JSON file and quiz yourself in Sequential, Random, or Adaptive mode, with
colored correct/incorrect feedback and an end-of-session summary.

## Features

- Loads flashcards from JSON, in either shape:
  - a plain array: `[{"front": "...", "back": "..."}, ...]`
  - a wrapper object: `{"cards": [{"front": "...", "back": "..."}, ...]}`
- Fails with a clear, friendly message (not a Python traceback) if the file
  is missing, isn't valid JSON, or a card is missing `front`/`back`.
- Three quiz modes, selectable with `-m`:
  - **sequential** — cards in the order they appear in the file.
  - **random** — cards in a shuffled order, once each.
  - **adaptive** — cards you get wrong are requeued so they come back later
    in the same session (up to 2 extra attempts each), so you see your weak
    spots more often.
- Case-insensitive answer checking with immediate colored feedback (green
  for correct, red for incorrect — the correct answer is shown when you
  miss one).
- Type `exit`, or press Ctrl+C / Ctrl+D, at any prompt to quit immediately
  without an error, and still see the summary for what you completed.
- End-of-session summary: total questions, accuracy %, and every term you
  missed. Pass `--stats` to also save that summary as JSON.

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
python main.py --help
python main.py --mode sequential --file data/glossary.json
python main.py -m adaptive -f data/python_basics.json
python main.py -m random -f data/glossary.json --stats            # writes stats.json
python main.py -m random -f data/glossary.json --stats results/session1.json
```

Sample decks are included in `data/`:

- `data/glossary.json` — server/infra acronyms (array format)
- `data/python_basics.json` — Python fundamentals (object/`cards` format)

### Run the tests

```bash
pytest
pytest --cov=main --cov=models --cov=quiz_engine --cov=ui --cov=utils --cov-report=html
```

Open `htmlcov/index.html` to browse the coverage report. Current coverage
on the five application modules is 95%, above the 80% target.

### Code quality checks

```bash
black .      # formatting (line length 100)
flake8 .     # linting
mypy .       # static type checking
```

All three currently pass with zero errors/warnings.

## Project Structure

```
flashcard-quizzer/
├── main.py                    # CLI entry point (argparse)
├── models.py                  # Flashcard dataclass
├── quiz_engine.py             # QuizMode strategies, factory, QuizEngine
├── ui.py                      # Terminal prompts, colored feedback, summary
├── utils/
│   └── file_handler.py        # JSON loading + validation
├── data/
│   ├── glossary.json
│   └── python_basics.json
├── tests/
│   ├── test_flashcard_loader.py
│   ├── test_quiz_modes.py
│   ├── test_integration.py
│   ├── test_ui.py
│   └── test_main.py
├── docs/
│   ├── ai_edit_log.md          # Detailed AI interaction log
│   ├── final_report.md         # Project report
│   ├── design_patterns.md      # Reference guide (from course starter)
│   └── project_rubric.md       # Reference rubric (from course starter)
├── ai_guidance/                 # Prompting & code review reference guides
├── prompts.md                   # Condensed prompt-by-prompt log
├── requirements.txt
├── setup.cfg                    # flake8 + mypy + pytest config
└── pyproject.toml                # black config
```

## Architecture & Design Patterns

- **Strategy pattern** (`quiz_engine.py`): `QuizMode` is an abstract base
  class with `SequentialMode`, `RandomMode`, and `AdaptiveMode` as
  interchangeable "what card comes next" algorithms. Adding a future mode
  (e.g. real spaced repetition) means adding one new class, not modifying
  existing ones.
- **Factory pattern** (`quiz_engine.py`): `QuizModeFactory.create(name,
  cards)` maps a mode name string to the correct `QuizMode` instance, so
  `main.py` never has to import or name a concrete mode class.
- `QuizEngine.run()` is decoupled from actual terminal I/O — it takes an
  `ask_answer` and `report_feedback` callable, so the entire session loop
  is unit-testable without touching stdin/stdout. `ui.py` supplies the real
  implementations used by `main.py`.

See `docs/ai_edit_log.md` for the reasoning behind these choices and where
Claude's first drafts were corrected.

## Flashcard JSON Format

```json
[
  {"front": "CPU", "back": "Central Processing Unit"}
]
```

or

```json
{
  "cards": [
    {"front": "CPU", "back": "Central Processing Unit"}
  ]
}
```

Both `front`/`back` and `Front`/`Back` keys are accepted; every card must
have a non-empty value for both.

## Built With

- [Python](https://www.python.org/) 3.10+
- [pytest](https://docs.pytest.org/) / [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Black](https://black.readthedocs.io/), [flake8](https://flake8.pycqa.org/), [mypy](https://mypy.readthedocs.io/)
- [Claude Code](https://claude.ai/code) — AI pair programmer used throughout
  development (see `prompts.md` and `docs/ai_edit_log.md`)
