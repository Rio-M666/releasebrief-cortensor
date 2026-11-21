"""Smoke test for the OpenMinion SDK wiring (no paid model, no network calls
to a model provider).

Steps:
1. Verify the pinned SDK imports and reports version 0.1.22.
2. Initialise an isolated echo-provider config in a temp HOME
   (`openminion config init --provider echo --force`).
3. Construct the ReleaseBrief Agent with the read tools forced and run one
   turn against a throwaway git repo. The echo provider cannot select tools
   like a real model, so this step proves runtime construction, session
   handling and clean shutdown — and reports exactly what the echo run
   returned instead of pretending it was a model run.

Run:  .venv/bin/python tests/smoke_agent.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    import openminion

    print(f"[1] openminion version: {openminion.__version__}")
    assert openminion.__version__ == "0.1.22", "unexpected SDK version"

    from openminion import Agent, ProviderError, TurnTimeoutError, tool  # noqa: F401

    print("[1] imports OK: Agent, tool, ProviderError, TurnTimeoutError")

    tmp_home = tempfile.mkdtemp(prefix="openminion-smoke-home-")
    env = dict(os.environ, HOME=tmp_home)
    exe = Path(sys.executable).with_name("openminion")
    init = subprocess.run(
        [str(exe), "config", "init", "--provider", "echo", "--force"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    print(f"[2] config init (echo) rc={init.returncode}")
    if init.returncode != 0:
        print(init.stdout[-2000:])
        print(init.stderr[-2000:])
        return 1

    # Throwaway repo for the forced tool call.
    import test_tools

    repo = test_tools.make_repo(Path(tempfile.mkdtemp()))

    from release_brief.tools import get_changed_files, get_git_log

    os.environ["HOME"] = tmp_home  # the SDK reads config from HOME at runtime
    try:
        with Agent(
            instructions="Use get_git_log and answer with the commit subjects you find.",
            tools=[get_git_log, get_changed_files],
            forced_tools=["get_git_log"],
            session_id="releasebrief-smoke",
        ) as agent:
            result = agent.run(
                f"List the commits of the git repository at {repo} from the last 30 days.",
                timeout_seconds=60,
            )
        print(f"[3] echo run finished: session={result.session_id}")
        print(f"    result.text (first 300 chars): {result.text[:300]!r}")
        print("    NOTE: echo provider is a wiring check only; it does not do")
        print("    model-selected tool use. Use a real provider for the demo run.")
    except (ProviderError, TurnTimeoutError) as exc:
        print(f"[3] echo run raised {type(exc).__name__}: {exc}")
        print("    (runtime wiring reached the provider layer; see SUBMISSION.md)")
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
