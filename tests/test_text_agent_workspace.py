from __future__ import annotations

from pathlib import Path

from hermes_cli import text_agent_workspace as taw


def test_ensure_project_creates_project_and_updates_index(tmp_path):
    root = tmp_path / "HermesWorkspace"

    summary = taw.ensure_project(
        root,
        department="scriptwriter",
        project_name="Salon Reversal Series",
    )

    project_dir = Path(summary["project_path"])
    assert project_dir.exists()
    assert (project_dir / "00_project_brief.md").exists()
    assert (project_dir / "scripts" / "README.md").exists()

    index_path = root / "shared_memory" / "project_index.md"
    content = index_path.read_text(encoding="utf-8")
    assert "Salon Reversal Series" in content
    assert "scriptwriter/projects/salon-reversal-series" in content


def test_resolve_workspace_root_from_project_path(tmp_path):
    root = tmp_path / "HermesWorkspace"
    summary = taw.ensure_project(
        root,
        department="novelist",
        project_name="Cyber Cultivation IP",
    )
    project_path = Path(summary["project_path"])

    resolved = taw.resolve_workspace_root(project_path)

    assert resolved == root.resolve()


def test_append_feedback_and_memory_note(tmp_path):
    root = tmp_path / "HermesWorkspace"

    feedback = taw.append_feedback_log(
        root,
        department="novelist",
        project_name="Cyber Cultivation IP",
        task_id="t_demo1234",
        feedback="Updated the heroine to be cold outside, warm inside.",
        applied_changes="characters and chapter outline adjusted",
    )
    feedback_path = Path(feedback["feedback_log_path"])
    feedback_content = feedback_path.read_text(encoding="utf-8")
    assert "t_demo1234" in feedback_content
    assert "cold outside, warm inside" in feedback_content

    memory = taw.append_memory_note(
        root,
        department="novelist",
        memory_key="genre_preferences",
        note="prefers visible growth arcs over instant overpowered openings",
    )
    memory_path = Path(memory["path"])
    memory_content = memory_path.read_text(encoding="utf-8")
    assert memory["added"] is True
    assert "prefers visible growth arcs" in memory_content
