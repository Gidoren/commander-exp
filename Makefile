.PHONY: data test smoke baseline clean\
ANSWERS ?= $(HOME)/commander-experiments/src/commander-exp-answers

data:
	python -c "from deckcheck.scryfall import fetch; print(fetch())"

test:
	pytest -q tests/

smoke:
	python scripts/run_eval.py tasks/tasks.json --config null \
	  --tests-dir $(ANSWERS)/tests --cmd 'true'
	python scripts/run_eval.py tasks/tasks.json --config oracle \
	  --tests-dir $(ANSWERS)/tests --cmd 'cp $(ANSWERS)/deckcheck/*.py deckcheck/'

baseline:
	for i in 1 2 3; do \
	  python scripts/run_eval.py tasks/tasks.json --config baseline-$$i \
	    --cmd 'pi --yolo "{task}"'; \
	done
	python scripts/aggregate.py > results/summary.md

clean:
	git worktree prune
	rm -rf .eval-*
