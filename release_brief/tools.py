"""Tools for ReleaseBrief.

The pure functions (`collect_git_log`, `collect_changed_files`, `write_brief`)
hold all logic and are unit-testable without a model or the SDK runtime.
Thin `@tool` wrappers expose them to the OpenMinion agent with explicit
scope / idempotency metadata, as the SDK quickstart prescribes.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from openminion import tool

# --------------------------------------------------------------------------
# Pure logic (no SDK runtime involved)
# --------------------------------------------------------------------------


def _run_git(repo: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise ValueError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def collect_git_log(repo_path: str, since: str = "7 days ago", limit: int = 50) -> str:
    """Return recent commits of a local git repo as compact JSON lines."""
    repo = Path(repo_path).expanduser()
    if not (repo / ".git").exists():
        raise ValueError(f"not a git repository: {repo}")
    fmt = "%H%x1f%an%x1f%ad%x1f%s"
    out = _run_git(
        repo,
        ["log", f"--since={since}", f"--max-count={limit}", f"--pretty=format:{fmt}", "--date=short"],
    )
    commits = []
    for line in out.splitlines():
        if not line.strip():
            continue
        full_hash, author, date, subject = line.split("\x1f", 3)
        commits.append(
            {"hash": full_hash[:7], "author": author, "date": date, "subject": subject}
        )
    return json.dumps({"repo": str(repo), "since": since, "commits": commits}, ensure_ascii=False)


def collect_changed_files(repo_path: str, since: str = "7 days ago") -> str:
    """Summarise which files changed in the window, with insertion/deletion counts."""
    repo = Path(repo_path).expanduser()
    if not (repo / ".git").exists():
        raise ValueError(f"not a git repository: {repo}")
    # Compare HEAD against the newest commit older than the window; fall back
    # to the root commit when the whole history is inside the window.
    boundary = _run_git(repo, ["rev-list", "-1", f"--before={since}", "HEAD"]).strip()
    if not boundary:
        boundary = _run_git(repo, ["rev-list", "--max-parents=0", "HEAD"]).splitlines()[0].strip()
    stat = _run_git(repo, ["diff", "--shortstat", f"{boundary}..HEAD"]).strip()
    names = _run_git(repo, ["diff", "--name-only", f"{boundary}..HEAD"]).strip()
    files = [f for f in names.splitlines() if f.strip()]
    return json.dumps(
        {"repo": str(repo), "files_changed": files, "summary": stat or "no changes"},
        ensure_ascii=False,
    )


def write_brief(markdown: str, filename: str, out_dir: str = "briefs") -> str:
    """Write a brief markdown file under out_dir and return its path."""
    safe_name = Path(filename).name  # never allow path traversal from a model
    if not safe_name.endswith(".md"):
        safe_name += ".md"
    target_dir = Path(out_dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe_name
    target.write_text(markdown, encoding="utf-8")
    return str(target)


# --------------------------------------------------------------------------
# OpenMinion tool wrappers (run-scoped, exposed only for the agent's run)
# --------------------------------------------------------------------------


@tool(min_scope="READ_ONLY", idempotent=True)
def get_git_log(repo_path: str, since: str = "7 days ago") -> str:
    """List recent commits (hash, author, date, subject) of a local git repository since a date expression such as '7 days ago'."""
    return collect_git_log(repo_path, since)


@tool(min_scope="READ_ONLY", idempotent=True)
def get_changed_files(repo_path: str, since: str = "7 days ago") -> str:
    """Summarise which files changed in a local git repository since a date expression such as '7 days ago'."""
    return collect_changed_files(repo_path, since)


@tool(idempotent=False, dangerous=False)
def save_brief(markdown: str, filename: str) -> str:
    """Save a finished release brief as a Markdown file in the local briefs folder and return the saved path. This writes to disk."""
    return write_brief(markdown, filename)


ALL_TOOLS = [get_git_log, get_changed_files, save_brief]
READ_TOOLS = [get_git_log, get_changed_files]
