# Local coding agent evaluation — retrospective

**2026-08-14 → 2026-08-17. Four days.**

Companion to `EVAL-FINDINGS.md`, which holds the technical record. This document
covers what transfers.

---

## What this was

The question: can a large model orchestrating a smaller local one do useful
software work, and what architecture makes that work?

The approach: build an evaluation harness first, measure a baseline, then test
orchestration interventions against it. A Magic: The Gathering Commander deck
validator was chosen as substrate — pure functions over a cached offline
dataset, deterministic tests, a genuine difficulty gradient, and a domain where
a wrong answer is recognisable at a glance.

## What actually happened

The harness was wrong in seven independent ways, and finding them consumed the
project.

| # | Defect | Symptom | Days corrupted |
|---|---|---|---|
| 1 | Missing scaffold | `deckcheck/` moved rather than copied; agents rebuilt it from git history before starting | all early runs |
| 2 | Shell quoting | task text truncated at the first `->`; models received partial function signatures | all early runs |
| 3 | stdin inheritance | clean exit, zero output, no error anywhere | ~5% of runs |
| 4 | Legacy quant | Q4_1 ran the engine at 11.5 tok/s decode vs 67.4 on Q4_K_M | 1 full baseline |
| 5 | Context overshoot | client declared the server's exact limit; requests landed 30–60 tokens over | 17 requests |
| 6 | `reasoning_effort: xhigh` | model burned the entire token budget inside an unclosed reasoning block | ~7% of runs |
| 7 | Path-guessing loop | agent invented an absolute main-repo path while cwd was the worktree, then cycled on `ENOENT` forever | ~7% of runs |

Plus three contamination defects: hidden tests readable via `git show` from any
worktree; a tracked brief that named task answers, caught by a wire trace of the
agent's own `ls`; and two tasks that were only passable if the agent
volunteered work belonging to a *different* task.

Plus six specification defects — casing conventions, ordering conventions, and
one hidden test asserting a requirement the task string never stated.

**Real model capability gaps found: two, arguably one.**

## The finding

> Most of what looked like capability failure was harness failure, and it
> evaporated as the harness was repaired.

Every apparent weakness that could be fixed by fixing the measurement, was. The
final frozen baseline: **10 / 11 / 10 of 13, spread 1, zero timeouts**, on a
27B model quantized to 4 bits running on a single consumer GPU.

## The architecture answer

The project set out to build a multi-tier orchestrator: a frontier model
planning, a mid-size local model executing, a small model on mechanical steps,
with a deterministic state machine between them.

None of it was built, and the evidence says none of it was needed.

- **Decomposition was tested and lost.** Splitting the hardest task into three
  bounded subtasks cost 2–3× wall clock with no reliability gain — each subtask
  paid a fresh startup and context-loading cost, and nothing was shared.
- **The tool layer came closest.** `pi-lens` (LSP, linters, type-checking) moved
  +1 task with a coherent mechanism: both tasks predicted to be
  language-server-visible improved, the one predicted not to didn't. Below the
  ≥2 detection floor, so inconclusive rather than negative.
- **A flat single-threaded agent loop solved 10 of 13 unaided.**

This matches the industry position that multi-agent systems work best when
writes stay single-threaded and additional agents contribute judgment rather
than actions.

**The caveat that matters:** the substrate structurally excludes the conditions
where orchestration would earn its place. Every task is single-file, clean-spec,
signature-pinned, with tests as unambiguous ground truth. That is the ideal case
for a flat loop. Orchestration pays off on long-horizon, multi-file, ambiguous
work in messy existing repos — which was never measured.

## Why the eval is finished

**10 of 13 tasks pass 3/3 regardless of intervention.** Three tasks of headroom
against a detection floor of two means any change must fix two-thirds of all
remaining failures to register at all. And one of those three is a
task-authoring defect rather than a capability gap.

More samples narrow the error bars. They do not fix saturation. The structural
answer is **harder tasks, not more runs** — and harder tasks means a real repo,
not a greenfield one.

## Methodological lessons

**Attribute before inferring.** The single worst reasoning error in the project:
*"only one 32768-token completion appears in the log, so at most one of these
three failures is the runaway."* The count was right, the inference was lazy —
nobody checked which task owned that completion. It was one of the three. The
answer was in data already on disk.

**Read the wire.** Four diagnoses were wrong — contention, proxy overhead, slot
starvation, `maxTokens`. All four came from reasoning about a gap instead of
reading what was recorded. The two that held — the runaway and the loop — both
came from wire traces. Tracing should have been step one, not step twenty.

**Verify the intervention is live.** `temperature`, `maxTokens`, and
`reasoning_effort` were all silently inert in the client config — the client
never sent them. A fix was credited to `maxTokens` that changed nothing on the
wire; four of six failures resolved simultaneously by coincidence inside a ±2
noise band. Later, `pi-lens` was verified live by watching tool count go 4 → 12
*before* interpreting its result.

**Bracket the harness from both ends.** A null run (nothing installed) must
score 0, and an oracle run (reference implementation copied in) must score 100%.
Between them they catch grading bugs that would otherwise be blamed on the
model. This was built early and caught real problems.

**Baseline before fixing.** Two tasks flipped to passing on a config change
alone. Had the specs been "fixed" first, those passes would have been credited
to the edits.

**n=1 measures nothing.** Identical configs produced 12 and 10 out of 13. Every
single-run comparison made during the project was later retracted.

**Keep the answer key outside the repository.** Not on a branch — worktrees
share the object store, so `git show` reaches any branch. Not in a gitignored
subdirectory — the agent's `bash` tool reads the filesystem. Outside the tree
entirely, and never adjacent to it.

## What would be done differently

1. **Wire tracing on day one.** It would have collapsed a three-day
   investigation into an afternoon.
2. **Oracle run before any model run.** Done, and it worked.
3. **Task strings written from the symptom side.** Several specs leaked the
   solution or under-specified conventions the hidden tests then asserted.
4. **No documentation committed to the eval repo.** A brief describing task
   answers landed in every agent worktree for two days.
5. **Fewer, harder tasks.** Thirteen easy tasks saturate. Six hard ones would
   have measured more.

## Where it stands

**Keep:** the frozen baseline as a 22-minute regression check for model or
serving-config changes. Wire tracing. The null/oracle brackets.

**Stop:** tuning against this suite. It cannot resolve what it is being asked
to test.

**Next:** use the agent on real work. The orchestration question is better
answered by noticing what needs working around three times in a week than by a
synthetic suite that structurally cannot show it.

## Config of record

Qwen3.8-27B-Q4_K_M, llama.cpp via Unsloth Studio, `--parallel 1`,
`--flash-attn on`, `--jinja`, temp 0.3, `reasoning_effort: medium`. pi 0.84.2.
~67 tok/s decode, ~345 prefill, single RTX 5090, 25.5 GB resident.

Frozen baseline: commit `313a11c`.
