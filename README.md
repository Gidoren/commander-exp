# deckcheck

Commander deck validator. Also the substrate for an agent evaluation harness.

## Two audiences

Read as a project: a library that parses a decklist and validates it against
Commander rules using cached Scryfall data. Offline and deterministic after one
data fetch.

Read as an eval: `deckcheck` ships with three modules complete and five as
signature-pinned stubs. Each stub is a task, graded against hidden tests.

Neither the library nor the tests live in this repo. This repo (`main`) is
the harness only — runner, task manifest, fixtures. `deckcheck/` (stub and
reference versions) and all tests live in a plain, non-git directory outside
the repo, by default `../commander-exp-answers` (override with `ANSWERS=`).
They're never committed to any branch: `git worktree add` shares the object
store and refs with this repo, so anything committed here — even on another
branch — is reachable from an agent's worktree via `git show`. Keeping them
out of git entirely is the only airtight version. See the docstring in
`scripts/run_eval.py` for the full rationale.

## Layout

Tracked in this repo:

| Path | Purpose |
|---|---|
| `scripts/run_eval.py` | grading harness: worktree per task, runs the agent, copies in tests only after, checks |
| `tasks/tasks.json` | task manifest (id, tier, start_ref, test_files, check, task prompt) |
| `fixtures/minimal.txt` | sample decklist |
| `Makefile` | `data` / `test` / `smoke` / `probe` / `baseline` / `clean` |
| `TODO.md` | outstanding harness gaps |

Outside this repo, in `$(ANSWERS)` (default `../commander-exp-answers`):

| Path | State |
|---|---|
| `deckcheck/models.py` | complete |
| `deckcheck/scryfall.py` | complete |
| `deckcheck/parse.py` | complete (t04 extends it) |
| `deckcheck/curve.py` | stub — t01, t02, t03 |
| `deckcheck/identity.py` | stub — t07 |
| `deckcheck/legality.py` | stub — t05, t06, t08, t09, t10 |
| `deckcheck/companions.py` | stub — t11 |
| `deckcheck/brackets.py` | stub — t12, t13 |
| `tests/` | visible + hidden tests together, plus the complete reference `deckcheck/` used for the `oracle` smoke run |

## Setup

`make data` and `make test` need a real `deckcheck/` package and `tests/`
directory present locally — they're not tracked here, so a bare checkout of
`main` can't run either target on its own. Populate them from `$(ANSWERS)`
first, e.g.:

```bash
mkdir -p deckcheck tests
cp $(realpath ../commander-exp-answers)/deckcheck/*.py deckcheck/
cp $(realpath ../commander-exp-answers)/tests/*.py tests/

make data        # one-time Scryfall fetch, ~500MB
make test        # foundation tests should pass on a clean checkout
```

Known gap: the `smoke` target's `oracle` leg (`cp $(ANSWERS)/deckcheck/*.py
deckcheck/`) assumes a `deckcheck/` directory already exists in the eval
worktree to copy into. Since `main` no longer carries any `deckcheck/`
files, that worktree starts empty and the `cp` has nowhere to land — see
`TODO.md`.

## Before measuring anything

1. The reference implementation lives at `$(ANSWERS)/deckcheck` (no longer a
   `reference` git branch). It's the answer key for the `oracle` run and for
   reading failures by hand later.
2. `make smoke` — `null` must score 0/13 and `oracle` 13/13. If oracle is not
   perfect, the harness is broken, not the model.
3. Only then `make baseline` (or `make probe` for a single-task dry run).

## Reproducibility

Record here before the first baseline run: model, quant, context length,
sampling params, Pi version, Scryfall snapshot date.

- **Model**: `unsloth/Qwen3.8-27B-GGUF`, quant `Q4_K_M` — not "Qwen3.6-27B" as
  earlier `results.jsonl` configs and this doc assumed; that was a stale
  alias in `~/.pi/agent/models.json` (`id: "qwen3.6-27b"`) that never matched
  what the server actually had loaded. Any comparison across configs should
  treat pre-2026-08-16 runs as a different (and not fully known) model/quant.
- **Serving**: `llama-server` (part of Unsloth Studio, which does run
  llama.cpp under the hood) with `--parallel 1` — a single client, single
  decode slot, so `-c` isn't split across slots. `-c 143616`; Pi's
  `contextWindow` is set to `131072` (headroom below the real ceiling, since
  Pi's own token accounting doesn't include chat-template overhead, tool
  schemas, or BOS tokens).
- **Speculative decoding is on** (`--spec-type ngram-mod`). This can make
  output vary run-to-run in ways unrelated to prompt or code changes -
  keep that in mind before attributing a behavior difference to anything
  else.
- **Reasoning effort is `medium`, set server-side** via
  `--chat-template-kwargs '{"enable_thinking": true, "preserve_thinking":
  false, "reasoning_effort": "medium"}'`. This is not cosmetic. The chat
  template defaults `reasoning_effort` to **`xhigh`**, and nothing overrode
  it: Pi declares `"supportsReasoningEffort": false` in
  `~/.pi/agent/models.json`, so it never sends the field regardless of its
  own `--thinking` level. At `xhigh` the model would spend all 32768 tokens
  inside an unterminated `<think>` block, return `finish_reason: length`
  with **empty** `content`, and Pi would exit 0 having written nothing — the
  t10/t12 "silent no-op". It also depressed quality broadly: t04, t08 and
  t11 all began passing once effort dropped to `medium`. Treat any run
  before 2026-08-16 as an `xhigh` run.
- **DRY sampler on** (`--dry-multiplier 0.8`). `repeat_penalty` is 1.0 and
  DRY defaulted to 0.0, so nothing could break a repetition loop once
  entered. Combined with ngram speculation this was visible as generation at
  356-719 tok/s (vs ~70 baseline) while burning the whole token budget.
- **Reloading the model rewrites these flags.** Unsloth Studio spawns
  `llama-server` itself and assigns a new random port each time; its
  `speculative_type: "auto"` resolved to `draft-mtp` on one reload and
  `ngram-mod` on another. Pin `speculative_type` explicitly and diff
  `/proc/<pid>/cmdline` before and after any reload rather than trusting
  the settings you passed.
- **Pi**: 0.84.2.
- **Scryfall snapshot**: `data/scryfall.json`, fetched 2026-08-14.
