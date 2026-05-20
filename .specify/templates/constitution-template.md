# Project Constitution (CLAUDE.md / AGENTS.md)

This document guides developers and AI assistants (Claude, GPT, Gemini, etc.) working on this project. It outlines architectural boundaries, core coding guidelines, and strict quality rules.

## 🚨 Critical Rules

- `File Line Limit (1000 lines)`: **Strict Rule**. No single file may exceed 1000 lines. When approaching 800 lines, stop, modularize, and divide functionality. The hook `.claude/hooks/check-file-size.sh` blocks writes that violate this.
- `Zero Temporary Files in Root`: All temporary, scratch, and debug scripts must reside in `temp/` subdirectories. The pre-commit hook blocks any violation of this.
- `Feature Branch Convention`: All development must be done on branches starting with standard prefixes: `(feature|fix|hotfix|chore|claude|test)/[name]`. Direct push/commit to `main`, `master`, or `develop` is strictly blocked.
- `Specification-Driven Development`: Feature branches must have their corresponding design specifications before development. The pre-commit hook verifies that `specs/<slug>/{spec.md,plan.md,tasks.md}` exist and are fully filled out.
- `No Hardcoded Secrets`: Committing api keys, tokens, or credentials will be blocked by secret scanners.

## 🏗️ Architecture Summary

- **`src/`**: Primary application source code.
  - `models/`: Domain schemas and validation models.
  - `services/`: Core business and integration services.
  - `api/`: Controllers, routers, and web application logic.
- **`tests/`**: Unit, integration, and critical path tests.
- **`specs/`**: Feature specifications and implementation plans.
- **`temp/`**: Temporary tools, deployment logs, backups, and scrap files.

## 🛠️ Developer Workflow

1. **Initialize Feature:** Run `make spec-new` to interactively create a new feature branch and pre-populate specification templates in `specs/<slug>/`.
2. **Design Specifications:** Define requirements in `spec.md` and technical strategy in `plan.md`. Get review before writing code.
3. **Develop & Implement:** Write clean code. Track progress in `tasks.md`.
4. **Local Verification:** Execute `make dev-check` and `make test` to ensure hooks and tests are fully functional.
5. **Push and PR:** Push branch, open Pull Request, ensure CI quality gates are fully green, merge, and clean up.
