# ReleaseBrief — an OpenMinion agent that writes your release brief

Built for **Cortensor Hackathon #5** with the OpenMinion 0.1 Python SDK
(`openminion==0.1.22`).

Point ReleaseBrief at a local git repository and a time window. It reads the
commits and changed files with read-only tools, drafts a structured brief
(highlights / fixes / breaking changes / contributors), and saves it as a
Markdown file you can paste into a release page or standup doc.

## Setup

Requires Python 3.11+ and git.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configure one model provider (credentials stay in OpenMinion's config /
environment, never in this repo):

```bash
openminion setup --no-chat        # pick OpenAI, Anthropic, Ollama, Cortensor Portal, ...
openminion doctor --check-turn    # verify the provider answers
```

## Run

Live (model-backed) mode:

```bash
python main.py --repo /path/to/repo --since "7 days ago"
```

Offline mode — no model, no network. Uses the same tool functions plus a
deterministic brief builder; against a real repo or the bundled fixture:

```bash
python main.py --offline --repo /path/to/repo --since "7 days ago"
python main.py --offline --fixture examples/fixture_commits.json
```

The finished brief is printed and saved to `briefs/`.

## Demo (1–5 min video script)

1. `python main.py --offline --fixture examples/fixture_commits.json` — show
   the classified brief (note the `feat!:` commit landing in Breaking changes).
2. `openminion setup --no-chat` already done → `python main.py --repo . --since "30 days ago"`
   and show the model calling `get_git_log` / `get_changed_files`, returning
   the typed `ReleaseBrief`, and `save_brief` writing the file.
3. Open the saved file in `briefs/`.

## How it works (OpenMinion SDK workflow)

- `release_brief/tools.py` — pure git/file logic, exposed to the agent via
  `@tool` wrappers with explicit scope metadata: `get_git_log` and
  `get_changed_files` are `min_scope="READ_ONLY", idempotent=True`;
  `save_brief` is the write tool (`idempotent=False`).
- `release_brief/agent.py` — the `Agent` facade: instructions, the three
  run-scoped tools, `forced_tools` for the two reads so the first run is
  reproducible, a stable per-repo `session_id`, and `output_type=ReleaseBrief`
  (Pydantic) so the app gets a validated object, not free text.
- `release_brief/brief.py` — the shared `ReleaseBrief` schema, the offline
  deterministic builder, and the Markdown renderer.
- `release_brief/cli.py` — live/offline entry points. `ProviderError`,
  `TurnTimeoutError`, and `AgentOutputValidationError` are surfaced with
  their codes / raw text, never swallowed.

## Tests

```bash
.venv/bin/python tests/run_all.py      # 5 unit tests against a real temp git repo
.venv/bin/python tests/smoke_agent.py  # SDK wiring smoke test (echo provider, offline)
```

## Submission

See `SUBMISSION.md` for the Building Blocks Tested note, What We Learned,
and the exact PR submission steps for Hackathon #5.

## License

MIT (sample/hackathon code).
