# Makefile for IA-Framework Quality Gate Harness

.PHONY: init-harness dev-check spec-new test clean help

help:
	@echo "======================================================================"
	@echo "IA-Framework Developer CLI Commands:"
	@echo "======================================================================"
	@echo "  make init-harness   - Install Git hooks and initialize directory structure"
	@echo "  make dev-check       - Run local pre-commit checks (simulate Git hooks)"
	@echo "  make spec-new       - Interactively create a new spec-driven feature branch"
	@echo "  make test           - Execute automated test suite"
	@echo "  make clean          - Run smart cleanup of temporary log and backup files"
	@echo "======================================================================"

init-harness:
	@chmod +x install.sh
	@./install.sh

dev-check:
	@chmod +x .claude/hooks/pre-commit.sh
	@bash .claude/hooks/pre-commit.sh

spec-new:
	@chmod +x .specify/scripts/bash/create-new-feature.sh
	@bash .specify/scripts/bash/create-new-feature.sh

test:
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v; \
	else \
		echo "pytest not installed. Create a virtual environment and run 'pip install pytest'."; \
	fi

clean:
	@chmod +x .claude/hooks/smart-cleanup.sh
	@bash .claude/hooks/smart-cleanup.sh
