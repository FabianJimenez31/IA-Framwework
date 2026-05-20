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
*   **Boilerplate CI/CD Quality Gates:** Generic GitHub Actions workflows to validate file sizes, branch naming, and run automated test suites on every Pull Request.
*   **Developer CLI API:** A clean `Makefile` providing standard endpoints for all workflow tasks.

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
├── temp/                             # 📂 Organized playground for scrap/logs
├── Makefile                          # Unified CLI commands for developers
├── install.sh                        # One-click interactive installer
├── CLAUDE.md                         # Reference project constitution for AI
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
    *   Establish folders (`specs/`, `temp/`, `src/`, `tests/`).
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
*   This will check branch naming, verify that spec files exist, scan for secrets, and block files that exceed 1000 lines.

### 5. Push & Pull Request
Push your branch and open a Pull Request. The **CI Quality Gate** will automatically run remote checks. Once green, merge to `main` and enjoy clean, high-quality code!

---

## 📄 License

This framework is open-source software licensed under the [MIT License](LICENSE).
