"""Zero-dependency test runner: `python tests/run_all.py` (exit 1 on any failure)."""

import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import test_brief  # noqa: E402
import test_tools  # noqa: E402


def main() -> int:
    cases = [
        ("test_brief.test_build_brief", lambda: test_brief.test_build_brief()),
        ("test_brief.test_render_markdown", lambda: test_brief.test_render_markdown()),
        ("test_tools.test_git_log", lambda: test_tools.test_git_log(Path(tempfile.mkdtemp()))),
        ("test_tools.test_changed_files", lambda: test_tools.test_changed_files(Path(tempfile.mkdtemp()))),
        ("test_tools.test_write_brief", lambda: test_tools.test_write_brief(Path(tempfile.mkdtemp()))),
    ]
    failed = 0
    for name, fn in cases:
        try:
            fn()
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
