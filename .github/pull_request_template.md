## Change and existing quality framework

- Spec/plan/tasks:
- Tests and coverage evidence:
- Sonar/CI result (disclose disabled/skipped gates):

## Observability layer

- [ ] Reuses request ID propagation; safe JSON startup/terminal business logs.
- [ ] Named happy/sad contract and source-grounding tests compare response meaning to logs.
- [ ] No PII, customer IDs, tokens, bodies, raw errors or conversation content in logs/evidence.
- [ ] Local artifact checked (`LOCAL_ONLY`), or reviewed non-impact/library N/A rationale.
- Post-deploy owner and acceptance task:
- CloudWatch startup/completion receipts: pending / verified (group, UTC window, build).
- Engram diagnosis: pending / verified (project, topic, observation, readback/search).

Do not mark runtime acceptance done from tests, awslogs config or HTTP 200 alone.
No sensitive artifacts in Git. See [the observability layer](../docs/observability.md).
