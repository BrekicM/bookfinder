# Book Finder

## Preferences

### Always use TDD for implementation work

Invoke the `test-driven-development` skill before writing any implementation code. Applies to
all implementation work (features, bug fixes, behavior changes, refactoring). Does not apply to
config, docs, dependency bumps, formatting, or exploratory spikes — defer to the skill's own
"When TDD is the wrong tool" section for edge cases.

Do not report implementation work as done without showing real test output. If a step went in
without a test, say so explicitly.

### Gate work with /no-mistakes before it ships

Use the `no-mistakes` skill before pushing: `/no-mistakes <task>` to build and gate in one go,
or bare `/no-mistakes` to gate already-committed work. Apply safe fixes automatically; stop and
ask on ambiguous findings. A task is done once it passes the gate, not once the code changed.

### Delegate gated tasks to a subagent

Spawn one subagent per task: implement (TDD), commit on a feature branch, then drive the
no-mistakes pipeline (`axi run --intent`) to completion. The subagent handles `auto-fix` and
`no-op` findings on its own judgment. On `ask-user` findings, it stops and reports verbatim to
the parent session — it must not guess or self-approve. No concurrent gate-drivers unless asked.

## Context re-entry

Write every response for cold re-entry — assume I remember nothing from the scrollback:

- **Recap first.** Open with 2–3 sentences on what we were working on, why, and where it stands.
- **One question at a time.** If multiple decisions are pending, say how many and present only the first.
- **Self-contained.** Every question must carry background, options, tradeoffs, and your recommendation inline — no scrolling back required.
- **Anchor the work.** Name the project, branch, and PR when reporting status. Close with the single next action waiting on me, or say nothing is.
