# TODO

## Before any real measurement
- [ ] `make data` — one-time Scryfall bulk fetch (~500MB) into `data/scryfall.json`.
      Not run yet (real network fetch, wanted explicit go-ahead).
- [ ] Write the reference implementation (`curve.py`, `identity.py`,
      `legality.py`, `companions.py`, `brackets.py`) on a `reference` branch.
      Answer key for the `oracle` run in `make smoke` and for reading
      baseline failures by hand.
- [ ] `make smoke` must show `null` at 0/13 and `oracle` at 13/13 before any
      baseline run — if oracle isn't perfect, the harness is broken, not the
      model.

## Harness gap
- [ ] `tasks/tasks.json` (id/tier/module/start_ref/test_ref/task per entry)
      does not match the manifest shape `scripts/run_eval.py` expects
      (`{"repo": ..., "candidates": [{"sha", "parent", "kind", "task",
      "test_files"}, ...]}`). Need something that derives `sha`/`parent` per
      task from commits (presumably once `reference` exists) and emits the
      manifest `run_eval.py` reads.

## Housekeeping
- [ ] `deckcheck-scaffold.tar.gz` is now fully extracted and redundant —
      decide whether to delete it or keep as the original download.
- [ ] `eval/tests` branch was cut before the `pytest.ini` / `.gitignore`
      fixes landed on `main` — merge/rebase if that branch needs to run
      `make test` standalone.

## Reproducibility (per README)
- [ ] Record before the first baseline run: model, quant, context length,
      sampling params, Pi version, Scryfall snapshot date.
      Toolchain on this machine: `aider` and `pi` on PATH; no `qwen` binary
      on PATH (served some other way, driven through aider/pi).
