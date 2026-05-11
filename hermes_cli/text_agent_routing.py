"""Routing helpers for the scriptwriter/novelist text-agent workflow."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hermes_cli.text_agent_workspace import ensure_project, resolve_workspace_root


SCRIPTWRITER_PRIMARY_KEYWORDS = {
    "short video",
    "short drama",
    "script",
    "storyboard",
    "shot list",
    "spoken script",
    "filmable",
    "短视频",
    "短剧",
    "脚本",
    "分镜",
    "拍摄",
    "口播",
}

SCRIPTWRITER_SECONDARY_KEYWORDS = {
    "搞笑",
    "反转",
    "剧情方案",
}

SCRIPTWRITER_KEYWORDS = SCRIPTWRITER_PRIMARY_KEYWORDS | SCRIPTWRITER_SECONDARY_KEYWORDS

NOVELIST_PRIMARY_KEYWORDS = {
    "novel",
    "worldbuilding",
    "chapter",
    "continuation",
    "fiction",
    "小说",
    "世界观",
    "章节",
    "续写",
    "番外",
}

NOVELIST_SECONDARY_KEYWORDS = {
    "character",
    "outline",
    "prose",
    "人物设定",
    "大纲",
    "文风",
}

NOVELIST_KEYWORDS = NOVELIST_PRIMARY_KEYWORDS | NOVELIST_SECONDARY_KEYWORDS

ADAPTATION_CUES = {
    "adapt",
    "adaptation",
    "ip",
    "改成",
    "改编",
    "先写世界观再改成",
    "先写小说再改成",
    "先写",
    "再改成",
}


@dataclass(frozen=True)
class RoutedTaskSpec:
    assignee: str
    title: str
    body: str
    workspace_path: str
    project_name: str
    project_slug: str
    parents: tuple[str, ...] = ()


def _normalize_text(text: str) -> str:
    return str(text or "").strip().lower()


def _keyword_matches(text: str, keywords: set[str]) -> list[str]:
    normalized = _normalize_text(text)
    return sorted(keyword for keyword in keywords if keyword in normalized)


def _has_primary_match(matches: list[str], primary_keywords: set[str]) -> bool:
    return any(match in primary_keywords for match in matches)


def classify_text_request(request: str) -> dict[str, Any]:
    normalized = _normalize_text(request)
    script_hits = _keyword_matches(normalized, SCRIPTWRITER_KEYWORDS)
    novel_hits = _keyword_matches(normalized, NOVELIST_KEYWORDS)
    adaptation_hits = _keyword_matches(normalized, ADAPTATION_CUES)
    has_script_primary = _has_primary_match(script_hits, SCRIPTWRITER_PRIMARY_KEYWORDS)
    has_novel_primary = _has_primary_match(novel_hits, NOVELIST_PRIMARY_KEYWORDS)

    if script_hits and novel_hits and adaptation_hits:
        route = "split"
    elif script_hits and novel_hits and ("先" in normalized and "再" in normalized):
        route = "split"
    elif script_hits and not novel_hits:
        route = "scriptwriter"
    elif novel_hits and not script_hits:
        route = "novelist"
    elif script_hits and novel_hits:
        if has_script_primary and not has_novel_primary:
            route = "scriptwriter"
        elif has_novel_primary and not has_script_primary:
            route = "novelist"
        elif len(script_hits) > len(novel_hits):
            route = "scriptwriter"
        elif len(novel_hits) > len(script_hits):
            route = "novelist"
        else:
            route = "ambiguous"
    else:
        route = "ambiguous"

    return {
        "route": route,
        "scriptwriter_matches": script_hits,
        "novelist_matches": novel_hits,
        "adaptation_matches": adaptation_hits,
    }


def default_project_name(request: str) -> str:
    stripped = str(request or "").strip()
    first_line = stripped.splitlines()[0] if stripped else "text project"
    compact = re.sub(r"\s+", " ", first_line).strip().strip("，。！？；：,.!?;:")
    if re.search(r"[\u4e00-\u9fff]", compact):
        return compact[:24].rstrip() + ("..." if len(compact) > 24 else "")
    ascii_tokens = re.findall(r"[A-Za-z0-9]+", first_line)
    if ascii_tokens:
        return " ".join(ascii_tokens[:6])
    digest = hashlib.sha1(first_line.encode("utf-8")).hexdigest()[:8]
    return f"text-project-{digest}"


def _short_title(prefix: str, request: str) -> str:
    first_line = str(request or "").strip().splitlines()[0] if str(request or "").strip() else prefix
    compact = re.sub(r"\s+", " ", first_line).strip()
    if len(compact) > 48:
        compact = compact[:45].rstrip() + "..."
    return f"{prefix}: {compact}"


def _task_body(
    request: str,
    *,
    assignee: str,
    workspace_path: str,
    project_name: str,
    dependency_note: str = "",
    reference_paths: tuple[tuple[str, str], ...] = (),
) -> str:
    deliverable = (
        "direction options first, then a filming-ready script package once the direction is clear"
        if assignee == "scriptwriter"
        else "project plan first, then the bounded novel deliverable requested by the user"
    )
    lines = [
        "Goal:",
        request.strip(),
        "",
        "Style or Tone:",
        "- Follow the explicit tone cues in the user request.",
        "- If the user has not fixed a direction yet, propose bounded options before long output.",
        "",
        "Hard Constraints:",
        "- Respect the latest user instructions exactly.",
        "- Reuse and update the persistent workspace files for this project.",
        "- Block instead of guessing when project identity or direction is unclear.",
        (
            "- This is a non-trivial script task: first pass must stay bounded."
            if assignee == "scriptwriter"
            else "- Keep the first pass bounded to planning and requested novel scope."
        ),
        (
            "- Before any full episode draft, write 2-3 direction options into "
            "a kanban comment and then block for user selection or adjustment "
            "unless the latest task comments already lock the direction."
            if assignee == "scriptwriter"
            else "- Do not expand beyond the requested chapter, outline, or planning scope."
        ),
        (
            "- Until the direction is locked, do not draft full episode files "
            "under scripts/ except lightweight scaffolding such as README placeholders."
            if assignee == "scriptwriter"
            else "- Until the direction is locked, do not finalize the full worldbuilding, character, plot-outline, or chapter-outline package beyond lightweight scaffolding and brief notes."
        ),
        "",
        "Deliverable Format:",
        f"- {deliverable}",
        "",
        "Workspace Path:",
        f"- {workspace_path}",
        "",
        "Project:",
        f"- {project_name}",
    ]
    if assignee != "scriptwriter":
        lines.insert(
            lines.index("Deliverable Format:") - 1,
            "- Before any long setting writeup, outline expansion, or chapter prose, write the working plan into a kanban comment and then block for user confirmation unless the latest task comments already lock the direction.",
        )
    if reference_paths:
        lines.extend(["", "Reference Project Paths:"])
        for label, path in reference_paths:
            lines.append(f"- {label}: {path}")
    if dependency_note:
        lines.extend(["", "Dependency Note:", dependency_note])
    return "\n".join(lines).rstrip()


def plan_text_request(
    request: str,
    *,
    workspace_root: str | Path | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    route_info = classify_text_request(request)
    resolved_root = resolve_workspace_root(workspace_root)
    effective_project_name = project_name or default_project_name(request)
    tasks: list[RoutedTaskSpec] = []

    if route_info["route"] == "scriptwriter":
        project = ensure_project(
            resolved_root,
            department="scriptwriter",
            project_name=effective_project_name,
            notes="planned by text-agent router",
        )
        tasks.append(
            RoutedTaskSpec(
                assignee="scriptwriter",
                title=_short_title("Scriptwriter", request),
                body=_task_body(
                    request,
                    assignee="scriptwriter",
                    workspace_path=project["project_path"],
                    project_name=effective_project_name,
                ),
                workspace_path=project["project_path"],
                project_name=effective_project_name,
                project_slug=project["project_slug"],
            )
        )
    elif route_info["route"] == "novelist":
        project = ensure_project(
            resolved_root,
            department="novelist",
            project_name=effective_project_name,
            notes="planned by text-agent router",
        )
        tasks.append(
            RoutedTaskSpec(
                assignee="novelist",
                title=_short_title("Novelist", request),
                body=_task_body(
                    request,
                    assignee="novelist",
                    workspace_path=project["project_path"],
                    project_name=effective_project_name,
                ),
                workspace_path=project["project_path"],
                project_name=effective_project_name,
                project_slug=project["project_slug"],
            )
        )
    elif route_info["route"] == "split":
        novel_project = ensure_project(
            resolved_root,
            department="novelist",
            project_name=effective_project_name,
            notes="planned by text-agent router",
        )
        script_project = ensure_project(
            resolved_root,
            department="scriptwriter",
            project_name=effective_project_name,
            notes="planned by text-agent router",
        )
        tasks.append(
            RoutedTaskSpec(
                assignee="novelist",
                title=_short_title("Novelist", request),
                body=_task_body(
                    request,
                    assignee="novelist",
                    workspace_path=novel_project["project_path"],
                    project_name=effective_project_name,
                ),
                workspace_path=novel_project["project_path"],
                project_name=effective_project_name,
                project_slug=novel_project["project_slug"],
            )
        )
        tasks.append(
            RoutedTaskSpec(
                assignee="scriptwriter",
                title=_short_title("Scriptwriter", request),
                body=_task_body(
                    request,
                    assignee="scriptwriter",
                    workspace_path=script_project["project_path"],
                    project_name=effective_project_name,
                    reference_paths=(
                        ("paired novelist project", novel_project["project_path"]),
                    ),
                    dependency_note=(
                        "This task depends on the paired novelist task. Read the "
                        "paired novelist project summaries first, especially "
                        "01_worldbuilding.md, 02_characters.md, 03_plot_outline.md, "
                        "04_chapter_outline.md, 05_style_guide.md, and the latest "
                        "feedback_log.md, then adapt without changing locked canon."
                    ),
                ),
                workspace_path=script_project["project_path"],
                project_name=effective_project_name,
                project_slug=script_project["project_slug"],
            )
        )

    clarification = None
    if route_info["route"] == "ambiguous":
        clarification = (
            "这条需求目前无法稳定判断该交给 scriptwriter 还是 novelist。"
            "请先确认你要的是短视频/剧本产出，还是小说/世界观/章节产出。"
        )

    return {
        **route_info,
        "workspace_root": str(resolved_root),
        "project_name": effective_project_name,
        "tasks": [
            {
                "assignee": task.assignee,
                "title": task.title,
                "body": task.body,
                "workspace_path": task.workspace_path,
                "project_name": task.project_name,
                "project_slug": task.project_slug,
                "parents": list(task.parents),
            }
            for task in tasks
        ],
        "clarification": clarification,
    }
