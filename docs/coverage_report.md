# Test Coverage Report

Target: **>80%**. Actual: **98%** overall / **95%** on application modules.

Generated with the command given in the project brief:

```bash
python -m pytest --cov=. --cov-report=html
```

The browsable HTML report produced by that command is committed at
[`htmlcov/index.html`](../htmlcov/index.html). The terminal output is
reproduced below for convenience.

## Full project (`--cov=.`, as specified in the brief)

```
Name                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------
main.py                             38      4    89%   69-71, 94
models.py                            5      0   100%
quiz_engine.py                      95      4    96%   76, 148, 168, 184
tests/__init__.py                    0      0   100%
tests/test_flashcard_loader.py      69      0   100%
tests/test_integration.py           38      0   100%
tests/test_main.py                  37      0   100%
tests/test_quiz_modes.py            86      0   100%
tests/test_ui.py                    42      0   100%
ui.py                               33      0   100%
utils/__init__.py                    0      0   100%
utils/file_handler.py               37      2    95%
--------------------------------------------------------------
TOTAL                              480     10    98%

42 passed
```

## Application modules only

Because `--cov=.` includes the test files themselves (which are trivially
100% covered by definition), here is the stricter figure covering only the
five application modules:

```bash
python -m pytest --cov=main --cov=models --cov=quiz_engine --cov=ui --cov=utils --cov-report=term-missing
```

```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
main.py                    38      4    89%   69-71, 94
models.py                   5      0   100%
quiz_engine.py             95      4    96%   76, 148, 168, 184
ui.py                      33      0   100%
utils/__init__.py           0      0   100%
utils/file_handler.py      37      2    95%   69-70
-----------------------------------------------------
TOTAL                     208     10    95%
```

## What the 10 uncovered lines are

These were reviewed individually rather than chased for a round number:

- `main.py:69-71` — the `except KeyboardInterrupt` fallback around
  `engine.run()`. In practice `ui.ask_answer()` catches Ctrl+C at the prompt
  itself (which *is* tested, in `test_ask_answer_returns_none_on_keyboard_interrupt`);
  this outer block only fires if the interrupt lands between prompts, which
  can't be triggered deterministically from a test.
- `main.py:94` — the `if __name__ == "__main__":` dispatch line.
- `quiz_engine.py:76, 148, 168, 184` — the four `@abstractmethod` bodies on
  the `QuizMode` ABC, which are never executed because every concrete
  subclass overrides them.
- `utils/file_handler.py:69-70` — the `except OSError` branch for a file
  that exists but can't be read (e.g. a permissions error). Triggering this
  reliably would require filesystem mocking that tests the mock more than
  the code.

## Test suite composition

42 tests across five files:

| File | Tests | Covers |
|---|---|---|
| `test_flashcard_loader.py` | 13 | Both JSON shapes, invalid JSON, missing/blank fields, missing file, empty deck |
| `test_quiz_modes.py` | 13 | Factory resolution + rejection, all three mode orderings, adaptive requeue/retry-limit |
| `test_integration.py` | 3 | Full simulated session, early exit, adaptive first-attempt scoring |
| `test_ui.py` | 8 | Input handling (`exit`, Ctrl+C, Ctrl+D), colored feedback, summary rendering |
| `test_main.py` | 5 | CLI parsing, `--help`, invalid mode, missing-file error path, `--stats` output |
