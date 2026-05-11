#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <task_id> <profile>" >&2
  exit 2
fi

task_id="$1"
profile="$2"

hermes_bin="${HERMES_BIN:-/home/lenovo/.local/bin/hermes}"
db_path="${HERMES_KANBAN_DB:-/home/lenovo/.hermes/kanban.db}"
workspaces_root="${HERMES_KANBAN_WORKSPACES_ROOT:-/home/lenovo/.hermes/kanban/workspaces}"
board="${HERMES_KANBAN_BOARD:-default}"
ttl="${HERMES_KANBAN_TTL:-900}"

# Reuse the proxy environment that the user systemd session already knows
# about so foreground runs behave like the live gateway path.
if command -v systemctl >/dev/null 2>&1; then
  while IFS= read -r line; do
    [ -n "$line" ] && export "$line"
  done < <(
    systemctl --user show-environment 2>/dev/null \
      | grep -E '^(http_proxy|https_proxy|all_proxy|no_proxy|HTTP_PROXY|HTTPS_PROXY|ALL_PROXY|NO_PROXY)=' \
      || true
  )
fi

"$hermes_bin" kanban claim "$task_id" --ttl "$ttl" >/dev/null

eval "$(
  python3 - <<PY
import shlex
import sqlite3

task_id = ${task_id@Q}
db_path = ${db_path@Q}
conn = sqlite3.connect(db_path)
row = conn.execute(
    "select current_run_id, claim_lock, workspace_path from tasks where id=?",
    (task_id,),
).fetchone()
if row is None:
    raise SystemExit(f"task not found: {task_id}")
run_id, claim_lock, workspace_path = row
if not workspace_path:
    raise SystemExit(f"task has no workspace_path after claim: {task_id}")
print(f"export HERMES_KANBAN_RUN_ID={run_id}")
print(f"export HERMES_KANBAN_CLAIM_LOCK={shlex.quote(str(claim_lock))}")
print(f"export HERMES_KANBAN_WORKSPACE={shlex.quote(str(workspace_path))}")
PY
)"

export HERMES_KANBAN_TASK="$task_id"
export HERMES_KANBAN_DB="$db_path"
export HERMES_KANBAN_WORKSPACES_ROOT="$workspaces_root"
export HERMES_KANBAN_BOARD="$board"
export HERMES_PROFILE="$profile"

cd "$HERMES_KANBAN_WORKSPACE"
exec "$hermes_bin" -p "$profile" --skills kanban-worker chat -q "work kanban task $task_id"
