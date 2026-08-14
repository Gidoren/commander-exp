ANSWERS ?= $(realpath $(CURDIR)/../commander-exp-answers)
EVAL    := python scripts/run_eval.py tasks/tasks.json --tests-dir $(ANSWERS)/tests

.PHONY: data test smoke baseline clean

data:
	python -c "from deckcheck.scryfall import fetch; print(fetch())"

test:
	pytest -q tests/

# ONLY=t01_nonland,t02_avg_mv  ->  restrict to those tasks
smoke:
	$(EVAL) --config null   $(if $(ONLY),--only $(ONLY),) --cmd 'true'
	$(EVAL) --config oracle $(if $(ONLY),--only $(ONLY),) \
	  --cmd 'cp $(ANSWERS)/deckcheck/*.py deckcheck/'

baseline:
	for i in 1 2 3; do \
	  $(EVAL) --config baseline-$$i --cmd 'pi --yolo "{task}"'; \
	done
	python scripts/aggregate.py > results/summary.md

clean:
	git worktree prune && rm -rf ../.eval-*
