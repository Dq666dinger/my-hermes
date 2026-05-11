#!/usr/bin/env python3
"""Bootstrap a HermesWorkspace for text-agent collaboration."""

from __future__ import annotations

import argparse
from pathlib import Path

from hermes_cli.text_agent_workspace import (
    bootstrap_summary,
    bootstrap_workspace,
    format_bootstrap_summary,
)


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
    created_dirs, written_files = bootstrap_workspace(root, force=args.force)
    summary = bootstrap_summary(root, created_dirs, written_files, force=args.force)
    print(format_bootstrap_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
