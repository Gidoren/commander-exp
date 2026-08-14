# deckcheck

Commander deck validator. Also the substrate for an agent evaluation harness.

## Two audiences

Read as a project: a library that parses a decklist and validates it against
Commander rules using cached Scryfall data. Offline and deterministic after one
data fetch.

Read as an eval: `deckcheck/` ships with three modules complete and five as
signature-pinned stubs. Each stub is a task. Hidden tests live on the
`eval/tests` branch and are copied in only at grading time.

## Layout

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
| `tests/` | visible; house style for the agent to imitate |
| `eval-tests/` | **move to branch `eval/tests` before running** |

## Setup

```bash
make data        # one-time Scryfall fetch, ~500MB
make test        # foundation tests should pass on a clean checkout
```

Then move the hidden tests off `main`:

```bash
git checkout -b eval/tests
git mv eval-tests/* tests/ && git commit -m "hidden tests"
git checkout main && git rm -r --cached eval-tests
```

## Before measuring anything

1. Write the reference implementation on branch `reference`. It is the answer
   key for the `oracle` run and for reading failures by hand later.
2. `make smoke` — `null` must score 0/13 and `oracle` 13/13. If oracle is not
   perfect, the harness is broken, not the model.
3. Only then `make baseline`.

## Reproducibility

Record here before the first baseline run: model, quant, context length,
sampling params, Pi version, Scryfall snapshot date.
