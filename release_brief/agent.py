"""OpenMinion Agent wiring for ReleaseBrief (live, model-backed mode)."""

from __future__ import annotations

from openminion import Agent, ProviderError, TurnTimeoutError

from .brief import ReleaseBrief
from .tools import ALL_TOOLS

INSTRUCTIONS = """You are ReleaseBrief, an agent that writes release briefs from git history.

Workflow you must follow:
1. Call get_git_log and get_changed_files for the repository and window the user names.
2. Draft a brief from the tool results only. Do not invent commits, files, or authors.
3. Classify: new capabilities and user-facing changes are highlights; bug fixes go to
   fixes; anything that removes or incompatibly changes behaviour is a breaking change.
4. Call save_brief with the finished Markdown and a short filename, then confirm the
   saved path to the user.
Answer with the structured brief fields requested by the output schema."""


def run_live(repo_path: str, since: str, timeout_seconds: int = 180) -> ReleaseBrief:
    """Run the model-backed agent once and return the typed brief.

    Raises ProviderError / TurnTimeoutError / AgentOutputValidationError to the
    caller on purpose: failures must be visible, never silently swallowed.
    """
    session_id = f"releasebrief-{repo_path.rstrip('/').split('/')[-1] or 'repo'}"
    with Agent(
        instructions=INSTRUCTIONS,
        tools=ALL_TOOLS,
        forced_tools=["get_git_log", "get_changed_files"],
        output_type=ReleaseBrief,
        session_id=session_id,
    ) as agent:
        result = agent.run(
            f"Write a release brief for the git repository at {repo_path} "
            f"covering changes since '{since}'.",
            timeout_seconds=timeout_seconds,
        )
    if result.output is None:
        raise RuntimeError(f"agent returned no structured output; raw text: {result.text!r}")
    return result.output


__all__ = ["run_live", "ProviderError", "TurnTimeoutError"]
