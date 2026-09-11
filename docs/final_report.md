# AI-Assisted Development Project Report

**Student Name:** Simon
**Project Title:** Flashcard Quizzer CLI
**Date:** 2026-09-12

## Executive Summary

"Flashcard Quizzer" is a terminal-based application that loads question-and-answer pairs from a JSON file and quizzes the user in one of three modes: sequential, random, or adaptive. Answers are evaluated in a case-insensitive manner, providing immediate, color-coded feedback. Upon session completion, a summary is displayed showing the total questions, the accuracy rate, and a list of terms that were answered incorrectly.

I developed this application using Claude Code, following the stages outlined in the specifications (Data Layer → Quiz Engine & Design Patterns → CLI → Testing & Tools). I reviewed the code generated at each stage before execution, rejecting or revising drafts several times; a record of this process is maintained in `docs/ai_edit_log.md`.

## Project Overview

### Problem Definition

New employees needed a way to memorize a glossary of server-related acronyms without relying on GUIs, user accounts, or network connectivity. The requirement was for a tool that runs in any Python-compatible environment, loads JSON files editable even by non-engineers, and enables repetitive practice on terms that are frequently missed.

### Solution Approach

The application is composed of four modules, each with a single responsibility: `models.py` (Flashcard data class), `utils/file_handler.py` (JSON loading and validation), `quiz_engine.py` (strategy, factory, and session loop), and `ui.py` (prompts, color-coding, and summary display). These modules are orchestrated via a CLI in `main.py` using `argparse`. A design decision was to decouple `QuizEngine.run()` from I/O operations like `input()` and `print()`. By designing the system to accept answer-retrieval and feedback-reporting functions as arguments, it is possible to test the grading loop without relying on standard input/output (stdin/stdout).

### Final Features

- [x] Flashcard loading from JSON (array format or `{"cards": [...]}` format)
- [x] Case-insensitive answer evaluation with immediate color-coded feedback
- [x] Three switchable quiz modes implemented using the Strategy pattern
- [x] Adaptive mode that re-presents incorrectly answered cards (with a retry limit via `max_retries`)
- [x] Session summary display: total questions, accuracy rate, and missed terms
- [x] `--stats` flag to save the summary as JSON

These features go beyond the starter kit's basic CRUD capabilities, delivering: pluggable quiz modes, adaptive spaced repetition, immediate grading upon the first attempt, dual-schema data ingestion with validation, and session statistics with export functionality.

## Experience Collaborating with AI

### AI Tools Used

- [x] Claude Code (Sonnet 5; Opus 5 was used for a final review pass)

### Collaboration Workflow

Instead of building the entire application at once, I proceeded in stages. For each prompt, I defined the target functions or classes, their inputs and outputs, and the failure patterns (error modes) that needed to be addressed. Relying on vague instructions like "handle errors appropriately" often results in code that only handles the failure scenarios the developer had in mind. After completing each stage, I reviewed the code and ran tests; I also had Claude run four quality-check tools and fix any issues identified.

### Key Outcomes of AI Collaboration

The following six instances are documented in `docs/ai_edit_log.md`: consolidating loader failures into a `FlashcardLoadError` rather than letting a `KeyError` propagate; identifying and fixing an infinite retry loop in the design of `AdaptiveMode`; decoupling `QuizEngine` from direct I/O operations; fixing a factory type definition error flagged by `mypy` (where `Type[QuizMode]` was incompatible with subclasses having different constructors); clarifying ambiguous adaptive scoring specifications before tests could incorrectly validate wrong answers as correct; and identifying inappropriate type assumptions within tests through a final review pass.

### Challenges in AI Collaboration

A recurring pattern emerged: while Claude implemented features exactly as instructed, prompts that sounded natural in English (e.g., "re-queue missed cards") could sometimes harbor hidden edge cases (e.g., an unlimited retry loop preventing the session from ever ending). The generated code was clean and idiomatic. The risk lay not in sloppy code, but in the AI faithfully implementing specifications that I had defined inadequately.

## Software Engineering Practices

### Commitment to Code Quality

- [x] Code formatting (Black, isort)
- [x] Linting (flake8, mypy)
- [x] Type hinting — Applied to all functions, including tests
- [x] Documentation/Comments — Docstrings written for all modules, classes, and functions
- [x] Error handling — Loader failures displayed as user-facing messages

### Testing Strategy

42 tests were conducted across five files: `test_flashcard_loader.py` (two JSON formats, invalid JSON, missing/empty fields), `test_quiz_modes.py` (factory resolution and rejection, mode ordering, adaptive re-queuing and retry limits), `test_integration.py` (full session, early termination, scoring on first attempt), `test_ui.py` (input handling including Ctrl+C/Ctrl+D/`exit`), and `test_main.py` (CLI parsing and error paths). Overall coverage reached 98%, with 95% for application modules alone, exceeding the 80% target. The decision not to aim for 100% coverage was made because the uncovered lines consist of abstract method bodies, dispatch logic in `__main__`, and two branches requiring filesystem mocking.

### Design Patterns Employed

- **Strategy** — `QuizMode` serves as the interface, with `SequentialMode`, `RandomMode`, and `AdaptiveMode` implemented as algorithms to determine which card to present next. These modes can be swapped without modifying the `QuizEngine`. Since these three modes employ different algorithms while sharing a common operational interface, the Strategy pattern was a perfect fit for the problem at hand; it was not a pattern forced onto unnecessary code.
- **Factory** — Since `QuizModeFactory.create(name, cards)` converts CLI strings into the appropriate instances, `main.py` does not directly import specific mode classes. Adding a new mode—such as "spaced-repetition"—requires only creating a single class and adding one line to the registry.

### Code Structure and Organization

Each module operates independently without directly interfering with the internal implementation of other modules. `main.py` oversees the entire system, `ui.py` handles terminal control, `quiz_engine.py` manages question sequencing and scoring, and `file_handler.py` handles JSON processing. As a result, the two refactoring efforts undertaken were confined to single modules, with no ripple effects on the calling code.

## Technical Challenges and Solutions

### Challenge 1: Terminating Adaptive Mode

**Issue:** The process of "re-queuing incorrect answers" lacks a natural termination condition.
**Solution:** Implement a "maximum retry count" (`max_retries`) limit for each card. **AI Involvement:** Claude initially wrote code lacking a termination condition (creating an infinite loop); however, when asked if the process would terminate, it proposed a fix. **Lesson:** Always verify that any AI-generated retry logic guarantees loop termination.

### Challenge 2: Defining Scoring for Retries

**Issue:** Allowing cards to appear multiple times makes the definition of "accuracy" ambiguous.
**Solution:** Use a `_seen` set to ensure only the "initial attempt" for each card counts toward the score. While retries trigger re-queuing, they do not affect score aggregation. **AI Involvement:** When the ambiguity was pointed out, Claude presented several implementation options. **Lesson:** Since tests might pass regardless of the chosen implementation, resolve behavioral ambiguities before writing the test code.

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
design utilizes callable injection, allowing verification of actual behavior rather than relying on mocks.
Reason for not scoring a 5: One test directly accesses the private attribute `_queue`.
- **Documentation: 5** — README includes usage examples; detailed AI logs;
coverage reports; docstrings provided for all public interfaces.

## Learning Outcomes

### Technical Skills Acquired

By implementing patterns like Strategy and Factory in scenarios where they were required, I gained clarity on when the added complexity of introducing such patterns is justified. I also learned to treat `mypy` not merely as a linter but as a design tool. The type errors related to the Factory pattern that `mypy` flagged revealed issues—signature mismatches. Correcting the types rather than ignoring the errors led to the design of more consistent interfaces.

### Skills in Collaborating with AI

The most valuable practice I adopted was specifying "failure modes" in my prompts and then verifying the generated output against perspectives not covered by the prompt itself (such as "Is this process guaranteed to terminate?"). I discovered more bugs by scrutinizing what I *hadn't* specified than by verifying what I *had* requested.

### Insights into Software Engineering

Applying the principle of "separation of concerns" yielded results; the necessary modifications for this task could all be completed by altering just a single module. I also gained an appreciation for the fact that the effectiveness of quality gates depends on their configuration. Relaxing type checks for the `tests/` directory meant that the code there fell outside the scope of the quality gate, resulting in defects being overlooked.

## Retrospective

### What Went Well

I employed a step-by-step prompting strategy that accounted for common failure patterns, and I treated "running without crashing" as a lower hurdle than "passing code review." I am pleased with the "callable injection" design used in `QuizEngine.run()`; this made testing the app's most difficult-to-test component easy.

### Areas for Improvement

I should have designed the system with Dependency Injection (DI) from the start rather than refactoring to introduce it later. Regarding quality assurance tools, I should have run them with the strictest settings from the first commit, rather than discovering later that issues had been overlooked due to loose configurations.

### Planned Future Extensions

I am considering adding a "spaced-repetition" mode to maintain intervals across sessions, a `--seed` flag to make random mode behavior reproducible, and per-card history tracking (which will enable adaptive mode to prioritize cards based on data spanning multiple sessions, rather than just within a single session).

## Conclusion

A turning point was shifting from treating AI output as a "finished answer requiring only partial verification" to viewing it as a "draft requiring critical scrutiny." By asking questions such as "What if X never succeeds?", "What are the implications if Y repeats?", and "Does this pattern fit every scenario?", I was able to uncover three flaws that might otherwise have been overlooked—flaws that existed even though the program functioned correctly and passed all tests. I intend to maintain this habit of verifying details beyond the specifications in future work, regardless of whether AI generates the draft.

## Appendix

### Appendix A: AI Interaction Log

`docs/ai_edit_log.md` — Six detailed records.

### Appendix B: Code Statistics

`docs/coverage_report.md` — Overall coverage output, per-file breakdown, and explanations for uncovered lines. The HTML report is located at `htmlcov/index.html`, and the prompt history is in `prompts.md`.

### Appendix C: Additional Resources

`ai_guidance/prompting_best_practices.md` and `ai_guidance/code_review_checklist.md` (used during reviews), `docs/design_patterns.md`, and documentation regarding Python's `abc`, `argparse`, and `dataclasses` modules.
