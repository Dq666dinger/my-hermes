from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTWRITER_SOUL = REPO_ROOT / "plans" / "text_agent_profiles" / "scriptwriter.SOUL.md"
NOVELIST_SOUL = REPO_ROOT / "plans" / "text_agent_profiles" / "novelist.SOUL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_contains_all(text: str, needles: list[str]) -> None:
    for needle in needles:
        assert needle in text, f"missing expected text: {needle}"


def test_worker_soul_templates_include_phase8_sections():
    for path in (SCRIPTWRITER_SOUL, NOVELIST_SOUL):
        text = _read(path)
        _assert_contains_all(
            text,
            [
                "## Failure Recovery",
                "## Cost Control",
                "## Continuation Clarification",
            ],
        )


def test_worker_soul_templates_limit_retries_and_require_failure_comment_fields():
    for path in (SCRIPTWRITER_SOUL, NOVELIST_SOUL):
        text = _read(path)
        _assert_contains_all(
            text,
            [
                "retry at most once",
                "Failed stage",
                "Failure reason",
                "Completed partial work",
                "Recommended next step",
            ],
        )


def test_worker_soul_templates_require_block_instead_of_guessing():
    for path in (SCRIPTWRITER_SOUL, NOVELIST_SOUL):
        text = _read(path)
        _assert_contains_all(
            text,
            [
                "block the task instead of guessing",
                "block instead of drafting blind",
            ],
        )


def test_scriptwriter_template_requires_bounded_delivery_and_continuation_anchors():
    text = _read(SCRIPTWRITER_SOUL)
    _assert_contains_all(
        text,
        [
            "do not write a whole series when one episode or one concept is enough",
            "the project or series name",
            "the target episode, scene, section, or draft to continue or revise",
            "the prior-material file path or a concise summary of the approved material",
            "the requested changes, locked constraints, or review notes that must be applied",
        ],
    )


def test_novelist_template_requires_bounded_delivery_and_continuation_anchors():
    text = _read(NOVELIST_SOUL)
    _assert_contains_all(
        text,
        [
            "Default to one chapter or one bounded fragment per prose-writing pass",
            "the project or novel name",
            "the target chapter or section to continue or revise",
            "the prior-material file path or a concise summary of the approved material",
            "any locked plot beats, style constraints, or latest feedback that must carry forward",
        ],
    )
