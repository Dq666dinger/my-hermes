"""Structured workspace helpers for scriptwriter/novelist kanban flows."""

from __future__ import annotations

import json
import logging
import os

from hermes_cli.text_agent_workspace import (
    append_feedback_log,
    append_memory_note,
    ensure_project,
    inspect_workspace,
)
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def _check_text_agent_workspace_mode() -> bool:
    if os.environ.get("HERMES_KANBAN_TASK"):
        return True
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        toolsets = cfg.get("toolsets", [])
        return "kanban" in toolsets
    except Exception:
        return False


def _handle_text_agent_workspace(args: dict, **_kw) -> str:
    action = str(args.get("action", "")).strip().lower()
    root = args.get("root")

    try:
        if action == "inspect":
            return tool_result(inspect_workspace(root))
        if action == "ensure_project":
            department = args.get("department")
            project_name = args.get("project_name")
            if not department or not project_name:
                return tool_error("ensure_project requires department and project_name")
            return tool_result(
                ensure_project(
                    root,
                    department=str(department),
                    project_name=str(project_name),
                    project_slug=args.get("project_slug"),
                    status=str(args.get("status") or "active"),
                    notes=str(args.get("notes") or ""),
                    force=bool(args.get("force", False)),
                )
            )
        if action == "append_feedback":
            department = args.get("department")
            project_name = args.get("project_name")
            feedback = args.get("feedback")
            if not department or not project_name or not feedback:
                return tool_error(
                    "append_feedback requires department, project_name, and feedback"
                )
            return tool_result(
                append_feedback_log(
                    root,
                    department=str(department),
                    project_name=str(project_name),
                    project_slug=args.get("project_slug"),
                    task_id=args.get("task_id"),
                    feedback=str(feedback),
                    applied_changes=str(args.get("applied_changes") or ""),
                )
            )
        if action == "append_memory_note":
            department = args.get("department")
            memory_key = args.get("memory_key")
            note = args.get("note")
            if not department or not memory_key or not note:
                return tool_error(
                    "append_memory_note requires department, memory_key, and note"
                )
            return tool_result(
                append_memory_note(
                    root,
                    department=str(department),
                    memory_key=str(memory_key),
                    note=str(note),
                )
            )
        return tool_error(
            "unknown action; expected inspect, ensure_project, append_feedback, or append_memory_note"
        )
    except Exception as exc:
        logger.exception("text_agent_workspace failed")
        return tool_error(f"text_agent_workspace: {exc}")


TEXT_AGENT_WORKSPACE_SCHEMA = {
    "name": "text_agent_workspace",
    "description": (
        "Manage the persistent scriptwriter/novelist workspace used by the "
        "text-agent kanban flow. Use this tool instead of ad-hoc file edits "
        "when you need to inspect the workspace, ensure a project directory "
        "exists from the department template, append project feedback, or "
        "record a durable memory note."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "inspect",
                    "ensure_project",
                    "append_feedback",
                    "append_memory_note",
                ],
                "description": "Workspace action to perform.",
            },
            "root": {
                "type": "string",
                "description": (
                    "Optional workspace root or current project path. When "
                    "omitted, the tool uses HERMES_KANBAN_WORKSPACE or "
                    "~/HermesWorkspace."
                ),
            },
            "department": {
                "type": "string",
                "enum": ["shared", "scriptwriter", "novelist"],
                "description": "Target department or shared memory scope.",
            },
            "project_name": {
                "type": "string",
                "description": "Human-readable project name for project actions.",
            },
            "project_slug": {
                "type": "string",
                "description": "Optional stable folder slug. Omit to auto-derive one.",
            },
            "status": {
                "type": "string",
                "description": "Project status recorded in shared_memory/project_index.md.",
            },
            "notes": {
                "type": "string",
                "description": "Notes recorded in shared_memory/project_index.md.",
            },
            "force": {
                "type": "boolean",
                "description": "Whether ensure_project should overwrite template files.",
            },
            "task_id": {
                "type": "string",
                "description": "Optional task id to include in appended feedback.",
            },
            "feedback": {
                "type": "string",
                "description": "Project-level feedback or outcome summary to append.",
            },
            "applied_changes": {
                "type": "string",
                "description": "How the feedback was applied, if known.",
            },
            "memory_key": {
                "type": "string",
                "description": (
                    "Memory file key. Examples: user_preferences, "
                    "global_style_preferences, script_style_preferences, "
                    "reusable_structures, novel_style_preferences, genre_preferences."
                ),
            },
            "note": {
                "type": "string",
                "description": "Durable note to append to the chosen memory file.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="text_agent_workspace",
    toolset="kanban",
    schema=TEXT_AGENT_WORKSPACE_SCHEMA,
    handler=_handle_text_agent_workspace,
    check_fn=_check_text_agent_workspace_mode,
    emoji="🗂",
)
