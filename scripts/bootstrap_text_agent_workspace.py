#!/usr/bin/env python3
"""Bootstrap a HermesWorkspace for text-agent collaboration.

This scaffolds the directory and markdown-file layout used by the
scriptwriter / novelist workflow described in the local development plan.
It is intentionally conservative: existing files are preserved unless
``--force`` is passed.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


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


def _write_file(path: Path, content: str, force: bool) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def bootstrap_workspace(root: Path, force: bool) -> tuple[list[Path], list[Path]]:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap a HermesWorkspace for scriptwriter + novelist flows."
    )
    parser.add_argument(
        "--root",
        default="~/HermesWorkspace",
        help="Workspace root to create. Defaults to ~/HermesWorkspace.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite template files if they already exist.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    created_dirs, written_files = bootstrap_workspace(root, force=args.force)

    print(f"Workspace root: {root}")
    print(f"Created directories: {len(created_dirs)}")
    print(f"Written files: {len(written_files)}")
    for path in written_files:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
