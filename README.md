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
