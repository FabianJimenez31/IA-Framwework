# Project Constitution (CLAUDE.md / AGENTS.md)

This document guides developers and AI assistants (Claude, GPT, Gemini, etc.) working on this project. It outlines architectural boundaries, core coding guidelines, and strict quality rules.

## 🚨 Critical Rules

- `File Line Limit (1000 lines)`: **Strict Rule**. No single file may exceed 1000 lines. When approaching 800 lines, stop, modularize, and divide functionality. The hook `.claude/hooks/check-file-size.sh` blocks writes that violate this.
- `Zero Temporary Files in Root`: All temporary, scratch, and debug scripts must reside in `temp/` subdirectories. The pre-commit hook blocks any violation of this.
- `Feature Branch Convention`: All development must be done on branches starting with standard prefixes: `(feature|fix|hotfix|chore|claude|test)/[name]`. Direct push/commit to `main`, `master`, or `develop` is strictly blocked.
- `Specification-Driven Development`: Feature branches must have their corresponding design specifications before development. The pre-commit hook verifies that `specs/<slug>/{spec.md,plan.md,tasks.md}` exist and are fully filled out.
- `No Hardcoded Secrets`: Committing api keys, tokens, or credentials will be blocked by secret scanners.
- `One Check, Once`: Every verification runs a single time, in the cheapest place that can catch the problem. Before pushing, run what your change touches (`make lanes` tells you which lanes those are), not the whole suite; CI runs the full suite of each touched lane once. Do not re-run locally what CI is about to run, and do not make CI run lanes the change did not touch.
- `Coverage on New Code (80%)`: The Quality Gate requires 80% coverage on new or modified code. The margin is for lines not worth a test (defensive branches, purely visual changes), never for leaving new logic untested.

## 🧠 Memory Protocol

This project has persistent memory through [Engram](https://github.com/Gentleman-Programming/engram). Memory is written by the **harness**, not by the agent: git hooks and agent hooks persist it over Engram's local HTTP API (`127.0.0.1:7437`). Do not rely on remembering to call `mem_save` — that path is not what keeps this memory alive.

**Reading it is your responsibility.** Before drafting a plan, changing architecture, or proposing an approach, search memory for the task slug and for the components you are about to touch. The project has already decided things; re-deciding them is the failure mode this exists to prevent.

Seven classes are tracked per task:

| Class | Key | Written when |
|---|---|---|
| Contextual | Engram session | `make spec-new` |
| Episodic | Session timeline | Automatically |
| Semantic | `spec/<slug>/semantic` | `plan.md` is completed |
| Procedural | `spec/<slug>/procedural` | `tasks.md` is completed |
| Decision | `spec/<slug>/decision` | Every commit |
| Preferences | `user/preferences` | The user states a constraint |
| Outcome | `spec/<slug>/outcome` | Push, CI, or hotfix |

Quotas scale with the branch prefix: `feature/` requires all seven, `fix/` and `hotfix/` require three (decision, outcome, semantic recorded as `bugfix`), and `chore/` requires one (decision). The gate runs at push time and blocks, exactly like the Spec-Kit Gate.

When the user states a working constraint that should outlive the session, record it explicitly:

```bash
bash scripts/memory/capture_stage.sh preferences "<the constraint>"
```

Inspect memory with `make mem-context`, verify the quota with `make mem-check`, and diagnose the subsystem with `make mem-doctor`.

## 🛤️ CI Lanes

The pipeline validates and deploys only what a change touches. `scripts/harness/ci_lanes.py` classifies the changed files into the lanes declared in `scripts/harness/lanes.json`:

| Change touches | CI runs | Deploy |
|---|---|---|
| Only the frontend lane | Frontend build + tests, Sonar | Frontend only |
| Only the backend lane | Backend tests, Sonar | Backend only |
| Only `tests/` | The lane's tests | Nothing |
| Only docs, specs or agent config | Conventions | Nothing |
| The pipeline itself | Every lane | Nothing |

Rules that keep this safe:

- **Unknown is backend.** A path nobody classified falls into the default lane instead of skipping validation.
- **No diff, everything.** If the diff cannot be computed, every lane runs and deploy uses `--all`.
- **Adapt the config, not the code.** New service or directory → add a lane or a prefix to `lanes.json`.

Check locally with `make lanes`. A deploy job reads the flags with `python3 scripts/harness/ci_lanes.py --mode deploy --base <previous sha> --head <new sha>`.

## 🌐 Modern Web Guidance (projects with a web UI)

Web platform APIs change faster than model training data. When the project has a web frontend, install the [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) skill with `make web-guidance` and consult it **before** writing or changing HTML, CSS or client-side JS (dialogs, forms, tables, accessibility, dark mode, animation, performance). It does not apply to backend, infrastructure, tooling or tests.

- Always call it through `scripts/dev/mwg.sh`: the CLI needs Node >= 22 and the wrapper picks a compatible one without changing the project's pinned version. Telemetry stays off.
- `scripts/dev/mwg.sh search "<2–5 words, one capability>"`, then `scripts/dev/mwg.sh retrieve "<id>"`, then check the code against the guide.
- **Browser support:** Baseline Widely available features need no fallback. Newly available ones are allowed only with the fallback the guide gives or with feature detection and clean degradation. No new polyfill dependencies without approval.
- Close the response with a `### Modern Web Guidance` section naming each guide applied and the non-obvious choice it imposed.

## 🏗️ Architecture Summary

- **`src/`**: Primary application source code.
  - `models/`: Domain schemas and validation models.
  - `services/`: Core business and integration services.
  - `api/`: Controllers, routers, and web application logic.
- **`tests/`**: Unit, integration, and critical path tests.
- **`specs/`**: Feature specifications and implementation plans.
- **`temp/`**: Temporary tools, deployment logs, backups, and scrap files.
- **`scripts/memory/`**: Engram client, task context, stage capture, and the memory gate.

## 🛠️ Developer Workflow

1. **Initialize Feature:** Run `make spec-new` to interactively create a new feature branch and pre-populate specification templates in `specs/<slug>/`.
2. **Design Specifications:** Define requirements in `spec.md` and technical strategy in `plan.md`. Get review before writing code.
3. **Develop & Implement:** Write clean code. Track progress in `tasks.md`.
4. **Local Verification:** Execute `make dev-check` and `make test` to ensure hooks and tests are fully functional.
5. **Push and PR:** Push branch, open Pull Request, ensure CI quality gates are fully green, merge, and clean up.

## ⏩ Operations & Emergency Procedures

- **Database-Code Enum Sincronización:** Run `make validate-enums` to verify that real database records are fully aligned with raw code Enum specifications before merging.
- **Nginx Config Sanity Gate:** Run `make lint-nginx` to check active configurations and prevent localhost upstream networking bugs in routing layers.
- **Frontend SPA Deploy Smoke Tester:** Run `make smoke-test` after deployment to ensure that all endpoints are live, bundles are responsive, and chunk versions are atomic (no partial deploys).
- **Incident & Emergency Hotfixes:** In production crises, declare structured hotfixes with `make hotfix`. It automatically generates documentation templates in `temp/emergency_logs/`, captures safety state snapshots in `temp/backup/`, and arms the emergency bypass.
- **Emergency Bypass Scope:** The bypass is persisted to `temp/.harness_emergency` with a 2-hour TTL (override with `HARNESS_EMERGENCY_TTL`), or forced ad hoc with `HARNESS_EMERGENCY=1` in the environment. It suspends **workflow gates only** — protected-branch blocks, branch naming, the Spec-Kit Gate, root-scratch-file checks, the architecture validator and the test suite. **Safety gates stay enforced**: hardcoded-secret scanning and the file-size limits are never skipped. An incident is a reason to skip process, never a reason to leak a credential. Re-arm every gate with `make emergency-clear`.
- **Atomic Rollback & Recovery:** Revert broken changes with `make rollback`. It lists git safety tags and workspace patches. Run `scripts/deployment/rollback.sh apply <target>` to safely restore workspace state.
