# Prompt Log

This is the condensed sequence of prompts used to build the Flashcard
Quizzer with Claude Code, in the order they were applied, following the
Decompose → Generate → Review → Refine → Verify workflow. Detailed
before/after analysis for the six most significant of these lives in
`docs/ai_edit_log.md`; this file is the flatter prompt-by-prompt record.

## Phase 1 — Data Layer & Validation

1. "Create a `Flashcard` dataclass with `front: str` and `back: str` fields."
2. "Write a `load_flashcards(filepath)` function in `utils/file_handler.py`
   that accepts either a JSON array of `{front, back}` objects, or an object
   with a top-level `cards` array. Validate every card has non-empty `front`
   and `back` strings. Never let `json.JSONDecodeError`, a missing file, or a
   missing field reach the caller as a raw traceback — raise one custom
   exception type with a human-readable message instead."
3. "Write pytest tests for the loader: a valid array-format deck, a valid
   object-format deck, invalid JSON syntax, a card missing `back`, a card
   missing `front`, an empty deck, and an unsupported top-level shape."

## Phase 2 — Core Logic & Design Patterns

4. "Implement an abstract `QuizMode` base class with `has_next()`,
   `get_next_card()`, and `record_result(card, correct)`. Then implement
   `SequentialMode` (serves cards 1..N in order), `RandomMode` (shuffles
   once), and `AdaptiveMode` (requeues cards answered incorrectly so they
   repeat later in the session)."
5. "Add a `QuizModeFactory.create(mode_name, cards)` that maps a mode name
   string to the right `QuizMode` subclass, raising `ValueError` for an
   unrecognized name."
6. "Does the Adaptive mode implementation you just wrote ever terminate if a
   card is never answered correctly?" — this surfaced the unbounded-retry
   issue documented in `docs/ai_edit_log.md`; follow-up: "Add a bounded
   `max_retries` per card so the session always ends."
7. "Write a `QuizEngine` that drives a `QuizMode` to completion and returns
   `SessionStats` (total questions, accuracy %, missed terms), but don't
   couple it to `input()`/`print()` directly — accept the answer-getting and
   feedback-reporting functions as parameters so the loop can be unit tested
   with fake I/O."
8. "If Adaptive mode re-asks a card and the user gets it right the second
   time, should that count as a fresh correct answer in the session stats,
   or should scoring only reflect each card's first attempt?" — resolved as
   documented in `docs/ai_edit_log.md`; scoring uses first attempt only.
9. "Write pytest tests for `QuizModeFactory` (each mode name, unknown mode
   name, case-insensitivity) and for each `QuizMode`'s ordering/requeue
   behavior, especially `AdaptiveMode` repeating a wrong answer and stopping
   after `max_retries`."

## Phase 3 — CLI & Interaction

10. "Build `main.py` with argparse: `-f/--file` (required), `-m/--mode`
    (choices sequential/random/adaptive, default sequential), and an
    optional `--stats` flag that writes the session summary to a JSON file."
11. "Build `ui.py`: prompt for an answer showing the card's front, print
    feedback in green for correct / red for incorrect (revealing the right
    answer), and print a final summary table. Typing 'exit' or pressing
    Ctrl+C/Ctrl+D must end the session cleanly with no traceback, not just
    print a bare error."
12. "Write an integration test that simulates a user answering 3 questions
    via a fake `ask_answer` function and asserts on the final `SessionStats`
    (`test_full_session`), plus tests for `ui.py`'s exit handling and
    `main.py`'s error path for a missing/invalid file."

## Verification pass

13. "Run `black`, `flake8`, `mypy`, and `pytest --cov` across the whole
    project and fix everything that fails." — this surfaced the
    `Type[QuizMode]` factory-typing bug fixed in `docs/ai_edit_log.md`, a
    black quote-style reformat, and a batch of missing type annotations in
    the test files.
14. "Add type hints to every test function too, and turn
    `disallow_untyped_defs` back on for `tests/` so mypy runs strict across
    the whole project, not just the source modules." — this surfaced a
    genuine typing gap: the tests were passing `Optional[Flashcard]`
    straight from `get_next_card()` into methods expecting a `Flashcard`.
    Fixed with a typed `next_card()` helper that asserts non-None.
15. "Manually run `python main.py -m adaptive -f data/python_basics.json`
    end-to-end, and also `-m sequential` with a wrong answer and the `exit`
    command, and a run against a missing file and a malformed JSON file —
    confirm none of these print a raw Python traceback."

## Second review pass — "Just follow the requirements, best practice later"

16. "Just follow the requirements please — we can do best practice later." —
    prompted a stricter re-read of `docs/report_template.md` section by
    section against `docs/final_report.md`, which found four missing
    sections (Code Quality Analysis, the Learning Outcomes and Reflection
    subsections, and Appendices A-C).
17. "Fill in the missing report sections with real, measured numbers —
    don't estimate the code/test statistics, count them." — added Metrics
    and Self-Assessment using actual LOC, function, and coverage counts
    rather than invented figures, then trimmed prose elsewhere to stay
    inside the 1000-1500 word band.
18. "The template's code-quality checklist names isort, which we dropped —
    add it, wire it into setup.cfg and requirements.txt, and confirm it
    doesn't reformat anything unexpected." — isort reported zero changes,
    confirming the existing import order was already compliant.
19. "The `ai_edit_log.md` Summary Statistics section has two blank fields
    (lines of AI-generated code used/modified) — fill them from the actual
    diff stats, not an estimate." — pulled from `git diff --stat` between
    the initial commit and the audit commit.
