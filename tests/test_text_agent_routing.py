from __future__ import annotations

from pathlib import Path

import pytest

from hermes_cli import text_agent_routing as tar


@pytest.mark.parametrize(
    ("prompt", "expected_route"),
    [
        ("帮我做一个美发店员工之间的搞笑短视频脚本，要求多反转。", "scriptwriter"),
        ("帮我设计一本赛博修仙小说的世界观和前三章大纲。", "novelist"),
        ("帮我写一个美发店短剧脚本大纲，要求多反转。", "scriptwriter"),
    ],
)
def test_classify_text_request_routes_examples(prompt, expected_route):
    route = tar.classify_text_request(prompt)
    assert route["route"] == expected_route


def test_classify_text_request_split_for_ip_adaptation():
    route = tar.classify_text_request(
        "我想做一个小说IP，先写世界观，再改成短视频短剧脚本。"
    )
    assert route["route"] == "split"
    assert route["adaptation_matches"]


def test_plan_text_request_returns_clarification_for_ambiguous_request(tmp_path):
    plan = tar.plan_text_request(
        "帮我先出一个剧情方案大纲。",
        workspace_root=tmp_path / "HermesWorkspace",
    )

    assert plan["route"] == "ambiguous"
    assert plan["tasks"] == []
    assert "scriptwriter" in plan["clarification"]
    assert "novelist" in plan["clarification"]


def test_default_project_name_preserves_chinese_text():
    name = tar.default_project_name("帮我设计一本赛博修仙小说的世界观和前三章大纲。")

    assert "赛博修仙" in name
    assert not name.startswith("text-project-")


def test_plan_text_request_split_creates_both_project_workspaces(tmp_path):
    root = tmp_path / "HermesWorkspace"

    plan = tar.plan_text_request(
        "我想做一个小说IP，先写世界观，再改成短视频短剧脚本。",
        workspace_root=root,
    )

    assert plan["route"] == "split"
    assert len(plan["tasks"]) == 2
    assert plan["tasks"][0]["assignee"] == "novelist"
    assert plan["tasks"][1]["assignee"] == "scriptwriter"
    assert "Dependency Note:" in plan["tasks"][1]["body"]
    assert Path(plan["tasks"][0]["workspace_path"]).exists()
    assert Path(plan["tasks"][1]["workspace_path"]).exists()
