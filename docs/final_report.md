# AI-Assisted Development Project Report

**Student Name:** Simon
**Project Title:** Flashcard Quizzer CLI
**Date:** 2026-09-12

## Executive Summary

The Flashcard Quizzer is a terminal application that loads question/answer
pairs from a JSON file and quizzes the user in one of three modes:
Sequential, Random, or Adaptive. It checks answers case-insensitively,
gives immediate colored feedback, and ends with a session summary of total
questions, accuracy, and missed terms.

I built it end-to-end with Claude Code, in the phases the brief lays out:
data layer, then quiz engine and design patterns, then CLI, then tests and
tooling. At each phase I reviewed the generated code before running it, and
several times rejected or corrected the first draft — a record kept in
`docs/ai_edit_log.md`.

## Project Overview

### Problem Statement

New hires need a low-friction way to memorize a glossary of server acronyms
with no GUI, account, or network dependency — something that runs anywhere
Python does, reads a JSON file a non-engineer can edit, and drills the
terms they keep getting wrong.

### Solution Approach

Four modules, one job each: `models.py` (the `Flashcard` dataclass),
`utils/file_handler.py` (JSON loading and validation), `quiz_engine.py`
(strategies, factory, session loop), and `ui.py` (prompts, color, summary),
wired by `main.py`'s argparse CLI. The key decision was keeping
`QuizEngine.run()` decoupled from `input()`/`print()`: it takes an
answer-getter and feedback-reporter as parameters, making the scoring loop
testable without stdin/stdout.

### Final Features

- [x] Load flashcards from JSON in array or `{"cards": [...]}` form
- [x] Case-insensitive answer checking with immediate colored feedback
- [x] Three interchangeable quiz modes via the Strategy pattern
- [x] Adaptive mode that requeues missed cards, bounded by `max_retries`
- [x] Session summary: total questions, accuracy %, missed terms
- [x] `--stats` flag to persist the summary as JSON

Five go beyond the starter's basic CRUD: pluggable quiz modes, adaptive
repetition, first-attempt scoring, dual-schema ingestion with validation,
and session statistics with export.

## AI Collaboration Experience

### AI Tools Used

- [x] Claude Code (Sonnet 5, then Opus 5 for the final rubric audit)

### Collaboration Workflow

I worked phase by phase rather than requesting the whole app at once. Each
prompt named the exact function or class, its inputs and outputs, and the
failure modes it had to handle — since "handle errors gracefully" alone
produces code handling only the failures the author imagined. After each
phase I read the code, ran the tests, then had Claude run the four quality
tools and fix what they flagged.

### Most Valuable AI Interactions

Six are documented in `docs/ai_edit_log.md`: consolidating loader failures
into one `FlashcardLoadError` instead of a leaked `KeyError`; catching an
unbounded retry loop in the first `AdaptiveMode` draft; decoupling
`QuizEngine` from direct I/O; fixing a `mypy` factory-typing error
(`Type[QuizMode]` doesn't fit subclasses with differing constructors);
resolving ambiguous Adaptive scoring before tests locked in the wrong
answer; and a rubric audit catching an unsound type assumption in tests.

### Challenges with AI Collaboration

One pattern recurred: Claude implements exactly what the prompt specifies,
but a prompt that sounds complete in English ("requeue a card when it's
wrong") can hide an edge case (no retry limit, so the session never ends).
The generated code was consistently clean and idiomatic — the risk was
never sloppiness, it was faithfully building what I under-specified.

## Software Engineering Practices

### Code Quality Measures

- [x] Code formatting (Black, isort)
- [x] Linting (flake8, mypy)
- [x] Type hints — every function, including tests
- [x] Documentation/comments — docstrings on every module, class, function
- [x] Error handling — loader failures become user-facing messages

### Testing Strategy

42 tests across five files: `test_flashcard_loader.py` (both JSON shapes,
invalid JSON, missing/blank fields), `test_quiz_modes.py` (factory
resolution and rejection, mode ordering, adaptive requeue and retry limit),
`test_integration.py` (full session, early exit, first-attempt scoring),
`test_ui.py` (input handling including Ctrl+C/Ctrl+D/`exit`), and
`test_main.py` (CLI parsing and error paths). Coverage is 98% overall, 95%
on application modules, against an 80% target. I didn't chase 100%: the ten
uncovered lines are abstract-method bodies, the `__main__` dispatch, and
two branches needing filesystem mocking — each justified in
`docs/coverage_report.md`.

### Design Patterns Used

- **Strategy** — `QuizMode` is the interface; `SequentialMode`,
  `RandomMode`, and `AdaptiveMode` are interchangeable algorithms for "what
  card comes next," swappable without touching `QuizEngine`. I chose it
  because the three modes are the same operation with different algorithms,
  exactly the problem Strategy solves — not a pattern imposed on code that
  didn't need one.
- **Factory** — `QuizModeFactory.create(name, cards)` turns a CLI string
  into the right instance, so `main.py` never imports a concrete mode class.
  Adding a spaced-repetition mode means one class plus one registry entry.

### Code Structure and Organization

No module reaches into another's internals: `main.py` orchestrates, `ui.py`
owns the terminal, `quiz_engine.py` owns ordering and scoring,
`file_handler.py` owns JSON. That is why both major refactors each touched
a single module without rippling to callers.

## Technical Challenges and Solutions

### Challenge 1: Terminating Adaptive mode

**Problem:** "Requeue wrong answers" has no natural end condition.
**Solution:** A `max_retries` budget per card. **AI Involvement:** Claude
wrote the unbounded version, then the fix once asked whether it terminates.
**Lessons Learned:** Ask "does this loop always end?" of any AI-generated
retry logic.

### Challenge 2: Scoring semantics under retries

**Problem:** Once a card can appear twice, "accuracy" is ambiguous.
**Solution:** Score each card on its first attempt via a `_seen` set;
retries still drive requeueing but don't touch the tally. **AI
Involvement:** Claude surfaced both options once I raised the ambiguity.
**Lessons Learned:** Settle behavioral ambiguity before writing tests,
since either version passes its own.

## Code Quality Analysis

### Metrics

- **Lines of code:** 654 excluding blanks/comments — 345 application, 309 tests
- **Test coverage:** 98% overall, 95% on application modules
- **Functions/classes:** 28 functions and 9 classes in the application;
  47 test functions
- **Linting score:** zero errors from `black`, `isort`, `flake8`, `mypy`
  (the last with `disallow_untyped_defs` on project-wide)

### Self-Assessment

- **Code Readability: 5** — short single-responsibility modules,
  descriptive names, docstrings throughout, no function over ~25 lines.
- **Code Maintainability: 5** — adding a mode takes one class and one
  registry line; the pattern choice is load-bearing, not decorative.
- **Test Quality: 4** — edge cases and error paths well covered, and the
  injected-callable design lets tests assert real behavior rather than
  mocks. Not a 5: one test reaches into a private `_queue` attribute.
- **Documentation: 5** — README with usage examples, detailed AI log,
  justified coverage report, docstrings on every public surface.

## Learning Outcomes

### Technical Skills Developed

Implementing Strategy and Factory on a problem that genuinely needed them
clarified when a pattern earns its complexity. I also learned to treat mypy
as a design tool rather than a linter: the factory-typing error it caught
was a real signature mismatch, and fixing the type instead of suppressing
it forced a more honest interface.

### AI Collaboration Skills

The most useful habit was specifying failure modes in the prompt, then
interrogating the result with questions the prompt didn't cover ("does this
terminate?"). Reviewing what I *hadn't* specified caught more bugs than
reviewing what I had.

### Software Engineering Insights

Separation of concerns paid off concretely: every correction here was a
one-module change. And a quality gate is only as strong as its config —
relaxing type checking for `tests/` moved that code outside the gate and
hid a real defect.

## Reflection

### What Worked Well

Phase-by-phase prompting with explicit failure modes, and treating "runs
without crashing" as a much lower bar than "passes review." The
injected-callable design for `QuizEngine.run()` is what I'm most pleased
with — it made the hardest-to-test part of the app trivial to test.

### What Could Be Improved

I should have asked for dependency injection up front instead of
refactoring into it, and run the quality tools at full strictness from the
first commit rather than discovering late that a relaxed setting was
masking a defect.

### Future Enhancements

A spaced-repetition mode with intervals persisted across sessions; a
`--seed` flag making Random mode reproducible; and per-card history so
Adaptive mode can prioritize across sessions, not just within one.

## Conclusion

The shift that mattered was treating AI output as a first draft to
interrogate rather than a finished answer to spot-check. Asking "what if X
never succeeds," "what does this mean when Y repeats," and "does this type
fit every case" surfaced three real defects that "it runs and my tests
pass" would not have caught. I'll carry the habit of reviewing for the
unspecified into future work, with or without an AI writing the draft.

## Appendices

### Appendix A: AI Interaction Log

`docs/ai_edit_log.md` — six detailed entries. Most consequential: the
`AdaptiveMode` infinite-loop fix, the `QuizEngine` I/O decoupling, and the
rubric audit that caught unsound `Optional[Flashcard]` handling in tests.

### Appendix B: Code Statistics

`docs/coverage_report.md` — full coverage output, per-file breakdown, and a
justification for each uncovered line. HTML report at `htmlcov/index.html`;
prompt sequence in `prompts.md`.

### Appendix C: Additional Resources

`ai_guidance/prompting_best_practices.md` and
`ai_guidance/code_review_checklist.md` (used during review),
`docs/design_patterns.md`, and the Python `abc`/`argparse`/`dataclasses` docs.
