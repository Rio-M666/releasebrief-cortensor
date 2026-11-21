"""Brief schema and the deterministic (offline) brief builder.

The Pydantic model is shared by both modes:
- live mode passes it to the OpenMinion Agent as `output_type=ReleaseBrief`;
- offline mode builds the same model deterministically from tool output,
  so the workflow can be exercised end-to-end with no model and no network.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from pydantic import BaseModel, Field

BREAKING_MARKERS = ("breaking", "!: ", "remove ", "drop support", "incompatible")
FEATURE_MARKERS = ("feat", "add", "new ")
FIX_MARKERS = ("fix", "bug", "hotfix")


class ReleaseBrief(BaseModel):
    """Structured release brief produced by the agent."""

    title: str = Field(description="One-line title, e.g. 'Release brief — myrepo (7 days)'")
    window: str = Field(description="Time window covered, e.g. '7 days ago -> now'")
    commit_count: int
    highlights: list[str] = Field(description="User-facing changes worth calling out")
    fixes: list[str] = Field(default_factory=list, description="Bug fixes in the window")
    breaking_changes: list[str] = Field(default_factory=list)
    contributors: list[str] = Field(description="'Name (n commits)' entries")
    files_summary: str = Field(description="Shortstat line for changed files")


def _classify(subject: str) -> str:
    low = subject.lower()
    if any(m in low for m in BREAKING_MARKERS):
        return "breaking"
    if any(low.startswith(m) or f" {m}" in low[:12] for m in FEATURE_MARKERS):
        return "highlight"
    if any(m in low for m in FIX_MARKERS):
        return "fix"
    return "highlight"


def build_brief_offline(log_json: str, files_json: str, window: str) -> ReleaseBrief:
    """Deterministically build a ReleaseBrief from the tools' JSON output."""
    log = json.loads(log_json)
    files = json.loads(files_json)
    commits = log["commits"]

    highlights: list[str] = []
    fixes: list[str] = []
    breaking: list[str] = []
    for c in commits:
        bucket = _classify(c["subject"])
        entry = f"{c['subject']} ({c['hash']})"
        if bucket == "breaking":
            breaking.append(entry)
        elif bucket == "fix":
            fixes.append(entry)
        else:
            highlights.append(entry)

    counts = Counter(c["author"] for c in commits)
    contributors = [f"{name} ({n} commits)" for name, n in counts.most_common()]

    repo_name = log["repo"].rstrip("/").split("/")[-1]
    title = f"Release brief — {repo_name} ({window})"
    return ReleaseBrief(
        title=title,
        window=window,
        commit_count=len(commits),
        highlights=highlights,
        fixes=fixes,
        breaking_changes=breaking,
        contributors=contributors,
        files_summary=files.get("summary", ""),
    )


def render_markdown(brief: ReleaseBrief) -> str:
    """Render a ReleaseBrief to the Markdown document that gets saved/shared."""

    def section(name: str, items: list[str]) -> str:
        if not items:
            return ""
        body = "\n".join(f"- {re.sub(r'\s+', ' ', i)}" for i in items)
        return f"\n## {name}\n{body}\n"

    md = f"# {brief.title}\n\n"
    md += f"Window: {brief.window} · Commits: {brief.commit_count} · Files: {brief.files_summary}\n"
    md += section("Highlights", brief.highlights)
    md += section("Fixes", brief.fixes)
    md += section("Breaking changes", brief.breaking_changes)
    if brief.contributors:
        md += "\n## Contributors\n" + "\n".join(f"- {c}" for c in brief.contributors) + "\n"
    return md
