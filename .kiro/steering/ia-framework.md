---
inclusion: always
---

# IA-Framework: Project Constitution for Kiro

This workspace is governed by IA-Framework. The rules below are not suggestions;
local git hooks and CI enforce them, and work that ignores them will be blocked
at commit or push time.

## Use this project's spec layout, not Kiro's

**Do not create a Kiro spec tree.** This project already has one, and Kiro's
default artifacts collide with it — `tasks.md` is the same filename in both.

| Kiro default | Use instead |
|---|---|
| `requirements.md` | `specs/<slug>/spec.md` |
| `design.md` | `specs/<slug>/plan.md` |
| `tasks.md` | `specs/<slug>/tasks.md` |

Create a task with `make spec-new`, which generates the branch and the three
artifacts together. `<slug>` must match `NNN-kebab-case` (e.g. `001-user-login`)
and the branch must be `feature/<slug>`. The pre-commit hook verifies that all
three files exist and are filled in.

## Critical rules

- **File line limit**: no file over 1000 lines. Modularize at 800.
- **No scratch files in the repository root**: they belong in `temp/`.
- **Branch naming**: `(feature|fix|hotfix|chore|claude|codex|kiro|test)/<slug>`.
  Direct commits or pushes to `main`, `master` or `develop` are blocked.
- **No hardcoded secrets**: the secret scanner blocks the commit, and it is
  never skipped, not even under an emergency bypass.

## Memory Protocol

This project has persistent memory through Engram. Memory is written by the
harness, not by you: git hooks and agent hooks persist it over Engram's local
HTTP API. You are not responsible for saving it, and you should not assume a
`mem_save` call is what keeps it alive.

**You are responsible for reading it.** Before drafting a plan, changing
architecture, or proposing an approach, search memory for the task slug and for
the components you are about to touch. The project has already decided things,
and re-deciding them is the failure mode this exists to prevent.

Seven classes are tracked per task:

| Class | Where it lives | Written when |
|---|---|---|
| Contextual | Engram session | `make spec-new` |
| Episodic | Session timeline | Automatically |
| Semantic | `spec/<slug>/semantic` | `plan.md` is completed |
| Procedural | `spec/<slug>/procedural` | `tasks.md` is completed |
| Decision | `spec/<slug>/decision` | Every commit |
| Preferences | `user/preferences` | The user states a constraint |
| Outcome | `spec/<slug>/outcome` | Push, CI, or hotfix |

Quotas scale with the branch prefix: `feature/` requires all seven, `fix/` and
`hotfix/` require three (decision, outcome, semantic recorded as `bugfix`), and
`chore/` requires one (decision). The gate runs at push time and blocks.

If the user states a working constraint that should outlive this session, record
it explicitly:

```bash
bash scripts/memory/capture_stage.sh preferences "<the constraint>"
```

## Commands

| Command | Purpose |
|---|---|
| `make spec-new` | Create a feature branch with its spec artifacts |
| `make dev-check` | Run local quality gates before committing |
| `make mem-context` | Show what the project already remembers |
| `make mem-check` | Evaluate the memory quota for this branch |
| `make mem-doctor` | Diagnose the memory subsystem |
| `make test` | Run the test suite |

## Observability evidence layer (mandatory for runtime changes)

- Follow [docs/observability.md](../../docs/observability.md): compare source-of-truth expected
  result, actual response meaning and correlated JSON business-outcome logs. Transport
  success/COMPLETED and configured awslogs never prove correctness or persistence.
- Reuse existing request-ID/logging infrastructure. No PII, customer IDs, tokens, bodies
  or conversational content in logs, evidence or Engram.
- Specs define named happy/sad contract and grounding tests. Keep existing tests,
  coverage and Sonar gates; disclose disabled/skipped gates instead of calling them green.
- Each runtime PR updates safe local `observability.evidence.json`; pre-push/CI run the
  checker. `make observability-check ARTIFACT=<json> STAGE=local` yields LOCAL_ONLY.
- After an approved deployment, obtain real startup/completion CloudWatch receipts
  with exact build, service, environment, request ID and bounded UTC window. Save only
  a sanitized debug diagnosis in Engram; verify by readback and search. Runtime acceptance
  remains open until `STAGE=runtime` passes. Explicit N/A is for libraries without runtime,
  not a waiver of acceptance in affected deployed consumers. Never copy the framework's N/A.
- Agent memory writes require the runtime identity registered by the host. If unavailable
  or unconfirmed, keep memory pending; do not create/select another session or invoke
  write hooks/CLI substitutes. This overrides automated memory capture for agent runs.
