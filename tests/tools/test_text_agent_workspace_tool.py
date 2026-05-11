from __future__ import annotations

import json
from pathlib import Path


def test_text_agent_workspace_tool_visible_in_kanban_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake")
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    import tools.text_agent_workspace_tool  # noqa: F401
    from tools.registry import registry
    from toolsets import resolve_toolset

    schema = registry.get_definitions(set(resolve_toolset("hermes-cli")), quiet=True)
    names = {s["function"].get("name") for s in schema if "function" in s}
    assert "text_agent_workspace" in names


def test_text_agent_workspace_tool_visible_with_active_toolsets_env(monkeypatch, tmp_path):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_ACTIVE_TOOLSETS", "kanban")

    import tools.text_agent_workspace_tool  # noqa: F401
    from tools.registry import registry
    from toolsets import resolve_toolset

    schema = registry.get_definitions(set(resolve_toolset("kanban")), quiet=True)
    names = {s["function"].get("name") for s in schema if "function" in s}
    assert "text_agent_workspace" in names


def test_text_agent_workspace_tool_handler_round_trip(monkeypatch, tmp_path):
    root = tmp_path / "HermesWorkspace"
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake")
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACE", str(root))

    from tools import text_agent_workspace_tool as twt

    ensured = json.loads(
        twt._handle_text_agent_workspace(
            {
                "action": "ensure_project",
                "root": str(root),
                "department": "scriptwriter",
                "project_name": "Salon Reversal Series",
            }
        )
    )
    assert ensured["project_name"] == "Salon Reversal Series"
    project_path = Path(ensured["project_path"])
    assert project_path.exists()

    feedback = json.loads(
        twt._handle_text_agent_workspace(
            {
                "action": "append_feedback",
                "root": str(root),
                "department": "scriptwriter",
                "project_name": "Salon Reversal Series",
                "task_id": "t_demo",
                "feedback": "User wants stronger reversals and no hard sell.",
                "applied_changes": "episode ideas updated",
            }
        )
    )
    assert feedback["task_id"] == "t_demo"
    feedback_path = Path(feedback["feedback_log_path"])
    assert "stronger reversals" in feedback_path.read_text(encoding="utf-8")
