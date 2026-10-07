# Feature: observability evidence layer

Branch: feature/010-observability-evidence. Created: 2026-10-07.

## Requirements

Add a reusable layer to the existing framework, not a second tests/specs/Sonar process.
For runtime changes, correlate expected business outcome, observed response and safe
structured logs. HTTP 200, SSE completed, a green pipeline or an awslogs configuration
alone must never prove business correctness or delivery to CloudWatch.

## Acceptance scenarios

- Local: contract and source-grounding assertions pass; response and completion log
  agree with the expected outcome and result code. CloudWatch/Engram can be pending,
  but the command explicitly reports LOCAL_ONLY, never runtime verified.
- Runtime: query CloudWatch read-only for the exact service, version and request ID;
  require startup and completion event receipts within bounded UTC windows. Require
  a saved Engram reference verified by readback and search before closing acceptance.
- Sad paths: wrong version/ID, missing event, stale receipt, malformed JSON, sensitive
  extra fields, false grounding assertion and transport-success/business-failure mismatch
  fail closed. Unknown schema fields and unknown stages fail.
- Libraries without a deployed process declare explicit N/A and verify changed logging
  behavior in affected deployed consumers; they do not invent CloudWatch receipts.
- No automated UAT business requests, database access, infrastructure mutation or Engram
  writes. CloudWatch is read-only and uses existing operator credentials. CI mocks AWS.
- Memory unavailable or runtime identity unconfirmed stays pending, without selecting,
  inventing or starting a replacement agent session.

## Non-goals

No bulk microservice retrofit, merge/deploy, new auth contract, body logging, automatic
LLM judgement, cloud credentials in CI, or change to existing coverage/Sonar thresholds.

## Success criteria

Tests exercise both positive and negative evidence checks, collector pagination and
safe errors. Agent constitutions, Spec-Kit templates, PR template and CLI point to the
new workflow. KITT adoption is governed separately through its control plane.
