from __future__ import annotations


def test_kanban_tools_visible_with_active_toolsets_env(monkeypatch, tmp_path):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_ACTIVE_TOOLSETS", "kanban")

    import tools.kanban_tools  # noqa: F401
    from tools.registry import registry
    from toolsets import resolve_toolset

    schema = registry.get_definitions(set(resolve_toolset("kanban")), quiet=True)
    names = {s["function"].get("name") for s in schema if "function" in s}

    assert "kanban_create" in names
    assert "kanban_comment" in names
    assert "kanban_complete" in names
