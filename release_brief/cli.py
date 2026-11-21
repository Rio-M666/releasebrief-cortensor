"""Command-line entry point.

Live mode (default):  python -m release_brief.cli --repo /path/to/repo
Offline mode:         python -m release_brief.cli --offline [--fixture examples/fixture_commits.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .brief import build_brief_offline, render_markdown
from .tools import collect_changed_files, collect_git_log, write_brief


def _offline(args: argparse.Namespace) -> int:
    if args.fixture:
        data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        log_json = json.dumps(data["log"])
        files_json = json.dumps(data["files"])
        window = data.get("window", args.since)
    else:
        log_json = collect_git_log(args.repo, args.since)
        files_json = collect_changed_files(args.repo, args.since)
        window = args.since
    brief = build_brief_offline(log_json, files_json, window)
    md = render_markdown(brief)
    saved = write_brief(md, "release-brief-offline.md")
    print(md)
    print(f"[offline] brief saved to {saved}")
    return 0


def _live(args: argparse.Namespace) -> int:
    from openminion import AgentOutputValidationError, ProviderError, TurnTimeoutError

    from .agent import run_live

    try:
        brief = run_live(args.repo, args.since)
    except ProviderError as exc:
        print(f"provider failed: {exc.code}: {exc.message}", file=sys.stderr)
        return 2
    except TurnTimeoutError as exc:
        print(f"turn timed out: {exc}", file=sys.stderr)
        return 3
    except AgentOutputValidationError as exc:
        print(f"structured output failed validation; raw text was:\n{exc.raw_text}", file=sys.stderr)
        return 4
    print(render_markdown(brief))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="release-brief", description=__doc__)
    parser.add_argument("--repo", default=".", help="path to a local git repository")
    parser.add_argument("--since", default="7 days ago", help="git date expression, e.g. '7 days ago'")
    parser.add_argument("--offline", action="store_true", help="no model, no network: deterministic brief")
    parser.add_argument("--fixture", help="offline mode only: JSON fixture instead of a real repo")
    args = parser.parse_args(argv)
    return _offline(args) if args.offline else _live(args)


if __name__ == "__main__":
    raise SystemExit(main())
