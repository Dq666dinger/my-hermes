from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_bootstrap_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "bootstrap_text_agent_workspace.py"
    )
    spec = importlib.util.spec_from_file_location(
        "bootstrap_text_agent_workspace", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_workspace_creates_expected_structure(tmp_path):
    module = _load_bootstrap_module()

    created_dirs, written_files = module.bootstrap_workspace(tmp_path, force=False)

    expected_dirs = {
        tmp_path / "shared_memory",
        tmp_path / "scriptwriter" / "memory",
        tmp_path / "scriptwriter" / "projects",
        tmp_path / "novelist" / "memory",
        tmp_path / "novelist" / "projects",
    }
    expected_files = {
        tmp_path / "shared_memory" / "user_preferences.md",
        tmp_path / "shared_memory" / "global_style_preferences.md",
        tmp_path / "shared_memory" / "project_index.md",
        tmp_path / "scriptwriter" / "memory" / "script_style_preferences.md",
        tmp_path / "scriptwriter" / "memory" / "user_feedback_log.md",
        tmp_path / "scriptwriter" / "memory" / "reusable_structures.md",
        tmp_path / "scriptwriter" / "projects" / "_template" / "00_project_brief.md",
        tmp_path / "scriptwriter" / "projects" / "_template" / "01_style_guide.md",
        tmp_path / "scriptwriter" / "projects" / "_template" / "02_episode_ideas.md",
        tmp_path / "scriptwriter" / "projects" / "_template" / "feedback_log.md",
        tmp_path / "scriptwriter" / "projects" / "_template" / "scripts" / "README.md",
        tmp_path / "novelist" / "memory" / "novel_style_preferences.md",
        tmp_path / "novelist" / "memory" / "user_feedback_log.md",
        tmp_path / "novelist" / "memory" / "genre_preferences.md",
        tmp_path / "novelist" / "projects" / "_template" / "00_project_brief.md",
        tmp_path / "novelist" / "projects" / "_template" / "01_worldbuilding.md",
        tmp_path / "novelist" / "projects" / "_template" / "02_characters.md",
        tmp_path / "novelist" / "projects" / "_template" / "03_plot_outline.md",
        tmp_path / "novelist" / "projects" / "_template" / "04_chapter_outline.md",
        tmp_path / "novelist" / "projects" / "_template" / "05_style_guide.md",
        tmp_path / "novelist" / "projects" / "_template" / "feedback_log.md",
        tmp_path / "novelist" / "projects" / "_template" / "chapters" / "README.md",
    }

    assert expected_dirs.issubset(set(created_dirs))
    assert expected_files.issubset(set(written_files))
    for path in expected_files:
        assert path.exists(), f"missing scaffolded file: {path}"


def test_bootstrap_workspace_preserves_existing_files_without_force(tmp_path):
    module = _load_bootstrap_module()
    target = tmp_path / "shared_memory" / "user_preferences.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom\n", encoding="utf-8")

    _created_dirs, written_files = module.bootstrap_workspace(tmp_path, force=False)

    assert target.read_text(encoding="utf-8") == "custom\n"
    assert target not in written_files


def test_bootstrap_workspace_force_overwrites_existing_files(tmp_path):
    module = _load_bootstrap_module()
    target = tmp_path / "shared_memory" / "user_preferences.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom\n", encoding="utf-8")

    _created_dirs, written_files = module.bootstrap_workspace(tmp_path, force=True)

    assert target in written_files
    content = target.read_text(encoding="utf-8")
    assert content.startswith("# User Preferences\n")
    assert "custom" not in content
