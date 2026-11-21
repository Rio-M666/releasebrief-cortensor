# Hackathon #5 Submission Notes — ReleaseBrief

Project: ReleaseBrief (this repository)
SDK: OpenMinion 0.1.22 (`openminion==0.1.22`, PyPI), Python 3.12
Status: implemented and verified locally (unit tests + SDK smoke test +
offline end-to-end demo). Live model demo video and PR not yet submitted —
see "Remaining steps" below.

## Building Blocks Tested

| Building block | How ReleaseBrief uses it | Worked? |
| --- | --- | --- |
| Agent execution | `Agent(...).run(msg, timeout_seconds=...)` inside a context manager | ✅ Clean startup/shutdown; `run_state=completed` |
| Decorated tools | `@tool(min_scope="READ_ONLY", idempotent=True)` read tools; write tool with `idempotent=False` | ✅ Schema derived from annotations/docstrings as documented |
| Permissions / scopes | Read tools declared READ_ONLY; `save_brief` deliberately left non-read-only as the write path | ⚠️ Partially — see Finding 2 |
| Sessions | Stable per-repo `session_id` (`releasebrief-<repo>`); smoke run used `releasebrief-smoke` | ✅ Session id echoed back on the result |
| Typed output | `output_type=ReleaseBrief` (Pydantic) in live mode; same schema built deterministically offline | ✅ Schema validates; live validation path wired to `AgentOutputValidationError` |
| Diagnostics | `result.stats` / `result.metadata`, `ProviderError`, `TurnTimeoutError` surfaced in CLI | ✅ Stats are rich (llm_calls, tool_calls, duration, termination reason) |
| Providers | Echo provider for credential-free wiring checks; real provider via `openminion setup` for the demo | ⚠️ Echo works but cannot exercise tools — see Finding 1 |
| Config | `openminion config init --provider echo --force` in an isolated HOME | ✅ Fully offline, reproducible |

## Findings (product feedback)

### Finding 1 — `forced_tools` does not execute the tool under the echo provider

- **Steps to reproduce:** configure the echo provider
  (`openminion config init --provider echo --force`), then run an `Agent`
  with a decorated READ_ONLY tool and `forced_tools=["<tool>"]`
  (our `tests/smoke_agent.py` does exactly this).
- **Expected:** the docs say `forced_tools` "makes the first demo exercise
  the tool" and only caution that echo "cannot prove *model-selected* tool
  use" — a forced tool is not model-selected, so we expected it to fire.
- **Actual:** the run completes (`run_state=completed`,
  `tool_loop_termination_reason=model_final`) with
  `stats.tool_calls == 0`; `result.text` is the prompt echoed back. There is
  no signal in the result that the forced tool was skipped — we only caught
  it by reading `stats`.
- **Suggestion:** either execute forced tools before the first model turn
  regardless of provider, or surface a visible warning (e.g. in
  `result.metadata`) when a forced tool never ran, so a builder's first
  "working demo" cannot silently be a no-op.

### Finding 2 — No documented scope value for write tools

- The quickstart and examples only ever show `min_scope="READ_ONLY"`. For a
  tool that writes files there is no documented enum value to declare
  (e.g. `WORKSPACE_WRITE`), so we omitted `min_scope` on `save_brief` and
  relied on `idempotent=False` — but it is unclear what scope the runtime
  assigns by default, which makes the permission story hard to reason about
  and hard to demonstrate to judges.
- **Suggestion:** publish the full `min_scope` value list in the Tool System
  docs, with one worked example of a write tool.

### What worked well

- The quickstart path is genuinely reproducible: pinned install, config
  init, and an agent run all worked first try on a clean venv (Python 3.12).
- `AgentRunResult.stats` / `.metadata` are excellent for diagnostics — the
  tool-call counters are exactly how Finding 1 was proven.
- Run-scoped tool registration/cleanup matches the docs; nothing leaked
  into the global tool list after the `with` block.

## What We Learned

- Treat the echo provider as a wiring check only; budget a real
  tool-capable model for the first end-to-end verification, and assert on
  `stats.tool_calls > 0` in smoke tests instead of trusting `result.text`.
- Keeping tool *logic* in pure functions (separate from the `@tool`
  wrappers) made the whole workflow testable offline and gave us a
  deterministic fallback demo — a pattern worth recommending to other
  SDK builders.
- Typed output (`output_type=`) is the right contract between an agent and
  an application; sharing one Pydantic schema between live and offline
  modes kept both honest.

## Remaining steps to submit (before the Dec 19, 2026 deadline)

1. Push this repo to a public GitHub repository.
2. Configure a real provider (`openminion setup --no-chat`; Cortensor
   Portal if access is granted) and run the live demo:
   `python main.py --repo . --since "30 days ago"` — verify
   `tool_calls > 0` and a brief file appears in `briefs/`.
3. Record a 1–5 minute demo video of the live run and add its link to the
   README.
4. Fork/clone/star the official OpenMinion repository
   (github.com/OpenMinion/openminion) and follow @OpenMinion / @Cortensor
   on GitHub and X (participation step 2 in the hackathon docs).
5. Open a PR to the dedicated Hackathon #5 submission repository (URL to
   be announced by Cortensor; check
   https://docs-v2.cortensor.network/ecosystem/hackathon-5/ and the
   DoraHacks page) linking: this public repo, the demo video, and this
   SUBMISSION.md (Building Blocks Tested + What We Learned).
6. Also submit the project on the DoraHacks hackathon page for
   Cortensor Hackathon #5.
7. Designate one payout wallet for $COR (prizes: 50% liquid upfront,
   50% in a one-month staking lock).
