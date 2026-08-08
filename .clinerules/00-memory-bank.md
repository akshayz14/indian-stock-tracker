# Cline Persistent Memory Instructions

## Purpose

This project uses a local Memory Bank to preserve important project knowledge across Cline tasks and conversations.

The Memory Bank is located in:

`memory-bank/`

Cline MUST use the Memory Bank as persistent project context.

---

# BEFORE STARTING A TASK

Before making significant changes to the codebase:

1. Read:

   * `memory-bank/project-context.md`
   * `memory-bank/architecture.md`
   * `memory-bank/requirements.md`
   * `memory-bank/current-state.md`
   * `memory-bank/known-issues.md`

2. Read `memory-bank/decisions.md` when:

   * changing architecture
   * introducing a dependency
   * changing an existing implementation strategy
   * making an important technical decision

3. Read `memory-bank/task-history.md` when:

   * continuing previous work
   * the current task appears related to an earlier task
   * the user references previous work

Do not ask the user to repeat information that is already available in the Memory Bank.

---

# DURING THE TASK

While working:

* Follow existing architectural decisions.
* Follow existing coding conventions.
* Prefer existing project patterns over introducing new patterns.
* Do not change architecture unnecessarily.
* Do not introduce dependencies without justification.
* Do not duplicate functionality that already exists.
* If existing code contradicts the Memory Bank, inspect the codebase and determine which is current.

If an important discovery is made, consider whether it should be recorded in the Memory Bank.

---

# AFTER COMPLETING A TASK

Before finishing a significant task, determine whether the task changed any persistent project knowledge.

Update the appropriate Memory Bank files when necessary.

### Update `project-context.md` when:

* project purpose changes
* technology stack changes
* major platforms or environments change

### Update `architecture.md` when:

* architecture changes
* modules change
* data flow changes
* important patterns change

### Update `decisions.md` when:

* an important technical decision was made
* a dependency was deliberately selected
* an alternative was rejected
* a significant trade-off was accepted

### Update `current-state.md` when:

* a feature is completed
* a feature is partially implemented
* major work is currently in progress
* important implementation status changes

### Update `known-issues.md` when:

* a non-obvious bug is discovered
* a workaround is required
* an external limitation is discovered
* technical debt is identified

### Update `requirements.md` when:

* requirements change
* acceptance criteria change
* an important constraint is discovered

### Update `task-history.md` when:

* a significant task is completed
* a major feature is implemented
* a substantial refactoring is performed

---

# MEMORY QUALITY RULES

The Memory Bank is NOT a conversation transcript.

Do NOT store:

* greetings
* temporary conversation
* obvious information
* repetitive information
* entire code files
* large logs
* raw stack traces
* information that is only relevant to one tiny task
* guesses presented as facts

Store:

* decisions
* architecture
* important constraints
* project conventions
* non-obvious discoveries
* important bugs and workarounds
* current implementation state
* requirements
* lessons learned

Keep entries concise and factual.

Prefer updating an existing entry instead of creating duplicate information.

---

# SOURCE OF TRUTH

When there is a conflict:

1. Current source code
2. Explicit current user requirements
3. Current Memory Bank
4. Older task history

If the codebase clearly changed but the Memory Bank is outdated, update the Memory Bank.

Never blindly follow outdated Memory Bank information.

---

# MEMORY SAFETY

Never store:

* API keys
* passwords
* access tokens
* private keys
* secrets
* credentials
* personal sensitive information

If sensitive information is discovered, do not write it to the Memory Bank.

---

# COMPLETION CHECK

Before declaring a significant task complete, ask internally:

"Did this task teach us something that will be useful in a future Cline session?"

If yes, update the appropriate Memory Bank file.

If no, do not create unnecessary memory.
