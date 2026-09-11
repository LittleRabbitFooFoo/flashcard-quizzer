# AI Edit Log — Flashcard Quizzer

This log documents the specific prompts used to build the Flashcard Quizzer
with Claude Code, what Claude produced, and where its first draft was
reviewed, corrected, or rejected before being accepted. See `prompts.md` at
the repository root for the condensed prompt sequence, and
`ai_guidance/code_review_checklist.md` for the checklist used during review.

---

## 2026-09-11 — Data loader error handling

**Context:** Needed `utils/file_handler.py` to load flashcards from JSON in
either the array or `{"cards": [...]}` shape, and to fail with a friendly
message rather than a traceback per the spec's "crash gracefully" rule.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Write a `load_flashcards(filepath)` function that
accepts either a JSON array of `{front, back}` objects or an object with a
top-level `cards` array. It must validate every card has non-empty `front`
and `back` strings, and never let `json.JSONDecodeError`, `FileNotFoundError`,
or a `KeyError` reach the caller as a raw traceback."

**AI Response:** Claude's first draft caught `json.JSONDecodeError` and
`FileNotFoundError` but re-raised missing-field problems as a bare
`KeyError(f"Card {i} missing 'back'")`, and used `raw["back"]` (dict
indexing) rather than `.get()`.

**Changes Made:** Replaced the bare `KeyError` with a single custom
`FlashcardLoadError` exception used for every failure mode (missing file,
bad JSON, wrong top-level shape, missing/blank field), each with a
human-readable message naming the file and, where relevant, the card
number. Switched to `.get()` so a missing key produces our own message
instead of leaking a raw `KeyError`.

**Reasoning:** `main.py` needs one exception type to catch at the CLI
boundary to satisfy "crash gracefully with a helpful message, not a stack
trace." A `KeyError` bubbling out would print exactly the traceback the spec
says to avoid, and its message ("`'back'`") is meaningless to a non-developer
end user.

**Outcome:** `main.py` now has a single `except (FlashcardLoadError,
ValueError)` block; every malformed-input path was covered directly in
`tests/test_flashcard_loader.py` (missing file, invalid JSON, missing
front/back, blank field, wrong shape, non-object card).

**Lessons Learned:** When asking an AI for "graceful error handling," be
explicit that *every* exception type must be caught and translated — the
first pass will usually handle the exception types you named in the prompt
and miss the ones you didn't (here, `KeyError` from direct indexing).

---

## 2026-09-11 — Adaptive mode risked an infinite loop

**Context:** Implementing `AdaptiveMode`, the "challenge feature" that
should "prioritize cards the user previously got wrong."

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Implement `AdaptiveMode(QuizMode)` that requeues a card
to the back of the deck whenever the user gets it wrong, so missed cards
keep coming back until answered correctly."

**AI Response:** The literal implementation of that request has no upper
bound: a card the user keeps answering wrong gets requeued forever, so
`has_next()` never returns `False` if even one card is never answered
correctly. In an unattended/scripted context (or a stuck user) the quiz
session would never terminate.

**Changes Made:** Rejected the unbounded version and added a `max_retries`
parameter (default 2) with a `_retry_counts` dict keyed by card front; a
wrong answer only requeues the card while it has retries remaining.

**Reasoning:** A quiz mode that can loop forever is a functional bug, not a
feature — "prioritize" should mean "ask again a bounded number of times,"
not "never let the session end." Bounding retries also made the mode
trivially testable (`test_adaptive_mode_stops_retrying_after_max_retries`)
where the unbounded version would have required an arbitrary iteration cap
in the test itself.

**Outcome:** `AdaptiveMode` now guarantees termination and the behavior is
covered by three targeted unit tests in `test_quiz_modes.py`, including one
that answers a card wrong `max_retries + 1` times and asserts the deck is
finally exhausted.

**Lessons Learned:** When an AI-generated behavior involves a queue/retry
loop, explicitly check for a termination guarantee before accepting it —
"repeat until correct" is a natural-sounding requirement that hides an
unbounded loop if taken literally.

---

## 2026-09-11 — QuizEngine was tightly coupled to `input()`/`print()`

**Context:** Wiring `QuizMode` + `QuizModeFactory` into a runnable session
loop (`QuizEngine`).

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Write a `QuizEngine` class that loops over a `QuizMode`
until it's exhausted, asking the user for input and printing correct/
incorrect feedback, then returns session stats (total questions, accuracy,
missed terms)."

**AI Response:** The first draft called `input()` and `print()` directly
inside `QuizEngine.run()`. It worked when run manually, but it meant the
only way to unit-test the full session loop (required by
`test_full_session` in the spec) would be monkeypatching built-in `input`
and capturing stdout with `capsys` — fragile and indirect for something as
important as the scoring logic.

**Changes Made:** Refactored `run()` to accept two injected callables,
`ask_answer(card) -> Optional[str]` and `report_feedback(card, correct) ->
None`, instead of calling `input`/`print` itself. Moved the real
`input()`/colored-`print()` implementations into `ui.py`, wired together
only in `main.py`.

**Reasoning:** Separation of concerns — `QuizEngine` should own scoring
logic, not terminal I/O. This also makes `test_integration.py::test_full_session`
a plain function test (pass in a list of canned answers via an iterator,
assert on the returned `SessionStats`) rather than a slower, less direct
subprocess or monkeypatch-heavy test.

**Outcome:** `test_full_session`, `test_session_stops_early_when_user_exits`,
and the adaptive-mode integration test all drive `QuizEngine.run()` directly
with fake callables — no I/O mocking required, and the same production
`ui.ask_answer`/`ui.report_feedback` pair is exercised separately and more
thoroughly in `test_ui.py`.

**Lessons Learned:** When an AI's first draft mixes business logic with I/O,
the fix is almost always dependency injection at the boundary. It's worth
asking for this explicitly up front next time ("accept the input/output
functions as parameters") rather than refactoring after the fact.

---

## 2026-09-11 — Factory registry typed too narrowly for mypy

**Context:** Running `mypy .` as part of the "Definition of Done" quality
gate, after implementing `QuizModeFactory`.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "Run mypy and flake8 across the project and fix any
errors."

**AI Response:** `mypy` failed with `Too many arguments for "QuizMode"` on
the line that calls `mode_class(cards)` inside `QuizModeFactory.create`.
The registry had been typed as `Dict[str, Type[QuizMode]]`, so mypy checked
every call against the abstract base class's (implicit, no-arg)
constructor, not the concrete subclasses' actual `__init__(self, cards)`
signatures.

**Changes Made:** Retyped the registry as
`Dict[str, Callable[[List[Flashcard]], QuizMode]]`, which correctly
describes "a callable that takes a list of flashcards and returns some
`QuizMode`" and matches every concrete class's constructor signature
(`RandomMode`'s optional `rng` parameter has a default, so it still fits).

**Reasoning:** This is a real type-safety gap, not a mypy false positive:
`Type[QuizMode]` is technically correct only if every subclass shares the
base class's constructor signature, which none of ours do. Silencing it
with `# type: ignore` would have hidden a genuine constructor-mismatch bug
if a future mode's `__init__` took incompatible arguments.

**Outcome:** `mypy .` passes with zero errors project-wide (`Success: no
issues found in 12 source files`), without any `# type: ignore` suppressions.

**Lessons Learned:** A factory/registry pattern mapping names to classes
should almost always be typed by the constructor's `Callable` signature,
not by `Type[Base]`, unless every subclass is guaranteed to share the base
constructor.

---

## 2026-09-11 — Scoring semantics for Adaptive mode were ambiguous

**Context:** Deciding what "Total Questions" and "Accuracy %" should mean
for `AdaptiveMode`, where the same card can be presented more than once in
one session.

**AI Tool Used:** Claude Code (Sonnet 5)

**Prompt/Request:** "If a card is answered wrong and then requeued and
later answered correctly in Adaptive mode, should the session stats count
it as one question or two, and should it count as correct or incorrect?"

**AI Response:** Claude proposed two options: (a) count every presentation
as a separate question (so a retried card can contribute both a wrong and a
later right answer to the tally), or (b) count each unique card once, scored
by its first attempt, with later presentations only affecting whether the
card keeps reappearing.

**Changes Made:** Accepted option (b): `QuizEngine` tracks a `_seen` set of
card fronts and only updates `total_questions`/`correct`/`missed_terms` the
first time a given card is presented; subsequent re-presentations (from
Adaptive mode's requeueing) still run through `record_result` but no longer
touch the stats.

**Reasoning:** Option (a) would let Adaptive mode inflate a user's own
accuracy by re-asking a card until it's answered right and counting that as
a fresh correct answer, which misrepresents how well the user actually knew
the deck on first exposure — and would make Adaptive-mode accuracy
non-comparable to Sequential/Random-mode accuracy for the same deck.

**Outcome:** Documented in `QuizEngine.run()`'s docstring and directly
asserted in
`test_full_session_with_adaptive_mode_scores_first_attempt_only`, which
answers a card wrong then right and checks it lands in `missed_terms` with
`correct == 1`, not `2`.

**Lessons Learned:** Ambiguous scoring rules are exactly the kind of design
decision that should be resolved with the AI (or in this case, worked
through explicitly) *before* writing tests around it, since either answer
is "correct code" but only one matches the intended product behavior.

---

## 2026-09-12 — Rubric audit caught an unsound type assumption in the tests

**Context:** Before submitting, I re-checked the finished project line by
line against the assignment rubric rather than assuming the earlier "all
tools pass" result meant everything was covered.

**AI Tool Used:** Claude Code (Opus 5)

**Prompt/Request:** "Check the output against the rubric in
`final-final-project.txt` — verify each requirement against the actual
files rather than from memory."

**AI Response:** The audit was run as scripted checks over the AST rather
than by eyeballing, which found four things a read-through had missed:
16 methods in `quiz_engine.py` with no docstrings (the rubric requires
docstrings on functions); 45 test functions with no type hints (the spec
says *all* functions need hints); two tests whose names didn't exactly
match the spec-mandated `test_quiz_mode_factory` and
`test_adaptive_mode_behavior`; and no coverage report committed to the
repo, since `htmlcov/` had been gitignored as a build artifact even though
the submission checklist lists it as a deliverable.

**Changes Made:** Added the missing docstrings; annotated every test
function and re-enabled `disallow_untyped_defs` for `tests/` so mypy runs
strict project-wide; added a `test_quiz_mode_factory` test asserting the
factory returns the right class for all three names, and renamed the
adaptive test to the spec's exact name; committed the coverage report and
documented it in `docs/coverage_report.md`.

**Reasoning:** Turning strict typing on for the tests wasn't just
box-ticking — it immediately failed with 11 errors showing the tests were
passing `Optional[Flashcard]` straight from `get_next_card()` into methods
that require a non-optional `Flashcard`. The tests only passed because the
decks happened never to be empty at those points. I added a typed
`next_card()` helper that asserts non-None, so the assumption is now
checked rather than merely true by luck.

**Outcome:** 42 tests passing, 98% coverage, and `black`/`flake8`/`mypy`
all clean with mypy now strict across tests as well as source.

**Lessons Learned:** "The tools all pass" is only as strong as the config
they run under — relaxing a rule for a directory (here, typing in `tests/`)
quietly moves that code outside the quality gate. It's worth periodically
re-running the gate at full strictness to see what the exemption was
hiding, and auditing against the spec mechanically rather than by memory.

---

## Summary Statistics

- **Total AI interactions logged in detail:** 6 (plus the ongoing
  decompose → generate → review → refine cycle described in `prompts.md`)
- **Lines of AI-generated code used:** 654 (345 application + 309 test
  lines, excluding blanks and comments). Every line in this project was
  AI-generated; none was hand-written from scratch, per the brief's
  instruction to rewrite the prompt rather than the Python.
- **Lines of AI-generated code modified:** 159 changed during the documented
  review passes (105 insertions, 54 deletions in the audit commit alone),
  plus the in-session corrections before the first commit: the
  `FlashcardLoadError` consolidation, the `AdaptiveMode` retry bound, the
  `QuizEngine.run()` signature change from direct I/O to injected
  callables, and the factory's `Callable` retyping. Roughly a quarter of
  the code was revised after review rather than accepted as first drafted.
- **Most helpful AI interaction:** The QuizEngine/UI decoupling — it made
  the hardest-to-test part of the app (a session loop that asks for input)
  trivially testable.
- **Most challenging AI interaction:** Deciding Adaptive mode's scoring
  semantics — the code was easy to write either way, but only one behavior
  was actually correct for the product.
- **Biggest lesson learned:** An AI agent will faithfully implement exactly
  what you asked for, including the edge cases you forgot to rule out (an
  unbounded retry loop, a `KeyError` you didn't name, a `Type[Base]`
  annotation that doesn't fit mismatched constructors). Review has to check
  what *wasn't* specified, not just whether the code satisfies what was.
