# Book Finder

## Preferences

### Always use TDD for implementation work

**Invoke the `test-driven-development` skill before writing any implementation code.** Do this
at the start of the task, not after — the skill governs how the code gets written, so loading
it afterwards is too late.

This applies to:

- Adding a feature or endpoint
- Fixing a bug (reproduce with a failing test first — always)
- Changing existing behavior
- Hardening or refactoring untested code

It does not apply to config changes, documentation, dependency bumps, pure formatting, or
throwaway exploratory spikes. The skill's own "When TDD is the wrong tool" section is the
authority on the edge cases — follow it rather than deciding ad hoc.

Do not report implementation work as done without showing real test output. If a step went in
without a test, say so explicitly instead of glossing over it.

### Gate work with /no-mistakes before it ships

Use the `no-mistakes` skill to validate changes before they reach the push target: automated
code review, tests, lint, docs, push, PR, and CI.

- To have the agent do a task and validate it in one go: `/no-mistakes <task>`.
- To gate work that's already committed: bare `/no-mistakes`.

The pipeline applies safe fixes on its own and stops to ask when something needs a human call
(e.g. an ambiguous review finding, a failing check with no obvious fix). Don't treat a task as
done just because the code changed — it's done once it's passed through the gate.

## Context re-entry (multi-project juggling)

I am juggling several projects, each with several concurrent sessions, and have usually lost
the thread by the time I return to any one of them. Write every user-facing message for cold
re-entry — assume I remember nothing from the scrollback:

- **Open with a recap.** Before any summary, decision point, or question: 2–3 plain sentences on
  what we were just working on, why, and where it stands now.
- **Plain language.** No invented codenames, abbreviations, or callbacks like "the earlier fix"
  or "option B from before" — restate the thing in place, every time.
- **Self-contained questions.** When asking me to decide something, the question itself
  must carry everything needed to answer it: the background, the options, the tradeoffs, and
  your recommendation. Never require scrolling back.
- **One question at a time.** When a summary or decision point holds several open questions or
  next steps, say so up front ("three decisions are waiting; here's the first"), then present
  only the first and wait for the answer before raising the next. Never dump them all at once —
  it's too much mental load.
- **Anchor the work.** Name the project, branch, and PR when reporting status — several other
  sessions look just like this one.
- **End with the next action.** Close long updates with the single thing waiting on me,
  or say explicitly that nothing is.