"""Utilities for bootstrapping the text-agent collaboration workspace."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any


BASE_DIRS = [
    "shared_memory",
    "scriptwriter/memory",
    "scriptwriter/projects",
    "novelist/memory",
    "novelist/projects",
]


BASE_FILES = {
    "shared_memory/user_preferences.md": dedent(
        """\
        # User Preferences

        ## Stable preferences

        Record only repeated or explicitly long-term user preferences that
        should influence both scriptwriter and novelist tasks.

        ## Do not store here

        - One-off scene requests
        - Single-project twists or endings
        - Temporary experiments the user has not repeated
        """
    ),
    "shared_memory/global_style_preferences.md": dedent(
        """\
        # Global Style Preferences

        ## Cross-project guidance

        Keep shared preferences that apply across departments, such as:

        - preferred pacing tendencies
        - taboo content to avoid
        - recurring tone or emotional direction
        """
    ),
    "shared_memory/project_index.md": dedent(
        """\
        # Project Index

        | Project | Department | Path | Status | Last Updated | Notes |
        | --- | --- | --- | --- | --- | --- |
        """
    ),
    "scriptwriter/memory/script_style_preferences.md": dedent(
        """\
        # Script Style Preferences

        ## Long-term preferences

        Record only stable screenplay preferences that recur across tasks.
        Examples:

        - likes strong reversals
        - dislikes hard-sell advertising
        - prefers a fast scene rhythm
        """
    ),
    "scriptwriter/memory/user_feedback_log.md": dedent(
        """\
        # Scriptwriter Feedback Log

        Append concise feedback summaries with date, source task, and
        whether the note is project-specific or globally reusable.
        """
    ),
    "scriptwriter/memory/reusable_structures.md": dedent(
        """\
        # Reusable Script Structures

        Capture recurring beat structures, comedic setups, or scene patterns
        only after they prove reusable across multiple script tasks.
        """
    ),
    "novelist/memory/novel_style_preferences.md": dedent(
        """\
        # Novel Style Preferences

        ## Long-term preferences

        Record recurring fiction-writing preferences that should influence
        multiple projects, such as prose density, romance intensity, or
        preferred growth-arc pacing.
        """
    ),
    "novelist/memory/user_feedback_log.md": dedent(
        """\
        # Novelist Feedback Log

        Append concise feedback summaries with date, source task, and
        whether the note belongs to long-term taste or a single novel.
        """
    ),
    "novelist/memory/genre_preferences.md": dedent(
        """\
        # Genre Preferences

        Track repeated genre-level preferences that affect multiple novel
        projects, for example:

        - growth-first power fantasy
        - low-exposition openings
        - emotionally complex female leads
        """
    ),
}


SCRIPTWRITER_TEMPLATE_FILES = {
    "scriptwriter/projects/_template/00_project_brief.md": dedent(
        """\
        # Project Brief

        - Project name:
        - Core premise:
        - Intended platform or format:
        - Primary audience:
        - Hard constraints:
        - Forbidden elements:
        """
    ),
    "scriptwriter/projects/_template/01_style_guide.md": dedent(
        """\
        # Style Guide

        - Tone:
        - Comedy pattern:
        - Pacing:
        - Dialogue style:
        - Visual or production constraints:
        """
    ),
    "scriptwriter/projects/_template/02_episode_ideas.md": dedent(
        """\
        # Episode Ideas

        ## Candidate directions

        1.
        2.
        3.
        """
    ),
    "scriptwriter/projects/_template/feedback_log.md": dedent(
        """\
        # Feedback Log

        ## Entries

        - Date:
          Task:
          Feedback:
          Applied changes:
        """
    ),
    "scriptwriter/projects/_template/scripts/README.md": dedent(
        """\
        # Scripts Directory

        Store scene outlines, drafts, and filming-ready scripts here.
        Prefer one markdown file per deliverable.
        """
    ),
}


NOVELIST_TEMPLATE_FILES = {
    "novelist/projects/_template/00_project_brief.md": dedent(
        """\
        # Project Brief

        - Project name:
        - Core premise:
        - Target length:
        - Genre:
        - Main emotional promise:
        - Hard constraints:
        """
    ),
    "novelist/projects/_template/01_worldbuilding.md": dedent(
        """\
        # Worldbuilding

        ## Setting overview

        ## Rules of the world

        ## Factions, locations, or systems
        """
    ),
    "novelist/projects/_template/02_characters.md": dedent(
        """\
        # Characters

        ## Main cast

        ### Protagonist

        ### Key supporting roles
        """
    ),
    "novelist/projects/_template/03_plot_outline.md": dedent(
        """\
        # Plot Outline

        ## Main line

        ## Major turns

        ## Midpoint and climax
        """
    ),
    "novelist/projects/_template/04_chapter_outline.md": dedent(
        """\
        # Chapter Outline

        | Chapter | Goal | Conflict | Outcome | Notes |
        | --- | --- | --- | --- | --- |
        """
    ),
    "novelist/projects/_template/05_style_guide.md": dedent(
        """\
        # Style Guide

        - Narrative distance:
        - Prose density:
        - Emotional tone:
        - Dialogue style:
        - Forbidden cliches:
        """
    ),
    "novelist/projects/_template/feedback_log.md": dedent(
        """\
        # Feedback Log

        ## Entries

        - Date:
          Task:
          Feedback:
          Applied changes:
        """
    ),
    "novelist/projects/_template/chapters/README.md": dedent(
        """\
        # Chapters Directory

        Store chapter drafts or chapter summaries here. Use stable,
        sortable names such as `chapter_001.md`.
        """
    ),
}


VALID_DEPARTMENTS = {"scriptwriter", "novelist"}

MEMORY_FILE_MAP = {
    "shared": {
        "user_preferences": "shared_memory/user_preferences.md",
        "global_style_preferences": "shared_memory/global_style_preferences.md",
    },
    "scriptwriter": {
        "script_style_preferences": "scriptwriter/memory/script_style_preferences.md",
        "user_feedback_log": "scriptwriter/memory/user_feedback_log.md",
        "reusable_structures": "scriptwriter/memory/reusable_structures.md",
    },
    "novelist": {
        "novel_style_preferences": "novelist/memory/novel_style_preferences.md",
        "user_feedback_log": "novelist/memory/user_feedback_log.md",
        "genre_preferences": "novelist/memory/genre_preferences.md",
    },
}


def _write_file(path: Path, content: str, force: bool) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def bootstrap_workspace(root: Path, force: bool = False) -> tuple[list[Path], list[Path]]:
    """Create the shared text-agent workspace structure under ``root``."""
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    created_dirs: list[Path] = []
    written_files: list[Path] = []

    for rel in BASE_DIRS:
        directory = root / rel
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_dirs.append(directory)

    for rel_map in (BASE_FILES, SCRIPTWRITER_TEMPLATE_FILES, NOVELIST_TEMPLATE_FILES):
        for rel, content in rel_map.items():
            path = root / rel
            if _write_file(path, content, force=force):
                written_files.append(path)

    return created_dirs, written_files


def normalize_department(department: str) -> str:
    value = str(department or "").strip().lower()
    if value not in VALID_DEPARTMENTS:
        raise ValueError(
            f"unknown department {department!r}; expected one of "
            f"{sorted(VALID_DEPARTMENTS)}"
        )
    return value


def resolve_workspace_root(path: str | Path | None = None) -> Path:
    """Resolve the durable HermesWorkspace root from an explicit or env path."""
    raw = path
    if raw is None:
        raw = os.environ.get("HERMES_KANBAN_WORKSPACE") or "~/HermesWorkspace"
    candidate = Path(str(raw)).expanduser().resolve()

    for probe in (candidate, *candidate.parents):
        if (
            (probe / "shared_memory").is_dir()
            and (probe / "scriptwriter").is_dir()
            and (probe / "novelist").is_dir()
        ):
            return probe
    return candidate


def derive_project_slug(project_name: str, department: str) -> str:
    """Create a stable ASCII-ish slug for a project directory."""
    normalized_dept = normalize_department(department)
    text = str(project_name or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if not slug:
        digest = hashlib.sha1(str(project_name).encode("utf-8")).hexdigest()[:8]
        slug = f"{normalized_dept}-{digest}"
    return slug[:80]


def infer_current_project(root: str | Path | None = None) -> dict[str, str] | None:
    """Infer the current project from an explicit or env workspace path."""
    workspace_hint = os.environ.get("HERMES_KANBAN_WORKSPACE")
    if root is None and not workspace_hint:
        return None

    resolved_root = resolve_workspace_root(root)
    target = Path(str(root or workspace_hint)).expanduser().resolve()
    try:
        rel_parts = target.relative_to(resolved_root).parts
    except ValueError:
        return None
    if len(rel_parts) < 3:
        return None
    department, section, project_slug = rel_parts[:3]
    if section != "projects" or department not in VALID_DEPARTMENTS or project_slug == "_template":
        return None
    return {
        "department": department,
        "project_slug": project_slug,
        "project_path": str((resolved_root / department / "projects" / project_slug).resolve()),
    }


def _copy_project_template(
    template_dir: Path,
    project_dir: Path,
    *,
    force: bool,
) -> tuple[list[Path], list[Path]]:
    created_dirs: list[Path] = []
    written_files: list[Path] = []

    for src in sorted(template_dir.rglob("*")):
        rel = src.relative_to(template_dir)
        dest = project_dir / rel
        if src.is_dir():
            if not dest.exists():
                dest.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dest)
            continue
        if src.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copyfile(src, dest)
                written_files.append(dest)
            elif force:
                shutil.copyfile(src, dest)
                written_files.append(dest)
    return created_dirs, written_files


def _replace_once(text: str, needle: str, replacement: str) -> str:
    if needle not in text:
        return text
    return text.replace(needle, replacement, 1)


def _seed_project_metadata(
    project_dir: Path,
    department: str,
    project_name: str,
) -> list[Path]:
    updated: list[Path] = []
    normalized_dept = normalize_department(department)
    brief_path = project_dir / "00_project_brief.md"
    if brief_path.exists():
        content = brief_path.read_text(encoding="utf-8")
        if "- Project name:" in content and f"- Project name: {project_name}" not in content:
            content = _replace_once(content, "- Project name:", f"- Project name: {project_name}")
            brief_path.write_text(content, encoding="utf-8")
            updated.append(brief_path)
    if normalized_dept == "novelist":
        style_path = project_dir / "05_style_guide.md"
    else:
        style_path = project_dir / "01_style_guide.md"
    if style_path.exists():
        content = style_path.read_text(encoding="utf-8")
        if "Source request:" not in content:
            content = content.rstrip() + "\n\n## Source request\n\n- Project identity seeded automatically.\n"
            style_path.write_text(content, encoding="utf-8")
            updated.append(style_path)
    return updated


def _clean_table_cell(value: str) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()


def upsert_project_index(
    root: str | Path,
    *,
    project_name: str,
    department: str,
    project_path: str | Path,
    status: str = "active",
    notes: str = "",
    last_updated: str | None = None,
) -> Path:
    resolved_root = resolve_workspace_root(root)
    normalized_dept = normalize_department(department)
    bootstrap_workspace(resolved_root, force=False)

    index_path = resolved_root / "shared_memory" / "project_index.md"
    project_dir = Path(str(project_path)).expanduser().resolve()
    try:
        rel_path = project_dir.relative_to(resolved_root).as_posix()
    except ValueError:
        rel_path = project_dir.as_posix()
    updated = last_updated or datetime.now().strftime("%Y-%m-%d")
    new_row = (
        f"| {_clean_table_cell(project_name)} | {normalized_dept} | "
        f"{_clean_table_cell(rel_path)} | {_clean_table_cell(status)} | "
        f"{_clean_table_cell(updated)} | {_clean_table_cell(notes)} |"
    )

    lines = index_path.read_text(encoding="utf-8").splitlines()
    replaced = False
    for idx, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        cols = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cols) < 6 or cols[0] == "Project":
            continue
        row_project, row_dept, row_path = cols[:3]
        if row_dept == normalized_dept and (row_path == rel_path or row_project == project_name):
            lines[idx] = new_row
            replaced = True
            break
    if not replaced:
        lines.append(new_row)
    index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return index_path


def ensure_project(
    root: str | Path | None,
    *,
    department: str,
    project_name: str,
    project_slug: str | None = None,
    status: str = "active",
    notes: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """Ensure a department project exists and is indexed in shared memory."""
    resolved_root = resolve_workspace_root(root)
    bootstrap_workspace(resolved_root, force=False)
    normalized_dept = normalize_department(department)
    slug = project_slug or derive_project_slug(project_name, normalized_dept)
    project_dir = resolved_root / normalized_dept / "projects" / slug
    created_project = not project_dir.exists()
    project_dir.mkdir(parents=True, exist_ok=True)

    template_dir = resolved_root / normalized_dept / "projects" / "_template"
    created_dirs, written_files = _copy_project_template(
        template_dir,
        project_dir,
        force=force,
    )
    seeded_files = _seed_project_metadata(project_dir, normalized_dept, project_name)
    index_path = upsert_project_index(
        resolved_root,
        project_name=project_name,
        department=normalized_dept,
        project_path=project_dir,
        status=status,
        notes=notes,
    )
    return {
        "root": str(resolved_root),
        "department": normalized_dept,
        "project_name": project_name,
        "project_slug": slug,
        "project_path": str(project_dir),
        "created_project": created_project,
        "created_directory_count": len(created_dirs),
        "written_file_count": len(written_files),
        "seeded_file_count": len(seeded_files),
        "created_directories": [str(path) for path in created_dirs],
        "written_files": [str(path) for path in written_files],
        "seeded_files": [str(path) for path in seeded_files],
        "project_index_path": str(index_path),
    }


def append_feedback_log(
    root: str | Path | None,
    *,
    department: str,
    project_name: str,
    feedback: str,
    task_id: str | None = None,
    applied_changes: str = "",
    project_slug: str | None = None,
) -> dict[str, Any]:
    resolved_root = resolve_workspace_root(root)
    summary = ensure_project(
        resolved_root,
        department=department,
        project_name=project_name,
        project_slug=project_slug,
        force=False,
    )
    feedback_path = Path(summary["project_path"]) / "feedback_log.md"
    date_str = datetime.now().strftime("%Y-%m-%d")
    block = [
        "",
        f"- Date: {date_str}",
        f"  Task: {task_id or '(unspecified)'}",
        f"  Feedback: {feedback.strip()}",
        f"  Applied changes: {(applied_changes or 'pending').strip()}",
    ]
    content = feedback_path.read_text(encoding="utf-8")
    feedback_path.write_text(content.rstrip() + "\n" + "\n".join(block) + "\n", encoding="utf-8")
    return {
        **summary,
        "feedback_log_path": str(feedback_path),
        "task_id": task_id,
        "feedback": feedback.strip(),
        "applied_changes": (applied_changes or "pending").strip(),
    }


def append_memory_note(
    root: str | Path | None,
    *,
    department: str,
    memory_key: str,
    note: str,
) -> dict[str, Any]:
    resolved_root = resolve_workspace_root(root)
    bootstrap_workspace(resolved_root, force=False)
    scope = str(department or "").strip().lower()
    choices = MEMORY_FILE_MAP.get(scope)
    if not choices or memory_key not in choices:
        raise ValueError(
            f"unknown memory target department={department!r}, key={memory_key!r}"
        )
    target = resolved_root / choices[memory_key]
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        bootstrap_workspace(resolved_root, force=False)
    content = target.read_text(encoding="utf-8")
    marker = note.strip()
    if marker and marker not in content:
        prefix = f"- {marker}"
        target.write_text(content.rstrip() + "\n\n" + prefix + "\n", encoding="utf-8")
        added = True
    else:
        added = False
    return {
        "root": str(resolved_root),
        "department": scope,
        "memory_key": memory_key,
        "path": str(target),
        "added": added,
        "note": marker,
    }


def inspect_workspace(root: str | Path | None = None) -> dict[str, Any]:
    resolved_root = resolve_workspace_root(root)
    current_project = infer_current_project(root)
    return {
        "root": str(resolved_root),
        "workspace_hint": str(root or os.environ.get("HERMES_KANBAN_WORKSPACE") or ""),
        "current_project": current_project,
        "shared_memory_exists": (resolved_root / "shared_memory").is_dir(),
        "scriptwriter_projects_exists": (resolved_root / "scriptwriter" / "projects").is_dir(),
        "novelist_projects_exists": (resolved_root / "novelist" / "projects").is_dir(),
    }


def bootstrap_summary(
    root: Path,
    created_dirs: list[Path],
    written_files: list[Path],
    *,
    force: bool,
) -> dict[str, Any]:
    resolved_root = root.expanduser().resolve()
    return {
        "root": str(resolved_root),
        "force": force,
        "created_directory_count": len(created_dirs),
        "written_file_count": len(written_files),
        "created_directories": [str(path) for path in created_dirs],
        "written_files": [str(path) for path in written_files],
    }


def format_bootstrap_summary(summary: dict[str, Any]) -> str:
    """Render a human-readable summary for CLI/script callers."""
    lines = [
        f"Workspace root: {summary['root']}",
        f"Created directories: {summary['created_directory_count']}",
        f"Written files: {summary['written_file_count']}",
    ]
    written_files = summary.get("written_files") or []
    for path in written_files:
        lines.append(f" - {path}")
    return "\n".join(lines)
