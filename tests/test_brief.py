"""Tests for the deterministic offline brief builder and Markdown renderer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_brief.brief import build_brief_offline, render_markdown

LOG = """{"repo": "demo-shop-api", "since": "7 days ago", "commits": [
  {"hash": "a1b2c3d", "author": "Rio", "date": "2026-11-20", "subject": "feat: add coupons"},
  {"hash": "e4f5a6b", "author": "Rio", "date": "2026-11-19", "subject": "fix: double charge"},
  {"hash": "c7d8e9f", "author": "Ana", "date": "2026-11-19", "subject": "feat!: drop support for v1"}
]}"""
FILES = """{"repo": "demo-shop-api", "files_changed": ["a.py"], "summary": "1 file changed, 3 insertions(+)"}"""


def test_build_brief() -> None:
    brief = build_brief_offline(LOG, FILES, "7 days ago")
    assert brief.commit_count == 3
    assert brief.breaking_changes and "drop support" in brief.breaking_changes[0]
    assert brief.fixes and "double charge" in brief.fixes[0]
    assert brief.highlights and "add coupons" in brief.highlights[0]
    assert brief.contributors[0].startswith("Rio (2 commits)")


def test_render_markdown() -> None:
    md = render_markdown(build_brief_offline(LOG, FILES, "7 days ago"))
    assert md.startswith("# Release brief — demo-shop-api")
    assert "## Breaking changes" in md
    assert "## Contributors" in md
