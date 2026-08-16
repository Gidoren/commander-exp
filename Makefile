ANSWERS ?= $(HOME)/.local/share/deckcheck-answers
MODEL   ?= local/qwen3.6-27b
AGENT   := pi -p --no-session --model $(MODEL) {task}
EVAL    := python scripts/run_eval.py tasks/tasks.json --tests-dir $(ANSWERS)/tests
TIMEOUT ?= 3600

.PHONY: data test smoke probe baseline summary clean

data:
	python -c "from deckcheck.scryfall import fetch; print(fetch())"

test:
	pytest -q tests/

# ONLY=t01_nonland,t02_avg_mv -> restrict to those tasks
smoke:
	$(EVAL) --config null   $(if $(ONLY),--only $(ONLY),) --cmd 'true'
	$(EVAL) --config oracle $(if $(ONLY),--only $(ONLY),) \
	  --cmd 'cp $(ANSWERS)/deckcheck/*.py deckcheck/'

probe:
	$(EVAL) --config probe --only t01_nonland --timeout $(TIMEOUT) --cmd '$(AGENT)'

# ONLY=t01_nonland,t02_avg_mv -> restrict to those tasks
# CONFIG=decomp-split-1     -> label this run in results.jsonl (default baseline-1)
CONFIG ?= baseline-1
baseline:
	$(EVAL) --config $(CONFIG) $(if $(ONLY),--only $(ONLY),) --timeout $(TIMEOUT) --cmd '$(AGENT)'

summary:
	python scripts/aggregate.py

clean:
	git worktree prune && rm -rf ../.eval-*
