"""Unit tests for the pure tool logic, run against a real temporary git repo."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_brief.tools import collect_changed_files, collect_git_log, write_brief


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def make_repo(tmp: Path) -> Path:
    repo = tmp / "demo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "app.py").write_text("print('v1')\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "feat: initial import")
    (repo / "app.py").write_text("print('v2')\n")
    (repo / "fix.py").write_text("# fix\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fix: correct output")
    return repo


def test_git_log(tmp: Path) -> None:
    repo = make_repo(tmp)
    data = json.loads(collect_git_log(str(repo), "30 days ago"))
    subjects = [c["subject"] for c in data["commits"]]
    assert subjects == ["fix: correct output", "feat: initial import"], subjects
    assert all(len(c["hash"]) == 7 for c in data["commits"])


def test_changed_files(tmp: Path) -> None:
    repo = make_repo(tmp)
    data = json.loads(collect_changed_files(str(repo), "30 days ago"))
    assert set(data["files_changed"]) == {"app.py", "fix.py"}, data
    assert "2 files changed" in data["summary"]


def test_write_brief(tmp: Path) -> None:
    out = write_brief("# hello", "../evil.md", out_dir=str(tmp / "briefs"))
    path = Path(out)
    assert path.name == "evil.md" and path.parent == tmp / "briefs"  # traversal stripped
    assert path.read_text() == "# hello"
