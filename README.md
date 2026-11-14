# IA-Framework: Spec-Kit & Quality Gate Harness

**IA-Framework** is a turnkey boilerplate that implements a professional, rigorous, and automated development workflow. It combines **Specification-Driven Development (Spec-Kit)** with strict **Quality Gate Harnesses** (Git Hooks + GitHub Actions CI) to enforce high-quality standards and protect codebases from agent drift, code bloat, and regression.

Perfect for modern engineering teams and developers paired with AI coding assistants (Claude Code, GPT, Gemini, etc.).

---

## 🚀 Key Features

*   **Specification-Driven Development (Spec-Kit):** Enforces that coding *only* begins after requirements, technical strategy, and task checklists are explicitly defined and placed in `specs/<slug>/`.
*   **AI Code Safeguards:** Blocks AI assistants from writing bloated code by enforcing a strict **1000-line limit** per single source file (warns at 800 lines).
*   **Strict Local Git Hooks:**
    *   Hard-blocks direct commits or pushes to protected branches (`main`, `master`, `develop`, etc.).
    *   Validates Git Flow branch naming conventions (`feature/`, `fix/`, `hotfix/`, `chore/`).
    *   Scans diffs for hardcoded secrets, api keys, and private tokens.
    *   Forces cleanup of temporary Python/shell scripts in the repository root.
*   **Lane-Based CI/CD Quality Gates:** GitHub Actions workflows that validate and deploy only what a change touches. A frontend-only change does not run the backend suite or restart the backend; a docs-only change deploys nothing. Lanes are declared in one JSON file.
*   **Modern Web Guidance for Agents:** One command installs Google Chrome's up-to-date web platform guidance as an agent skill, with a wrapper that handles its Node requirement.
*   **Advanced Operations & Harness Suite:**
    *   **Nginx Upstream Linter:** Blocks IPv6 connection lottery hazards in proxy/upstream routing configurations (localhost loops).
    *   **Frontend SPA Smoke Tester:** Guarantees atomic deployment states, ensuring that all SPA routes are up and reference identical static bundle versions.
    *   **Database-Enum Integrity Checker:** Performs set checks between code Enums and raw database distinct records to avoid runtime data degradation.
    *   **Structured Incident & Hotfix Pipelines:** Standardizes emergency responses with automated backups, local testing gates, rollback tags, and incident documentation logs.
*   **Developer CLI API & Pre-Commit Config:** A clean `Makefile` and `.pre-commit-config.yaml` providing standard endpoints for all local quality gates and workflow tasks.

---

## 📁 Directory Structure

```text
.
├── .specify/                         # 🛠️ Spec-Kit templates & CLI scripts
│   ├── templates/                    # Markdown templates (Spec, Plan, Tasks)
│   └── scripts/bash/                 # Automation scripts for branches/validation
├── .claude/                          # 🤖 AI Agent Safeguards & Git Hooks
│   └── hooks/                        # Pre/Post hooks & hook wrappers
├── .github/workflows/                # 🔗 CI/CD pipeline quality gates
├── scripts/                          # ⏩ Custom project-specific validation & ops
│   ├── validation/                   # Architecture & Database-enum consistency validators
│   ├── harness/                      # CI lane classifier, web server & deployment smoke checkers
│   ├── dev/                          # Developer tooling (Modern Web Guidance wrapper)
│   └── deployment/                   # Standard emergency hotfix & rollback scripts
├── temp/                             # 📂 Organized playground for scrap/logs
├── .pre-commit-config.yaml          # 🔗 Git pre-commit framework config
├── Makefile                          # Unified CLI commands for developers
├── install.sh                        # One-click interactive installer
├── CLAUDE.md                         # Reference project constitution for AI
├── AGENTS.md                         # Reference mirror for other AI assistants
└── README.md                         # This file
```

---

## ⚡ Quick Start & Installation

To integrate **IA-Framework** into any existing or new project:

1.  **Clone or Copy** the framework files into the root of your project repository.
2.  Run the **One-click Installer**:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
    This script will:
    *   Initialize Git (if not already done).
    *   Establish folders (`specs/`, `temp/`, `src/`, `tests/`, `scripts/`).
    *   Automatically bind local Git hooks to `.claude/hooks/git` using Git `core.hooksPath`.
    *   Populate the `.gitignore` with standard rules.
    *   Generate your `CLAUDE.md` and `AGENTS.md` constitution guidelines.

3.  Verify the installation:
    ```bash
    make help
    ```

---

## 🛠️ Developer Workflow

The framework implements a highly reliable TDD-like cycle powered by specifications:

### 1. Initialize a Feature
Run the following command to interactively create a new feature branch and pre-populate specification templates:
```bash
make spec-new
```
*   *Prompt example:* `001-user-login`
*   *Result:* Creates branch `feature/001-user-login` and initializes files:
    *   `specs/001-user-login/spec.md` (Product/Business specifications)
    *   `specs/001-user-login/plan.md` (Technical implementation plan)
    *   `specs/001-user-login/tasks.md` (Checklist to track implementation progress)

### 2. Design Phase
Document your business requirements in `spec.md`, design your architecture and dependencies in `plan.md`, and outline tasks in `tasks.md`.

### 3. Development Phase
Implement the code (e.g. in `src/`). Track progress by updating the `[ ]`, `[/]`, and `[x]` states inside `tasks.md`.

### 4. Local Validation Gate
Before committing, verify that your changes pass all local hooks:
```bash
make dev-check
```
*   This will check branch naming, verify that spec files exist, scan for secrets, run the Python architecture anti-pattern scanner, and block files that exceed 1000 lines.

### 5. Push & Pull Request
Push your branch and open a Pull Request. The **CI Quality Gate** will automatically run remote checks. Once green, merge to `main` and enjoy clean, high-quality code!

---

## 🧠 Persistent Memory (Engram)

The framework governs *how* software is built. Memory is what keeps *what was learned* from evaporating when a session ends — the decisions taken, the approaches discarded, and whether any of it worked.

Memory is backed by [Engram](https://github.com/Gentleman-Programming/engram) (a single Go binary with SQLite + FTS5) and is **mandatory**: `install.sh` installs it and aborts if it cannot.

### It is written by the harness, not by the agent

Engram is normally driven over MCP, where the agent calls `mem_save` when it remembers to. That cannot be guaranteed and does not survive context compaction. This framework instead writes through Engram's **local HTTP API** from the same git hooks that already block bad commits. The agent reads memory; it is never responsible for saving it.

### Seven classes per task

| Class | Key | Written when |
|---|---|---|
| Contextual | Engram session | `make spec-new` |
| Episodic | Session timeline | Automatically |
| Semantic | `spec/<slug>/semantic` | `plan.md` is completed |
| Procedural | `spec/<slug>/procedural` | `tasks.md` is completed |
| Decision | `spec/<slug>/decision` | Every commit |
| Preferences | `user/preferences` | The user states a constraint |
| Outcome | `spec/<slug>/outcome` | Push, CI, or hotfix |

Five of the seven are by-products of artifacts the framework already demands — the slug, `plan.md`, `tasks.md`, the commit message and the test result. Nothing new is asked of the developer.

### Quotas scale with the branch prefix

| Prefix | Required |
|---|---|
| `feature/` | All seven |
| `fix/`, `hotfix/` | Three — decision, outcome, semantic recorded as `bugfix` |
| `chore/` | One — decision |
| `test/`, `claude/`, `codex/`, `kiro/` | Session only |

Demanding seven classes from a one-line chore produces ritual filling, and memory filled as a ritual is worse than none: it pollutes future searches with noise that looks like signal.

The gate runs at push time and blocks, exactly like the Spec-Kit Gate. `pre-commit` is deliberately left untouched, so a memory failure can never block a commit through a path you cannot disable.

### Commands

| Command | Purpose |
|---|---|
| `make mem-context` | Show what the project already remembers |
| `make mem-check` | Verify the quota for the current branch (`STAGE=merge` to override) |
| `make mem-capture` | Capture every state derivable from the working tree |
| `make mem-doctor` | Diagnose the memory subsystem |
| `make mem-ingest ARTIFACT=<path>` | Fold a CI outcome artifact into local memory |

### Agents

`install.sh` configures **Claude Code**, **Codex** and **Kiro**. Project-level surfaces are versioned in the repository (`.claude/settings.json`, `AGENTS.md`, `.kiro/steering/`, `.kiro/settings/mcp.json`); machine-level MCP registration is delegated to `engram setup <agent>`.

> **Kiro note:** the steering file instructs Kiro to use this project's `specs/<slug>/` layout instead of generating its own. Kiro's default artifacts collide with the framework's — `tasks.md` is the same filename in both.

### CI

GitHub Actions runners have no Engram store and cannot reach the daemon, which binds to `127.0.0.1`. The CI Quality Gate emits its result as a `ci-outcome` artifact; download it and run `make mem-ingest ARTIFACT=<path>` to fold it into the outcome state.

---

## ⏩ Operations & Emergency Procedures

IA-Framework comes preloaded with production-tested developer operations scripts.

### 📊 Database-Code Enum Validation
To check database record consistency vs. code Enum classes, run:
```bash
make validate-enums
```
This runs `scripts/validation/validate_enums.py`, which computes exact set differences and suggests updates before discrepancies cause validation crashes.

### 🌐 Nginx Config Upstream Linter
To verify active Nginx sites and prevent the IPv6/IPv4 localhost connection lottery bug, run:
```bash
make lint-nginx
```
This runs `scripts/harness/lint_nginx.sh` to parse configs and enforce explicit IP targets (`127.0.0.1`).

### 📦 Frontend SPA Smoke Testing
To run an automated post-deploy smoke test checking route status and JS chunk versions compatibility (atomic checks), run:
```bash
make smoke-test
```
This runs `scripts/harness/smoke_test_frontend.sh`. You can configure it by setting environment variables:
```bash
BASE_URL=https://myprodapp.com ROUTES="/ /dashboard /admin" make smoke-test
```

### 🚨 Structured Production Emergency Hotfix
When production is down and normal staging review stages must be bypassed, run:
```bash
make hotfix
```
This will run the interactive hotfix initializer `scripts/deployment/emergency_hotfix.sh crear`:
1.  **Safety Snapshots:** Saves dirty changes into `temp/backup/`.
2.  **Incident Documentation:** Creates a post-mortem Markdown template in `temp/emergency_logs/` so that fixes are documented.
3.  **Emergency Validation:** Run `scripts/deployment/emergency_hotfix.sh validar` to run local tests.
4.  **Bypass Action:** Run `scripts/deployment/emergency_hotfix.sh aplicar` to commit/push the fix under the emergency bypass. The bypass is written to `temp/.harness_emergency` with a 2-hour TTL so the git hooks — which run as separate processes — actually observe it. It suspends workflow gates only; secret scanning and file-size limits remain enforced.
5.  **Re-arm:** Run `make emergency-clear` once the incident is closed to restore every quality gate.

### ⏪ Atomic Local & Git Rollback
If a hotfix or deploy causes unforeseen regressions, run:
```bash
make rollback
```
This runs `scripts/deployment/rollback.sh list` to display all git rollback safety tags and local snapshots.
To apply a rollback, execute:
```bash
./scripts/deployment/rollback.sh apply <tag_or_patch_file>
```
This safely reverts files while capturing a safety backup of your current state.

---

## 🛤️ Lane-Based CI

A pipeline that runs everything on every change gets slow, and a slow pipeline gets bypassed. This one runs each check once, only where it applies.

`scripts/harness/ci_lanes.py` reads the changed files and the lanes declared in `scripts/harness/lanes.json`, and each CI job runs only if its lane is active:

| Change touches | CI runs | Deploy flags |
|---|---|---|
| `frontend/` | Frontend build + tests, Sonar | `--frontend` |
| `src/` or anything unclassified | Backend tests, Sonar | `--backend` |
| Only `tests/` | The lane's tests | none |
| Only docs, specs, agent config | Conventions | none |
| The workflow or the lane config | Every lane | none |

Three defaults keep it safe: an unclassified path falls into the default lane, a change to the pipeline itself runs every lane, and when the diff cannot be computed everything runs and deploy falls back to `--all`.

```bash
make lanes                 # which lanes does my branch touch?
make lanes BASE=origin/develop
```

### Adapting the lanes

Edit `scripts/harness/lanes.json`. Each lane has a `name`, the path prefixes that belong to it, and the flags your deploy script takes for it. Mark one lane as `default` to catch unclassified paths. Add a job to `.github/workflows/ci-quality-gate.yml` with `if: needs.changes.outputs.<lane> == 'true'` for each new lane.

### Deploying by lane

The framework ships no deploy job, because deployment is project-specific. In yours, compute the flags from the pushed range and pass them to your script:

```yaml
- id: lanes
  run: >-
    python3 scripts/harness/ci_lanes.py --mode deploy
    --base "${{ github.event.before }}" --head "${{ github.sha }}"
- if: steps.lanes.outputs.flags != ''
  run: ./deploy.sh ${{ steps.lanes.outputs.flags }}
```

### Test efficiency

*   **One check, once.** Locally, run what you touched. In CI, the full suite of each touched lane runs a single time and also produces the coverage report.
*   **Coverage on new code: 80%.** The reference gate is in `infra/sonarqube/quality-gate.json`. It evaluates new code only; apply it in your SonarQube server.
*   **Tests never deploy.** A change under `tests/` is validated but restarts nothing.

---

## 🌐 Modern Web Guidance

For projects with a web UI. Models learn the web as it was at training time; [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) gives agents current practice for dialogs, forms, tables, accessibility, dark mode, animation and performance.

```bash
make web-guidance                                   # install the skill for your agents
scripts/dev/mwg.sh search "light dismiss dialog"    # find a guide
scripts/dev/mwg.sh retrieve "dialog"                # read it
scripts/dev/mwg.sh legacy-scan frontend/src --json  # find legacy patterns
```

The CLI requires Node 22 or newer. `scripts/dev/mwg.sh` picks a compatible Node (the active one, or the newest installed through nvm) without touching the version your project pins, and keeps the CLI's telemetry off. The usage rules for agents are in `CLAUDE.md` / `AGENTS.md`.

---

## 📊 SonarQube Quality Gate

**IA-Framework** features a robust out-of-the-box **SonarQube Quality Gate** integration to measure bugs, code smells, vulnerabilities, security hotspots, and unit test coverage in both local and remote environments.

### 🛡️ Remote Quality Gate (CI)
On Pull Request creation, the CI action `.github/workflows/ci-quality-gate.yml` will automatically trigger a SonarQube Scanner scan. It enforces remote verification of the Quality Gate, blocking PR merges if the status is red (using secret values `SONAR_HOST_URL` and `SONAR_TOKEN`).

### 💻 Local Quality Gate (Developer Sandbox)
You do not need to wait for remote CI/CD pipelines to know if your changes will pass the SonarQube Quality Gate. Run the local gate command:
```bash
make sonar-check
```
This command runs:
1.  **Test Coverage Collection:** Executes tests generating `coverage.xml`.
2.  **Local Sonar Scan:** Triggers a Dockerized `sonar-scanner-cli` to analyze source files and publish metrics locally or to a shared SonarQube server.
3.  **Project Status API Poll:** Queries the SonarQube project status API to check if it's `OK` or `ERROR`.
4.  **Error Diagnostics:** Prints a colorized report displaying failed conditions, code issues, severity, and files with uncovered code.

To customize Sonar scanner properties (e.g. project name, file inclusions/exclusions, source path), edit `sonar-project.properties` in your repository root.

---

## 📄 License

This framework is open-source software licensed under the [MIT License](LICENSE).
