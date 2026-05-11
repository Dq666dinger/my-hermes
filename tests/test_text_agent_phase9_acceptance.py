from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_cli import kanban as kc
from hermes_cli import kanban_db as kb
from hermes_cli import text_agent_routing as tar


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


def test_phase9_scenario_a_scriptwriter_plan_is_bounded_and_workspace_backed(tmp_path):
    root = tmp_path / "HermesWorkspace"
    request = (
        "\u5e2e\u6211\u5199\u4e00\u4e2a\u7f8e\u53d1\u5e97\u7cfb\u5217\u641e\u7b11"
        "\u77ed\u89c6\u9891\uff0c\u5458\u5de5\u548c\u8001\u677f\u4e4b\u95f4\uff0c"
        "\u8981\u6c42\u591a\u53cd\u8f6c\uff0c\u4e0d\u8981\u8425\u9500\u3002"
    )

    plan = tar.plan_text_request(
        request,
        workspace_root=root,
        project_name="Salon Comedy Series",
    )

    assert plan["route"] == "scriptwriter"
    assert len(plan["tasks"]) == 1
    task = plan["tasks"][0]
    project_dir = Path(task["workspace_path"])

    assert task["assignee"] == "scriptwriter"
    assert project_dir.exists()
    assert "direction options first" in task["body"]
    assert "Block instead of guessing" in task["body"]
    assert "kanban comment" in task["body"]
    assert "block for user selection or adjustment" in task["body"]
    assert "do not draft full episode files under scripts/" in task["body"]
    assert (project_dir / "00_project_brief.md").exists()
    assert (project_dir / "scripts" / "README.md").exists()

    project_index = (root / "shared_memory" / "project_index.md").read_text(encoding="utf-8")
    assert "Salon Comedy Series" in project_index


def test_phase9_scenario_b_novelist_plan_creates_expected_project_files(tmp_path):
    root = tmp_path / "HermesWorkspace"
    request = (
        "\u5e2e\u6211\u8bbe\u8ba1\u4e00\u90e8\u8d5b\u535a\u4fee\u4ed9\u5c0f\u8bf4"
        "\uff0c\u4e3b\u89d2\u4e0d\u8981\u5f00\u5c40\u592a\u5f3a\uff0c\u5973\u4e3b"
        "\u5916\u51b7\u5185\u70ed\uff0c\u5148\u7ed9\u4e16\u754c\u89c2\u3001\u4eba"
        "\u7269\u548c\u524d\u4e09\u7ae0\u5927\u7eb2\u3002"
    )

    plan = tar.plan_text_request(
        request,
        workspace_root=root,
        project_name="Cyber Cultivation Novel",
    )

    assert plan["route"] == "novelist"
    assert len(plan["tasks"]) == 1
    task = plan["tasks"][0]
    project_dir = Path(task["workspace_path"])

    assert task["assignee"] == "novelist"
    assert project_dir.exists()
    assert "project plan first" in task["body"]
    assert "kanban comment" in task["body"]
    assert "block for user confirmation" in task["body"]
    assert "do not finalize the full worldbuilding" in task["body"]
    assert (project_dir / "01_worldbuilding.md").exists()
    assert (project_dir / "02_characters.md").exists()
    assert (project_dir / "04_chapter_outline.md").exists()
    assert (project_dir / "feedback_log.md").exists()


def test_phase9_scenario_c_split_route_references_paired_novelist_project(
    kanban_home, tmp_path
):
    root = tmp_path / "HermesWorkspace"
    request = (
        "\u628a\u521a\u624d\u90a3\u90e8\u8d5b\u535a\u4fee\u4ed9\u5c0f\u8bf4 IP "
        "\u6539\u6210\u4e00\u4e2a 3 \u96c6\u77ed\u89c6\u9891\u77ed\u5267\u65b9\u6848\u3002"
    )

    out = kc.run_slash(
        f"route-text-request '{request}' --workspace-root '{root}' --create --json"
    )
    payload = json.loads(out)

    assert payload["route"] == "split"
    assert len(payload["tasks"]) == 2
    assert len(payload["created_tasks"]) == 2

    novel_task, script_task = payload["tasks"]
    created_novel, created_script = payload["created_tasks"]

    assert novel_task["assignee"] == "novelist"
    assert script_task["assignee"] == "scriptwriter"
    assert created_script["parents"] == [created_novel["task_id"]]
    assert "Reference Project Paths:" in script_task["body"]
    assert novel_task["workspace_path"] in script_task["body"]
    assert "01_worldbuilding.md" in script_task["body"]
    assert "locked canon" in script_task["body"]

    first_show = json.loads(kc.run_slash(f"show {created_novel['task_id']} --json"))
    second_show = json.loads(kc.run_slash(f"show {created_script['task_id']} --json"))
    assert first_show["task"]["status"] == "ready"
    assert second_show["task"]["status"] == "todo"
    assert novel_task["workspace_path"] in second_show["task"]["body"]

    project_index = (root / "shared_memory" / "project_index.md").read_text(encoding="utf-8")
    assert "| novelist |" in project_index
    assert "| scriptwriter |" in project_index


def test_phase9_orchestrator_contract_requires_dir_workspace_args():
    contract = Path("plans/text_agent_profiles/orchestrator.SOUL.md").read_text(
        encoding="utf-8"
    )

    assert 'workspace_kind="dir"' in contract
    assert "workspace_path" in contract
    assert "Do not only mention the path in the task body." in contract
    assert "HERMES_KANBAN_WORKSPACE" in contract
    assert "kanban_comment(...)" in contract
    assert "kanban_block(...)" in contract
    assert "no full episode drafts under `scripts/`" in contract
    assert "no full worldbuilding / character / chapter-outline package or chapter prose" in contract
    assert "cyber-cultivation novel" in contract
    assert "first three chapter outlines" in contract


def test_phase9_novelist_contract_blocks_broad_package_requests():
    contract = Path("plans/text_agent_profiles/novelist.SOUL.md").read_text(
        encoding="utf-8"
    )

    assert "Treat broad new-project package requests as direction-unlocked" in contract
    assert "design a cyber-cultivation novel" in contract
    assert "the first three chapter outlines" in contract
    assert "the first run must post 2-3 planning directions or framing options" in contract
    assert "Do not ship the full worldbuilding / characters / chapter-outline package in that first run." in contract
