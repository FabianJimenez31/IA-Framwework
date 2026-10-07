# Plan: observability evidence layer

## Architecture

Python standard-library scripts in scripts/observability provide a strict evidence
validator and bounded read-only AWS CLI collector. Existing specs/tests/Sonar remain
authoritative; the new layer consumes evidence rather than restating those gates.

Two stages prevent an impossible pre-deploy CloudWatch requirement: local validates
safe fixtures and business assertions; runtime additionally checks real delivery receipts
and verified Engram references. Neither stage copies request/response bodies into evidence.
Expected outcome and resultCode are contract-defined, non-sensitive codes, not free text.
Source-grounding and contract assertions must come from named tests/reviewer evidence;
the generic checker does not pretend to understand a natural-language answer by itself.

## Changes

- scripts/observability/evidence.py: allowlisted logs, outcome comparison, receipt checks.
- scripts/observability/cloudwatch.py: filter-log-events only; bounded window and pages;
  captured messages never printed on failure. No calls to business endpoints or Engram.
- tests/test_observability.py: test-first offline success/failure and collector coverage.
- docs/observability.md: operator workflow, semantic scenarios, privacy and memory.
- Makefile, agent mirrors, templates, CI: expose the layer and validate it offline.

## Verification

Use unittest/pytest with mocked AWS; run coverage for scripts/observability separately.
Run the original pre-commit checks, shell syntax, documentation mirror checks and diff
secret scan. Live KITT diagnostics are a separate bounded read-only audit, not evidence
that the new standard is already deployed in every service.

## Rollback and delivery

Revert this isolated PR to remove the new layer. No service version, infrastructure,
existing quality threshold or database is changed. Runtime adoption requires reviewed
consumer PRs and deployment evidence. Memory capture awaits confirmed host identity.
