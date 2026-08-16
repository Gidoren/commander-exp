# Decomposition experiment: t11_companions (whole) vs t11a/b/c (split)

## Hypothesis under test

`t11_companions` bundles nine structurally distinct companion rules into one
task and is the slowest, least reliable task in the set (3025s in the
baseline run that passed; historically anywhere from 231s to a full 3600s
timeout). The hypothesis: splitting it into `t11a_companions_mv` (Lurrus,
Obosh, Gyruda, Keruga), `t11b_companions_cost` (Jegantha, Kaheera), and
`t11c_companions_struct` (Umori, Zirda, Yorion) improves wall clock and pass
rate, with no orchestration and no shared state between subtasks — each runs
independently against `start_ref: main`, exactly like any other task.

Three runs of each configuration, per the brief:

```
make baseline ONLY=t11_companions CONFIG=decomp-whole-$i
make baseline ONLY=t11a_companions_mv,t11b_companions_cost,t11c_companions_struct \
  CONFIG=decomp-split-$i
```

## Results

| Config | Task | Passed | Seconds |
|---|---|---|---|
| decomp-whole-1 | t11_companions | **FAIL** (context overflow — see below) | 20.4 |
| decomp-whole-2 | t11_companions | PASS | 891.1 |
| decomp-whole-3 | t11_companions | PASS | 693.8 |
| decomp-split-1 | t11a_companions_mv | PASS | 248.0 |
| decomp-split-1 | t11b_companions_cost | PASS | 441.8 |
| decomp-split-1 | t11c_companions_struct | PASS | 492.9 |
| decomp-split-2 | t11a_companions_mv | PASS | 240.6 |
| decomp-split-2 | t11b_companions_cost | PASS | 734.2 |
| decomp-split-2 | t11c_companions_struct | **FAIL** (silent no-op — see below) | 529.1 |
| decomp-split-3 | t11a_companions_mv | PASS | 234.7 |
| decomp-split-3 | t11b_companions_cost | PASS | 511.1 |
| decomp-split-3 | t11c_companions_struct | PASS | 1690.9 |

### Wall clock, per run (whole = 1 task, split = 3 tasks summed)

| Run | Whole (s) | Split (s) |
|---|---|---|
| 1 | 20.4 | 1182.7 |
| 2 | 891.1 | 1503.9 |
| 3 | 693.8 | 2436.7 |
| **Total** | **1605.3** | **5123.3** |
| **Median** | 693.8 | 1503.9 |

### Pass rate

| Config | Passed / total |
|---|---|
| Whole (task-level, 3 attempts) | 2/3 (67%) |
| Split (subtask-level, 9 attempts) | 8/9 (89%) |

## What the two failures actually were

**decomp-whole-1** failed in 20.4s with `agent_exit=1` and `agent_tail`:
`"Context size has been exceeded."` This is an environment ceiling, not a
model reasoning failure: `llama-server` is running with `-c 61184` (~61K
total context), while `pi`'s model registry
(`~/.pi/agent/models.json`) advertises this model at `contextWindow: 131072`
/ `maxTokens: 32768`. The full `t11_companions` task text plus the full
nine-companion stub docstring plus normal tool-call overhead is apparently
enough to blow that budget almost immediately. This was not fixed as part of
this experiment (fixing it means restarting the model server with a larger
`-c`, which would break comparability with every existing baseline number in
`results.jsonl`) — it's flagged here as a real, separate finding.

**decomp-split-2**'s `t11c_companions_struct` failed with `agent_exit=0`, an
empty `diff_stat` (no files touched), and an empty `agent_tail`, despite
running for a real 529.1s. This is the identical signature documented in
`results/t07-regression.md` for the t07 regression's one clean-run
failure — the agent apparently did nothing observable and exited cleanly.
It is not a decomposition-specific failure; it looks like the same
occasional agent-tooling flake seen elsewhere in this harness, independent
of task size.

## Verdict

**Wall clock: splitting is slower, not faster — by roughly 2-3x.** Every
split run's summed wall clock (1182.7s–2436.7s) exceeds every successful
whole run's wall clock (693.8s, 891.1s). This is expected, not surprising:
each subtask is a fresh `--no-session` process against a fresh worktree, so
splitting pays three separate agent-startup and context-loading costs
(reading the same stub file, the same imports, the same fixtures) instead of
one. Nothing about the harness shares context between subtasks — nor was it
supposed to, per this step's non-goals — so this overhead is inherent to the
approach, not an implementation gap.

**Pass rate: split's 89% vs whole's 67% is not clean evidence for the
original coherence hypothesis.** The one whole-task failure was a context-
window overflow, not the model losing track of nine bundled rules through
reasoning drift — the run never got far enough to demonstrate coherence loss
one way or the other. Smaller task+docstring text does mean splitting is
less likely to hit that particular ceiling, which is a genuine practical
benefit, but it's a different mechanism than "the model loses coherence
across structurally distinct rules." And the one split-side failure was an
unrelated no-op flake, not a reasoning failure either — so of the three
recorded failures across both conditions, none is actually evidence of a
model coherence problem in the whole-task condition.

**Bottom line:** with n=3 per configuration, one confounded failure on each
side, this data does not support the hypothesis as stated. Splitting
`t11_companions` clearly costs wall clock rather than saving it. It may
reduce exposure to the context-window ceiling for large bundled tasks — a
real and separate benefit worth knowing about — but that is an artifact of
prompt/context size, not evidence that the model was losing coherence across
the nine companion rules. `t11_companions` stays intact; nothing here
justifies replacing it with the split tasks in the default task set.
