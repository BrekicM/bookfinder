# Book Finder

## Preferences

### Always use TDD for implementation work

Invoke the `test-driven-development` skill before writing any implementation code. Applies to
all implementation work (features, bug fixes, behavior changes, refactoring). Does not apply to
config, docs, dependency bumps, formatting, or exploratory spikes — defer to the skill's own
"When TDD is the wrong tool" section for edge cases.

Do not report implementation work as done without showing real test output. If a step went in
without a test, say so explicitly.

## Orchestrating the gate (builder/driver split)

- **Builders never drive the gate.** A builder agent builds, commits on its branch, and ends its
  task with a `HANDOFF: INTENT` paragraph — a thorough statement of what changed and why, for
  the reviewer. Its large transcript is read once and never resumed for gate-driving.
- **A fresh driver agent per worktree** (Sonnet model) runs the gate:
  it starts the review with the handed-off intent, monitors progress, and answers the gate's
  questions.
- **Gate rules for the driver:** apply auto-fixable findings; approve info-only findings; for
  anything that needs a human decision, PARK — quote the finding verbatim and end the task so
  the orchestrator can relay it to me, then resume the driver with my decision. Resume a
  builder only when a finding needs real code fixes.
- Never end a subagent's turn while a gate run is active — its background processes are
  orphaned the moment the turn ends.

## Context re-entry

Write every response for cold re-entry — assume I remember nothing from the scrollback:

- **Recap first.** Open with 2–3 sentences on what we were working on, why, and where it stands.
- **One question at a time.** If multiple decisions are pending, say how many and present only the first.
- **Self-contained.** Every question must carry background, options, tradeoffs, and your recommendation inline — no scrolling back required.
- **Anchor the work.** Name the project, branch, and PR when reporting status. Close with the single next action waiting on me, or say nothing is.
