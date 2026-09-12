# AI-Assisted Development Project Report

**Student Name:** Simon
**Project Title:** Flashcard Quizzer CLI
**Date:** 2026-09-12

## Executive Summary

"Flashcard Quizzer" is a terminal-based application that loads question-and-answer pairs from a JSON file and quizzes the user in one of three modes: sequential, random, or adaptive. Answers are evaluated case-insensitively with immediate, color-coded feedback, and it ends with a summary of total questions, accuracy rate, and missed terms.

I built this with Claude Code, in stages (Data Layer → Quiz Engine & Design Patterns → CLI → Testing & Tools), reviewing and revising generated code at each stage; that process is recorded in `docs/ai_edit_log.md`.

## Project Overview

### Problem Definition

New employees needed to memorize a glossary of server acronyms without a GUI, an account, or a network dependency — something that runs anywhere Python does, reads a JSON file a non-engineer can edit, and drills the terms they keep getting wrong.

### Solution Approach

The application is composed of four modules, each with a single responsibility: `models.py` (Flashcard data class), `utils/file_handler.py` (JSON loading and validation), `quiz_engine.py` (strategy, factory, and session loop), and `ui.py` (prompts, color-coding, and summary display). These modules are orchestrated via a CLI in `main.py` using `argparse`. A design decision was to decouple `QuizEngine.run()` from I/O operations like `input()` and `print()`. By designing the system to accept answer-retrieval and feedback-reporting functions as arguments, it is possible to test the grading loop without relying on standard input/output (stdin/stdout).

### Final Features

- [x] Flashcard loading from JSON (array format or `{"cards": [...]}` format)
- [x] Case-insensitive answer evaluation with immediate color-coded feedback
- [x] Three switchable quiz modes implemented using the Strategy pattern
- [x] Adaptive mode that re-presents incorrectly answered cards (with a retry limit via `max_retries`)
- [x] Session summary display: total questions, accuracy rate, and missed terms
- [x] `--stats` flag to save the summary as JSON

These features go beyond the starter kit's basic CRUD: pluggable quiz modes, adaptive spaced repetition, first-attempt grading, dual-schema data ingestion with validation, and session statistics with export.

## Experience Collaborating with AI

### AI Tools Used

- [x] Claude Code (Sonnet 5; Opus 5 was used for a final review pass)

### Collaboration Workflow

I worked in stages rather than requesting the whole app at once, specifying each function's inputs, outputs, and failure modes explicitly — vague prompts like "handle errors appropriately" tend to produce code that only covers the failures the author already thought of. After each stage I reviewed the code, ran tests, and had Claude run the quality tools.

### Key Outcomes of AI Collaboration

Six instances are documented in `docs/ai_edit_log.md`: consolidating loader failures into one `FlashcardLoadError` instead of a leaked `KeyError`; fixing an infinite retry loop in the design of `AdaptiveMode`; decoupling `QuizEngine` from direct I/O operations; fixing a `mypy` factory-typing error (`Type[QuizMode]` doesn't fit subclasses with differing constructors); resolving ambiguous Adaptive scoring before tests locked in the wrong answer; and a final review pass catching an unsound type assumption in tests.

### Challenges in AI Collaboration

A recurring pattern: Claude implemented features exactly as instructed, but prompts that sounded natural in English (e.g., "re-queue missed cards") could hide edge cases like an unlimited retry loop. The code itself was clean and idiomatic — the risk was specifications I had defined inadequately, not sloppy AI output.

## Software Engineering Practices

### Commitment to Code Quality

- [x] Code formatting (Black, isort)
- [x] Linting (flake8, mypy)
- [x] Type hinting — Applied to all functions, including tests
- [x] Documentation/Comments — Docstrings written for all modules, classes, and functions
- [x] Error handling — Loader failures displayed as user-facing messages

### Testing Strategy

42 tests were conducted across five files: `test_flashcard_loader.py` (two JSON formats, invalid JSON, missing/empty fields), `test_quiz_modes.py` (factory resolution and rejection, mode ordering, adaptive re-queuing and retry limits), `test_integration.py` (full session, early termination, scoring on first attempt), `test_ui.py` (input handling including Ctrl+C/Ctrl+D/`exit`), and `test_main.py` (CLI parsing and error paths). Coverage: 98% overall, 95% on application modules (target: 80%). 100% coverage wasn't the goal: the uncovered lines are abstract method bodies, `__main__` dispatch logic, and two branches needing filesystem mocking.

### Design Patterns Employed

- **Strategy** — `QuizMode` serves as the interface, with `SequentialMode`, `RandomMode`, and `AdaptiveMode` implemented as algorithms to determine which card to present next. These modes can be swapped without modifying the `QuizEngine`, since they share an interface but use different algorithms — exactly the problem Strategy solves, not a pattern forced onto code that didn't need one.
- **Factory** — `QuizModeFactory.create(name, cards)` converts CLI strings into instances, so `main.py` never imports a concrete mode class. Adding a mode—e.g. spaced-repetition—means one new class and one registry line.

### Code Structure and Organization

Each module has one job: `main.py` orchestrates, `ui.py` handles terminal I/O, `quiz_engine.py` handles ordering and scoring, and `file_handler.py` handles JSON. As a result, both refactors so far were confined to a single module, with no ripple effects on callers.

## Technical Challenges and Solutions

### Challenge 1: Terminating Adaptive Mode

**Issue:** "Re-queuing incorrect answers" has no natural end condition.
**Solution:** A `max_retries` limit per card. **AI Involvement:** Claude wrote the unbounded version first; asked whether it would terminate, it proposed the fix. **Lesson:** Verify any AI-generated retry logic actually terminates.

### Challenge 2: Defining Scoring for Retries

**Issue:** Once a card can appear twice, "accuracy" is ambiguous.
**Solution:** A `_seen` set scores only each card's first attempt; retries still requeue but don't affect the tally. **AI Involvement:** Claude offered several options once the ambiguity was raised. **Lesson:** Resolve behavioral ambiguity before writing tests—either version can pass.

## Code Quality Analysis

### Metrics

- **Lines of Code:** 654 lines (excluding blank lines and comments) — 345 lines for the application, 309 lines for tests.
- **Test Coverage:** 98% overall; 95% for application modules.
- **Functions & Classes:** 28 functions and 9 classes in the application; 47 test functions.
- **Linting Score:** Zero errors across `black`, `isort`, `flake8`, and `mypy`
(`mypy` configured with `disallow_untyped_defs` enabled project-wide).

### Self-Assessment

- **Code Readability: 5** — Concise modules adhering to the Single Responsibility Principle,
clear naming conventions, comprehensive docstrings, and no functions exceeding 25 lines.
- **Code Maintainability: 5** — Adding a mode requires only one new class and a single-line addition to the registry;
the adopted patterns are central to the design, not merely decorative.
- **Test Quality: 4** — Thorough coverage of edge cases and error paths;
the injected-callable design lets tests assert real behavior rather than mocks.
Not a 5: one test reaches into the private `_queue` attribute.
- **Documentation: 5** — README includes usage examples; detailed AI logs;
coverage reports; docstrings provided for all public interfaces.

## Learning Outcomes

### Technical Skills Acquired

Implementing Strategy and Factory where they were actually needed clarified when that complexity is justified. I also learned to treat `mypy` as a design tool, not just a linter: the Factory type error it flagged was a real signature mismatch, and fixing it produced a more honest interface.

### Skills in Collaborating with AI

The most valuable habit was specifying failure modes in prompts, then interrogating the result with questions the prompt didn't cover (such as "does this terminate?"). Reviewing what I *hadn't* specified caught more bugs than reviewing what I had.

### Insights into Software Engineering

Separation of concerns paid off concretely: every fix in this project was a one-module change. And a quality gate is only as strong as its configuration — relaxing type checks for `tests/` moved that code outside the gate and hid a real defect.

## Retrospective

### What Went Well

Step-by-step prompting that accounted for failure patterns, and treating "running without crashing" as a lower bar than "passing review." I'm most pleased with the callable-injection design in `QuizEngine.run()` — it made the hardest-to-test part of the app trivial to test.

### Areas for Improvement

I should have designed in Dependency Injection from the start instead of refactoring it in later, and run the quality tools at full strictness from the first commit instead of discovering a relaxed setting had hidden a defect.

### Planned Future Extensions

A spaced-repetition mode with intervals persisted across sessions, a `--seed` flag for reproducible Random mode, and per-card history so Adaptive mode can prioritize across sessions, not just within one.

## Conclusion

The key shift was treating AI output as a draft to interrogate, not a finished answer to spot-check. Asking "what if X never succeeds," "what happens when Y repeats," and "does this fit every case" surfaced three real flaws that "it runs and passes tests" would not have caught. I'll carry that habit — reviewing for the unspecified — into future work, AI-drafted or not.

## Appendix

### Appendix A: AI Interaction Log

`docs/ai_edit_log.md` — Six detailed records.

### Appendix B: Code Statistics

`docs/coverage_report.md` — coverage output, per-file breakdown, explanations for uncovered lines. HTML report: `htmlcov/index.html`. Prompt history: `prompts.md`.

### Appendix C: Additional Resources

`ai_guidance/prompting_best_practices.md`, `ai_guidance/code_review_checklist.md`, `docs/design_patterns.md`, and Python's `abc`, `argparse`, `dataclasses` docs.
