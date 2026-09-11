# AI-Assisted Development Project Report

**Student Name:** Simon
**Project Title:** Flashcard Quizzer CLI
**Date:** 2026-09-11

## Executive Summary

The Flashcard Quizzer is a terminal application that loads a deck of
question/answer pairs from a JSON file and quizzes the user on them in one
of three modes: Sequential, Random, or Adaptive. It compares typed answers
case-insensitively, gives immediate colored feedback, and prints a session
summary (total questions, accuracy, and a list of missed terms) at the end.

I built this end-to-end with Claude Code, working in the small phases the
project brief lays out — data loading and validation, then the quiz engine
and design patterns, then the CLI and interaction layer, then tests and
quality tooling — reviewing and, in several cases, rejecting or correcting
Claude's first draft before accepting it. That review record lives in
`docs/ai_edit_log.md`; this report summarizes the process and what I took
from it.

## Project Overview

### Problem Statement

New hires need a low-friction way to memorize a glossary of terms (server
acronyms, in the motivating example) without a GUI, an account, or a
network dependency — something that runs anywhere Python does, reads a
plain JSON file a non-engineer could edit, and gets harder to fool the more
you get wrong.

### Solution Approach

The application is split into four modules with one job each: `models.py`
(the `Flashcard` data shape), `utils/file_handler.py` (loading and
validating JSON), `quiz_engine.py` (the quiz strategies, factory, and
session loop), and `ui.py` (terminal prompts, color, and the summary
table), wired together by `main.py`'s argparse-based CLI. Keeping the quiz
engine's `run()` method decoupled from `input()`/`print()` — it accepts an
answer-getter and a feedback-reporter as parameters — turned out to be the
single most important architectural decision, since it made the entire
scoring loop testable without touching stdin/stdout.

### Final Features

- [x] Load flashcards from JSON in either array or `{"cards": [...]}` form
- [x] Case-insensitive answer checking with immediate colored feedback
- [x] Three interchangeable quiz modes via the Strategy pattern
- [x] Adaptive mode that requeues missed cards, bounded by `max_retries`
- [x] End-of-session summary: total questions, accuracy %, missed terms
- [x] `--stats` flag to persist that summary as JSON for later review

Five of these go well beyond the starter template's basic CRUD: the
pluggable quiz-mode system, adaptive repetition, first-attempt scoring,
dual-schema JSON ingestion with validation, and session statistics with
JSON export.

## AI Collaboration Experience

### AI Tools Used

- [x] Claude Code (Sonnet 5)

### Collaboration Workflow

I worked phase by phase rather than asking for the whole application in one
prompt: data layer first, then the design-pattern-driven quiz logic, then
the CLI, then the test suite and quality gates. Each prompt named the exact
function or class to produce, its inputs/outputs, and — critically — the
failure modes it had to handle, since "handle errors gracefully" alone
tends to produce code that only handles the failure modes the author
happened to think of. After each phase I read the generated code before
running anything, ran the test suite, and then asked Claude to run `black`,
`flake8`, and `mypy` and fix whatever they flagged, rather than accepting
the code as done once it merely executed.

### Most Valuable AI Interactions

Five interactions are documented in full in `docs/ai_edit_log.md`:
tightening the loader's error handling into one `FlashcardLoadError` type
instead of a leaked `KeyError`; catching and fixing an unbounded retry loop
in the first draft of `AdaptiveMode`; decoupling `QuizEngine` from direct
`input()`/`print()` calls so the session loop could be unit tested;
correcting a `mypy` factory-typing error (`Type[QuizMode]` doesn't fit
subclasses with different constructor signatures — `Callable[[List[
Flashcard]], QuizMode]` does); and resolving an ambiguous scoring question
for Adaptive mode (does a retried-and-then-correct card count as a fresh
correct answer, or does scoring reflect only the first attempt?) before
writing tests that would have locked in whichever answer came first.

### Challenges with AI Collaboration

The pattern across all five documented interactions is the same: Claude
reliably implements exactly what a prompt specifies, but a prompt that
sounds complete in plain English ("requeue a card when it's answered
wrong") can still hide an edge case (no retry limit, so the loop never
ends) that only surfaces when you ask "does this actually terminate?"
rather than "does this look right?" The fix was never to distrust the
tool's code quality — the generated code itself was consistently clean,
type-hinted, and idiomatic — it was to be more suspicious about what I
hadn't specified.

## Software Engineering Practices

### Code Quality Measures

- [x] Code formatting (Black, line length 100)
- [x] Linting (flake8) — zero errors
- [x] Type hints on every function; mypy passes with zero errors
- [x] Docstrings on every module, class, and public function
- [x] Error handling at the file-loading boundary; input validation on
      every parsed card

### Testing Strategy

42 pytest tests across five files: `test_flashcard_loader.py` (valid and
invalid JSON in both supported shapes, missing/blank fields), `test_quiz_
modes.py` (the factory, and each mode's ordering/requeue behavior),
`test_integration.py` (a full simulated session, an early-exit session, and
the adaptive first-attempt-scoring rule), `test_ui.py` (input handling
including Ctrl+C/Ctrl+D/`exit`, and colored output), and `test_main.py`
(the CLI's argument parsing and error path for a missing file). Coverage on
the five application modules (`main.py`, `models.py`, `quiz_engine.py`,
`ui.py`, `utils/file_handler.py`) is 95%, comfortably above the 80% target;
the ten uncovered lines are argparse's own `--help` exit path and two
narrow `OSError` branches in file reading that aren't practical to trigger
without mocking the filesystem.

### Design Patterns Used

- **Strategy** — `QuizMode` is the abstract interface; `SequentialMode`,
  `RandomMode`, and `AdaptiveMode` are interchangeable algorithms for "what
  card comes next," selected at runtime and swappable without touching
  `QuizEngine`.
- **Factory** — `QuizModeFactory.create(name, cards)` turns a CLI string
  into the right `QuizMode` instance, so `main.py` never imports or names a
  concrete mode class directly. Adding a future "spaced repetition" mode
  means adding one class and one factory registry entry.

### Code Structure and Organization

Each module has a single responsibility and no module reaches into
another's internals: `main.py` only orchestrates, `ui.py` only touches the
terminal, `quiz_engine.py` only knows about ordering and scoring, and
`utils/file_handler.py` only knows about JSON. This is what made the
Strategy/Factory refactor and the I/O-decoupling refactor both low-risk —
each one touched exactly one module's internals without requiring changes
to its callers' code, only (in the Strategy/Factory case) the values passed
across the boundary.

## Technical Challenges and Solutions

### Challenge 1: Terminating Adaptive mode

**Problem:** The literal implementation of "requeue wrong answers" has no
natural end condition. **Solution:** Added `max_retries` per card, tracked
in a dict keyed by the card's front. **AI Involvement:** Claude wrote both
the original unbounded version and, once asked directly whether it
terminates, the bounded fix. **Lessons Learned:** Ask "does this loop
always end?" as a standing question for any AI-generated queue/retry logic.

### Challenge 2: Scoring semantics under retries

**Problem:** Once a card can be presented more than once, "accuracy" is
ambiguous. **Solution:** Score every card by its first attempt only, using
a `_seen` set in `QuizEngine`; later re-presentations still drive the
`QuizMode`'s requeue logic but don't touch the tally. **AI Involvement:**
Claude proposed both options once the ambiguity was raised explicitly.
**Lessons Learned:** Resolve product-behavior ambiguity before writing
tests, since either implementation passes its own tests.

## Learning Outcomes

Working phase-by-phase with explicit failure-mode requirements, then
treating "runs without crashing" as a much lower bar than "passes review,"
was the main practical skill this project reinforced. I also came away
more confident using type checking (mypy) as a design tool rather than
pure lint — the factory-typing bug it caught was a real signature mismatch,
not a false positive, and fixing the type instead of suppressing it forced
a more honest interface.

## Reflection

The Strategy/Factory pattern pairing paid for itself immediately: Adaptive
mode's retry-limit fix and the I/O decoupling in `QuizEngine` were both
one-module changes because responsibilities were already separated. If I
extended this further, I'd add a real spaced-repetition mode (interval-based
rather than same-session requeue) as a fourth `QuizMode`, and a `--seed`
flag so Random mode's shuffles are reproducible for grading or debugging.

## Conclusion

The most useful shift in this project was treating AI-generated code as a
first draft to interrogate, not a finished answer to spot-check — asking
"what happens if X never succeeds," "what does this mean when Y repeats,"
and "does this type actually fit every case" surfaced three real bugs that
"it runs and the tests I already wrote pass" would not have caught.
