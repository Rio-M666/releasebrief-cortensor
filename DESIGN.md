# Design Note — ReleaseBrief Agent

Cortensor Hackathon #5 entry. One small, genuinely useful agent built on the
OpenMinion 0.1 Python SDK (`openminion==0.1.22`).

## Problem

Small teams ship code all week and then hand-write release notes / standup
digests from `git log` output. It is a 15–30 minute chore, it is easy to do
badly (raw commit dumps), and it happens on a schedule — an ideal repeatable
agent workflow.

## Concept: ReleaseBrief

Give the agent a local git repository and a time window. It produces a
structured, human-readable release brief (Markdown) in under a minute:

1. **Collect** — read-only tools pull the facts from git:
   - `get_git_log(repo_path, since)` → commits (hash, author, date, subject)
   - `get_changed_files(repo_path, since)` → `git diff --stat` style summary
2. **Draft** — the model (via the OpenMinion `Agent` facade) turns the raw
   facts into a brief and returns it as **typed output** (Pydantic model):
   title, highlights, breaking changes, contributor stats.
3. **Deliver** — a separate write-scoped tool `save_brief(markdown, filename)`
   persists the brief to `./briefs/`. Writing is a different permission class
   from reading, which deliberately exercises OpenMinion's tool scope /
   approval metadata.

Demo shape (fits a 1–5 minute video): run one command against this repo (or
the bundled fixture), watch the two read tools fire, see the typed brief
render, and open the saved Markdown file.

## Why this fits the hackathon rubric

| Criterion (weight) | How ReleaseBrief addresses it |
| --- | --- |
| Working functionality, useful outcome (25%) | Real chore automated; output is a file a team can paste into a release page |
| Meaningful SDK usage (20%) | `Agent` facade, run-scoped `@tool` tools with scope/idempotency metadata, `forced_tools` for the deterministic first run, explicit `session_id`, typed `output_type`, `ProviderError` / `TurnTimeoutError` handling |
| Reproducibility & demo quality (20%) | Pinned SDK, offline fixture mode, smoke tests, one-command demo |
| Building-block findings & feedback (25%) | Read vs write tool scopes, forced-tool behaviour, echo-provider limits, typed-output validation — logged in `SUBMISSION.md` |
| Relevance to builder workflows (10%) | Release/standup digests are a Cortensor/OpenMinion builder's own workflow |

## OpenMinion building blocks exercised

- **Agent execution** — `Agent(...).run(...)` with per-run `timeout_seconds`
- **Tools** — three decorated tools with explicit `min_scope` and
  `idempotent` metadata (two READ_ONLY, one write)
- **Permissions** — write tool declared non-read-only so policy can gate it
- **Sessions** — explicit, stable `session_id` per repository (`releasebrief-<repo>`)
- **Typed output** — Pydantic `ReleaseBrief` schema via `output_type=`
- **Diagnostics** — `ProviderError.code/message`, `TurnTimeoutError`,
  `AgentOutputValidationError.raw_text` surfaced to the CLI, never swallowed
- **Providers** — any tool-capable provider via `openminion setup`
  (OpenAI / Anthropic / Ollama / Cortensor Portal …); echo provider used only
  for credential-free wiring checks

## Modes

- **Live mode** (demo / judging): real provider configured via
  `openminion setup --no-chat`; the model selects and calls the tools.
- **Offline mode** (`--offline`): no model, no network. Uses the same tool
  functions against a fixture dataset (or a real local repo) plus a
  deterministic brief builder. Proves the workflow end-to-end in CI and in
  the smoke test; clearly labelled so it is never mistaken for a model run.

## Non-goals

No frontend, no multi-agent system, no GitHub API dependency, no hosted
deployment. Secrets stay in environment variables / OpenMinion config, never
in the repo.
