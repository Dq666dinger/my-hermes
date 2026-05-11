---
name: kanban-worker
description: Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itself is auto-injected into every worker's system prompt as KANBAN_GUIDANCE (from agent/prompt_builder.py); this skill is what you load when you want deeper detail on specific scenarios.
version: 2.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, collaboration, workflow, pitfalls]
    related_skills: [kanban-orchestrator]
---

# Kanban Worker

> Auto-loaded for every dispatched worker. The mandatory lifecycle already lives in `KANBAN_GUIDANCE`; this skill is a compact refresher for reliable handoffs, retries, and human checkpoints.

## Core pattern

1. Call `kanban_show()` immediately and trust its task context over guesses.
2. Work inside `$HERMES_KANBAN_WORKSPACE` unless the task explicitly says otherwise.
3. Use `kanban_heartbeat(note=...)` for genuinely long work.
If you are still orienting after about 30 seconds because the workspace is large, you are reading many files, or you are waiting on a model/tool response, send a heartbeat before continuing.
4. Use `kanban_comment(...)` for extra context that should stay on the task thread.
5. If you need a human decision, call `kanban_block(reason="...")` with one concrete question.
6. When the requested work is actually done, call `kanban_complete(summary=..., metadata=...)`.

## Workspace rules

- `scratch`: read and write freely; it is disposable.
- `dir:<path>`: treat it as persistent shared state for future runs.
- `worktree`: behave like a real git worktree; commit there when the task asks for code changes.

## Memory hygiene

- When the workspace is persistent, keep durable preferences separate from one-off task details.
- Put repeated user taste into long-term memory files; keep project-specific twists and feedback inside the current project directory.
- If you create a new persistent project folder, update whatever project index or manifest the workspace already uses.

## Good completion shape

```python
kanban_complete(
    summary="delivered 3 short-video directions and 1 filming-ready draft",
    metadata={
        "artifacts": ["direction_options", "final_script"],
        "decisions": ["kept salon setting", "preserved non-marketing tone"],
    },
)
```

- Keep `summary` short and concrete.
- Put machine-readable facts in `metadata`.
- Only pass `created_cards=[...]` when you captured real ids from successful `kanban_create(...)` calls.

## Retry and block rules

- If `kanban_show()` reveals earlier failed runs, do not repeat the same path blindly.
- If the task is ambiguous, missing source material, or waiting on a user choice, block instead of guessing.
- If a tool call fails twice, explain the failure in a comment or block reason and stop retrying.
- If a task repeatedly dies before completion, shrink the amount of context you load, resume from the files already written, and send earlier heartbeats.
- If the task was already blocked, reassigned, or archived before you start, stop immediately.

## Cost control

- Prefer staged outputs over giant first drafts.
- Reuse project summaries, outlines, and durable notes before loading more raw context.
- Keep each run bounded to the deliverable the task actually requests.

## Do not

- Do not shell out to `hermes kanban ...` from inside the worker.
- Do not modify files outside the workspace unless the task explicitly requires it.
- Do not create follow-up tasks assigned to yourself; hand them to the right specialist.
- Do not mark the task complete if the requested output is still missing.
- Do not exit after writing files or comments without calling `kanban_complete(...)` or `kanban_block(...)`.
