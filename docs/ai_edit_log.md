# AI Editing Log — Flashcard Quizzer

This log records the specific prompts used to build "Flashcard Quizzer" with Claude Code, Claude's outputs, and the points where the initial draft was reviewed, modified, or rejected before final adoption. Please refer to `prompts.md` at the repository root for a summary of prompts, and `ai_guidance/code_review_checklist.md` for the checklist used during reviews.

---

## Data Loader Error Handling

**Background:** A `utils/file_handler.py` module was required to load flashcards from JSON. The JSON format needed to support either a raw array (list) or a structure like `{"cards": [...]}`. In accordance with the "crash gracefully" rule in the specifications, the code had to fail by displaying a clear, understandable message rather than exposing a raw traceback.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Create a `load_flashcards(filepath)` function that accepts either a JSON array of `{front, back}` objects or an object with a top-level `cards` array. Validate that the `front` and `back` strings for each card are non-empty, and ensure that `json.JSONDecodeError`, `FileNotFoundError`, and `KeyError` do not propagate to the caller as raw tracebacks."

**AI Response:** Claude's initial draft successfully caught `json.JSONDecodeError` and `FileNotFoundError`. However, issues regarding missing fields resulted in a raw `KeyError(f"Card {i} missing 'back'")` being re-raised, as the code used direct dictionary access (`raw["back"]`) instead of `.get()`.

**Changes Made:** Instead of using raw `KeyError` exceptions, the code was modified to use a single custom exception, `FlashcardLoadError`, for all failure scenarios (missing file, invalid JSON, incorrect top-level structure, or missing/empty fields). Each exception now includes a human-readable message containing the filename and (where applicable) the card number. Additionally, the code was modified to use `.get()` instead of direct access, ensuring a custom message is displayed rather than leaking a raw `KeyError` when a key is missing.

**Reasoning:** To meet the requirement of "crashing gracefully with a helpful message instead of a stack trace," it was necessary to unify the exception types caught at the CLI boundary within `main.py`. If a `KeyError` were allowed to bubble up, it would result in the output of a traceback—something the specifications aim to avoid. Furthermore, the error message itself (e.g., `'back'`) is meaningless to the average end-user who is not a developer.

**Result:** A single exception-handling block—`except (FlashcardLoadError, ValueError)`—was implemented in `main.py`. Additionally, all invalid input scenarios (missing files, invalid JSON, missing 'front' or 'back' fields, empty fields, malformed structures, non-object card entries, etc.) are now directly tested in `tests/test_flashcard_loader.py`.

**Lesson Learned:** When asking AI to implement "graceful error handling," you must explicitly state the need to catch *all* exception types and convert them into the appropriate format. Otherwise, the initial output often handles only the specific exception types mentioned in the prompt, overlooking others—such as the `KeyError` caused by direct index access in this instance.

## Risk of Infinite Loop in Adaptive Mode

**Background:** Implementation of `AdaptiveMode`, a "challenge feature" that prioritizes presenting cards the user previously answered incorrectly.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Implement `AdaptiveMode(QuizMode)` so that whenever a user answers incorrectly, the card is returned to the end of the deck. This ensures that incorrectly answered cards are presented repeatedly until the user gets them right."

**AI Response:** Implementing that request literally removes the upper limit for the termination condition. Since a card answered incorrectly would be returned to the deck indefinitely, `has_next()` would never return `False` as long as there was even a single card the user couldn't answer correctly. Consequently, the quiz session would never end during unattended execution or scripted processing (or if the user became unable to interact with the system).

**Changes Made:** I rejected the implementation without limits and added a `max_retries` parameter (default: 2) along with a `_retry_counts` dictionary keyed by the card's "front" content. This ensures that an incorrectly answered card is returned to the deck only if retry attempts remain.

**Rationale:** A quiz mode capable of looping forever is a "bug," not a feature. "Prioritizing" should mean "re-presenting a limited number of times," not "preventing the session from ever ending." Setting a limit on retries also facilitated testing (specifically, `test_adaptive_mode_stops_retrying_after_max_retries`). Without a limit, the test itself would have required an arbitrary cap on the number of iterations.

**Result:** `AdaptiveMode` is now guaranteed to terminate. This behavior is verified by three unit tests in `test_quiz_modes.py`, including a test confirming that the deck empties after `max_retries + 1` incorrect answers.

**Lesson:** When an AI-generated process involves queues or retry loops, you should explicitly verify that termination is guaranteed before adopting it. A requirement to "repeat until successful" may seem natural at first glance, but taking it literally can harbor the pitfall of an infinite loop.

---

## Issue: Tight Coupling of `QuizEngine` with `input()` and `print()`

**Background:** I was working on integrating `QuizMode` and `QuizModeFactory` into an executable session loop (`QuizEngine`).

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Create a `QuizEngine` class that loops until `QuizMode` finishes, prompts the user for input, displays feedback on correctness, and finally returns session statistics (total questions, accuracy rate, and missed terms)."

**AI Response:** The initial draft called `input()` and `print()` directly within `QuizEngine.run()`. While this worked for manual execution, it meant that performing the required unit test for the full session loop (`test_full_session`) would necessitate monkey-patching the built-in `input` and capturing standard output with `capsys`. This was a fragile and indirect testing approach for a critical component: the scoring logic.

**Changes Made:** I refactored the `run()` method to accept two injected callables—`ask_answer(card) -> Optional[str]` and `report_feedback(card, correct) -> None`—instead of calling `input` and `print` directly. The actual implementations for `input()` and the `print()` calls (handling colored output) were moved to `ui.py`, with the coordination logic placed solely in `main.py`.

**Reasoning:** To achieve Separation of Concerns. `QuizEngine` should handle scoring logic, not terminal I/O. This change allowed `test_integration.py::test_full_session` to be implemented as a simple functional test—passing a list of answers via an iterator and asserting the returned `SessionStats`—rather than relying on slow, indirect subprocesses or heavy use of monkey-patching.

**Result:** It is now possible to execute `QuizEngine.run()` directly using dummy callables across `test_full_session`, `test_session_stops_early_when_user_exits`, and all integration tests for adaptive mode. Mocking I/O is no longer necessary; the production-grade `ui.ask_answer` and `ui.report_feedback` pair is now tested separately and more thoroughly in `test_ui.py`.

**Lesson Learned:** When AI-generated code mixes business logic with I/O, the standard approach for remediation is to employ "Dependency Injection (DI) at the boundaries." Rather than refactoring later, it is wiser to explicitly require this architecture from the start—such as by designing functions to accept I/O operations as parameters.

---

## Issue: Factory Registry Type Definition Was Too Restrictive for mypy

**Background:** This issue arose when running `mypy .` as part of the "Definition of Done" quality gate after implementing `QuizModeFactory`.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Run `mypy` and `flake8` across the entire project and fix any errors."

**AI Response:** `mypy` reported a "Too many arguments for 'QuizMode'" error on the line calling `mode_class(cards)` within `QuizModeFactory.create`. Because the registry type was defined as `Dict[str, Type[QuizMode]]`, `mypy` was validating the calls against the abstract base class's constructor (which takes no arguments) rather than the actual `__init__(self, cards)` signatures of the concrete subclasses.

**Changes Made:** I updated the registry type definition to `Dict[str, Callable[[List[Flashcard]], QuizMode]]`. This accurately represents a "callable that accepts a list of flashcards and returns a `QuizMode`" and is compatible with the constructor signatures of all concrete classes (this definition works fine even for `RandomMode`, as its optional `rng` argument has a default value).

**Reasoning:** This was not a `mypy` false positive but a genuine lack of type safety. The type definition `Type[QuizMode]` is technically correct only when all subclasses share the base class's constructor signature; in this case, however, none of the subclasses did so. If I had suppressed the error using `# type: ignore`, I risked overlooking actual bugs—such as constructor mismatches—that could arise if a mode added in the future required incompatible arguments for its `__init__` method.

**Result:** Running `mypy .` without suppressing errors via `# type: ignore` yielded zero errors across the entire project (`Success: no issues found in 12 source files`).

**Lesson Learned:** For factory or registry patterns that map names to classes, you should define types using the constructor's `Callable` signature rather than `Type[Base]`, unless it is guaranteed that all subclasses share the base class's constructor.

---

## Scoring Definition in Adaptive Mode Was Ambiguous

**Background:** The issue of how to define "Total Questions" and "Accuracy %" in "Adaptive Mode," where the same card might appear multiple times within a single session.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "In Adaptive Mode, if a user answers a card incorrectly but answers it correctly when it appears again later, should the session statistics count this as one question or two? Also, should it be treated as a correct answer, an incorrect answer, or both?"

**AI Response:** Claude proposed two options: (a) Count each presentation as a separate question (meaning a retried card contributes to the tally as both an incorrect answer and a subsequent correct answer), or (b) Count each card as a unique item only once and determine the score based on the initial attempt (subsequent presentations affect only whether the card continues to reappear).

**Changes Made:** Option (b) was adopted. The `QuizEngine` maintains a `_seen` set to track cards (specifically their "front" sides) that have already been presented; it updates `total_questions`, `correct`, and `missed_terms` only when a specific card is presented for the first time. While `record_result` is still executed for subsequent presentations triggered by Adaptive Mode, the statistical data remains unchanged.

**Reasoning:** With option (a), a user could repeatedly answer the same card until getting it right and have those subsequent correct answers counted, artificially inflating their accuracy rate. This approach fails to accurately reflect the user's level of understanding at the time they first encountered the card. Furthermore, it makes it impossible to compare accuracy rates between Adaptive Mode and Sequential or Random modes using the same deck.

**Result:** The specification was documented in the `QuizEngine.run()` docstring and explicitly verified via the test case `test_full_session_with_adaptive_mode_scores_first_attempt_only`. This test confirms that if a card is answered incorrectly and then correctly, the item remains in `missed_terms` while the `correct` count is recorded as 1 rather than 2.

**Lesson Learned:** Ambiguous scoring rules are design decisions that should be resolved with the AI—or otherwise explicitly clarified—*before* writing tests. This is because, while multiple approaches might result in "correct code," only one aligns with the intended product behavior.

---

## Final Review Reveals Inappropriate Type Assumptions in Tests

**Background:** Before submission, instead of assuming all requirements were met based solely on the previous "all tools passed tests" result, the completed project was reviewed line by line against the assignment specification.

**AI Tool Used:** Claude Code (Opus 5)

**Prompt/Request:** "Compare the requirements and output in `final-final-project.txt`. Verify by comparing the actual file with each requirement, rather than relying on memory."

**AI Response:** Auditing using an AST (Abstract Syntax Tree) script, rather than visual inspection, revealed four issues that would have been overlooked with a simple read-through. Specifically, 16 methods in `quiz_engine.py` lacked docstrings (documentation strings), 45 test functions lacked type hints (the specification requires hints for *all* functions), test names did not perfectly match the `test_quiz_mode_factory` and `test_adaptive_mode_behavior` specified in the specification, and the coverage report was not committed to the repository (because `htmlcov/` was included in `.gitignore` as a build artifact, even though it was listed as an artifact in the submission checklist).

**Changes made:** Added missing docstrings. Added type hints to all test functions and re-enabled `disallow_untyped_defs` for the `tests/` directory to ensure strict mypy checks are performed throughout the project. Additionally, we added a `test_quiz_mode_factory` test to verify that the factory returns the correct class for all three names, and changed the adaptive mode test names to match the specification. Furthermore, we committed a coverage report and documented its contents in `docs/coverage_report.md`.

**Reason:** Enabling strict type checking for the tests wasn't just a formality. Immediately after enabling it, we encountered 11 errors. This indicated that the `Optional[Flashcard]` returned by `get_next_card()` was being passed directly to a method that required a `Flashcard` that was not `Optional` (i.e., did not allow `None`). The tests had passed until then simply because the deck (stack of cards) happened not to be empty at that point. Therefore, we added a `next_card()` helper function with a type definition that guarantees it's not `None`. This ensures that the preconditions are explicitly verified, rather than relying on mere "chance success."

**Results:** All 42 tests passed, achieving 98% coverage. Checks by `black`, `flake8`, and `mypy` all passed, demonstrating that mypy's rigorous checks are applied not only to source code but also to test code.

**Lesson Learned:** Even if a tool "passes everything," it's ultimately dependent on runtime settings. Relaxing rules for a specific directory (in this case, type checking in `tests/`) can inadvertently slip that code outside the quality check network (quality gate). It's worth periodically rerunning checks with the strictest settings to see the impact of exceptions.

---

## Statistical Data

- **Total number of detailed AI interactions:** 6 (excluding the continuous "decompose → generate → review → improve" cycle documented in `prompts.md`).
- **Lines of AI-generated code:** 654 lines (345 lines for the application + 309 lines for tests; excluding blank lines and comments). All code in this project was generated by AI; no code was hand-written from scratch, as the process followed the instruction to revise prompts rather than directly rewriting Python code.
- **Lines of AI-generated code modified:** 159 lines were altered during the recorded review process (audit commits alone involved 105 insertions and 54 deletions). This figure also includes corrections made during sessions prior to the initial commit (e.g., consolidating `FlashcardLoadError`, setting retry limits for `AdaptiveMode`, changing the `QuizEngine.run()` signature from direct I/O to injectable callables, and fixing `Callable` type definitions in the factory). Approximately one-quarter of the code was modified after review rather than being adopted in its initial draft form.
- **Most beneficial AI interaction:** Decoupling `QuizEngine` from the UI. This made it easy to test the part of the app that was previously the most difficult to test: the session loop that prompts for user input.
- **Most challenging AI interaction:** Determining the scoring specifications (semantics) for Adaptive Mode. While writing the code for either approach was simple, only one method resulted in the correct behavior for the actual product.
- **Key takeaway:** AI agents faithfully implement exactly what the user instructs. This includes edge cases the user forgot to exclude—such as infinite retry loops, unexpected `KeyError` exceptions, or `Type[Base]` annotations that were inconsistent with the constructor. Therefore, during the review, it is necessary to verify not only that the code meets the specified requirements but also to check the aspects that were *not* specified.
