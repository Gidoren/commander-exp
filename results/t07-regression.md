# t07_identity regression — diagnosis

## What ran, in order

| # | Config (results.jsonl) | Prompt | Agent invocation | Result | Seconds |
|---|---|---|---|---|---|
| 1 | baseline-1 | truncated (quoting bug) | old `pi --yolo "{task}"` | PASS | 1074.9 |
| 2 | baseline-2 | truncated (quoting bug) | old `pi --yolo "{task}"` | PASS | 1058.5 |
| 3 | baseline-3 | truncated (quoting bug) | old `pi --yolo "{task}"` | PASS | 3409.0 |
| 4 | baseline-1 (2nd batch) | full | new `pi -p --no-session --model … {task}` | PASS | 1131.2 |
| 5 | baseline-1 (3rd batch, the one referenced as "the clean run") | full | new `pi -p --no-session --model … {task}` | **FAIL** | 100.6 |

Run 5 is the most recent `baseline-1` and the only number this step's brief
treats as valid; runs 1–4 are shown for context only.

## What differs

Runs 1–3 received a **truncated** task string: the old command template
`pi --yolo "{task}"` interpolated the raw task text into a `shell=True`
command, and the shell split at the first `->` in
`color_identity(card: Card) -> frozenset[str]`. The model actually received
something like:

> Implement deckcheck/identity.py::color_identity(card: Card)

with everything after — the return type, `identity_string`, and critically
the "do NOT read card.color_identity" instruction — cut off. Despite that,
all three passed, because the same instructions are restated in full in the
`deckcheck/identity.py` stub docstring, which the model reads directly from
the checked-out file regardless of what the task string says. Each of these
three runs wrote a substantial (1000–3400s) implementation with its own
Scryfall-derived validation pass, cross-checked against the full card
database, before landing on a correct `color_identity`/`identity_string`.

Run 4, the first run after the quoting fix, received the full prompt and
also passed — again with a detailed implementation and validation report
(~1130s), structurally identical in approach to runs 1–3.

Run 5 — same fixed harness, same full prompt, same model, run immediately
after run 4 — is the outlier:

- `agent_exit`: `0` (the agent process exited cleanly, no crash, no non-zero
  status)
- `diff_stat`: `""` (no files were touched in the worktree at all)
- `agent_tail`: `""` (no stdout/stderr captured)
- `seconds`: `100.6` (well under the timeout)
- `check_tail`: all 15 tests fail with `NotImplementedError` — `identity.py`
  is untouched, still the raw stub (confirmed: `deckcheck/identity.py` on
  `main` still raises `NotImplementedError` in both `color_identity` and
  `identity_string` — eval runs only ever touch the file inside a disposable
  worktree, so the stub on `main` was never at risk of drifting from this)

In other words: the agent ran for ~100 seconds, made zero changes to the
repository, and exited successfully having produced no observable output.
That is not "misread the spec" (there's no partial/wrong implementation to
misread from) and it is not a harness timeout (exit 0, well under the time
budget, no `TimeoutExpired`). It looks like the agent invocation itself
produced a degenerate or empty response for this one task and then quit —
an isolated no-op, not a reasoned attempt that failed.

## Verdict

This reads as **run-to-run variance**, not a genuine capability regression.
The model has solved this exact task correctly, with real implementation
depth, in 4 of 5 total attempts — including the attempt immediately
preceding this one, under the identical (fixed) harness and prompt. The one
failure has none of the signatures of the model struggling with the spec
(no partial code, no reasoning trail, no test near-misses); it has the
signature of the agent tooling silently doing nothing for this single task
before returning success. Nothing here points to a change in how the model
handles the t07 spec.

No fix applied — this file is diagnosis only, per the brief.
