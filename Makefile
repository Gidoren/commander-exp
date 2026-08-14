.PHONY: data test smoke baseline clean

data:
	python -c "from deckcheck.scryfall import fetch; print(fetch())"

test:
	pytest -q tests/

smoke:
	python scripts/run_eval.py tasks/tasks.json --config null --cmd 'true'
	python scripts/run_eval.py tasks/tasks.json --config oracle --cmd 'git merge --no-edit reference'

baseline:
	for i in 1 2 3; do \
	  python scripts/run_eval.py tasks/tasks.json --config baseline-$$i \
	    --cmd 'pi --yolo "{task}"'; \
	done
	python scripts/aggregate.py > results/summary.md

clean:
	git worktree prune
	rm -rf .eval-*
