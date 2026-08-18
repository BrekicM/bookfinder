# Book Finder

## Development process

Always use the `test-driven-development` skill for development in this project — drive implementation test-first with red-green-refactor, don't write implementation code before a failing test exists for it.

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