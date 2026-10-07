# Layer: logs, response meaning, CloudWatch and debug memory

This layer extends the existing specs/tests/coverage/Sonar framework. It does not replace
any quality gate and does not claim that installing the framework retrofits deployed services.

## Required workflow for every affected runtime change

1. Read Engram context/search and the project's canonical specs/contracts before coding.
2. Define happy and sad scenarios, the source of truth and expected business result in the
   spec. For each scenario name the contract test and source-grounding test. A `.spec.ts`
   is a test, not a substitute for the feature's spec/plan/tasks.
3. Reuse existing request-ID middleware and logger. Validate the incoming ID according
   to the agreed safe platform profile; generate UUID v4 if absent/invalid. Propagate to
   downstream HTTP/gRPC/jobs and return on errors too. Never use it for authentication.
4. Test response meaning against the actual governed source and the correlated logs.
   Contract and grounding assertions must be computed by tests or explicitly verified
   by a reviewer, not set to true just to satisfy the evidence schema.
5. Before deployment, run `make observability-check ARTIFACT=<safe-json> STAGE=local`.
   Its success is **LOCAL_ONLY**. It does not prove CloudWatch delivery or a deployed fix.
6. After approved deployment, use existing authorized AWS credentials to query actual
   CloudWatch events. Capture startup near task start and completion near the test request,
   using separate UTC windows of at most 15 minutes. Record service, deployed version,
   environment, opaque request ID and event IDs. Retry boundedly for ingestion delay;
   missing data, forbidden IAM access or a timeout stays pending, never silently green.
7. Save a sanitized diagnosis to Engram with a stable `debug/<service>/<slug>` topic.
   Verify returned observation by readback and search. Then attach its reference to the
   evidence and run `STAGE=runtime`. A saved file or a successful HTTP write without
   readback/search is not proof of searchable memory.

## What “the response makes sense” means

Compare **expected source result → observed response → recorded business outcome**.
Transport status alone is not a business result: HTTP 200/SSE completed can contain an
unavailable capability, a dependency failure or a fallback.

Examples to turn into contract/grounding tests without copying customer data:

- A failed balance lookup must not become a fabricated balance or a request for unnecessary
  account data. Owner, amount, currency and formatting are checked inside the test; logs
  only contain `outcome=unavailable` and a non-sensitive result code.
- A today's-only vehicle restriction tool cannot substantiate tomorrow or Saturday.
  Log the unsupported scope, not a claimed success or vehicle plate.
- A dependency timeout followed by an approved fallback records `degraded`, not plain
  success. Correlated dependency/fallback events retain only safe codes and timing.
- An asynchronous stream/job records its **terminal business outcome**, including cancel,
  rather than treating socket opening or acknowledgement as success.

The generic checker compares outcome/code and checks contract/grounding attestations.
It is **not an automatic natural-language truth detector**. Tests, source evidence and
review remain necessary, including cases where a plausible answer contradicts the source.

## JSON log profile v1

Common fields: `time` (UTC ISO 8601 ending Z), `level`, `event`, `service`, real build
`version`, `environment`.

- `startup`: adds effective `logLevel`. Emit once per process; never dump the environment.
- `request.completed`: adds `requestId`, `method`, static `route` template, `statusCode`,
  `durationMs`, `outcome`, `resultCode`. Supported outcomes: success, degraded, unavailable,
  rejected, cancelled. Result codes are non-sensitive UPPER_SNAKE_CASE contract constants.
- Additional safe dependency/tool/fallback milestones can be logged with the same ID;
  the evidence collector deliberately selects only startup or terminal completion.
  The terminal code must reflect those failures. A service adapter must test this mapping.

Keep canonical field names/meaning across runtimes; adapters may map existing event
names before adopting v1. The collector expects v1 natively in CloudWatch; it does not
silently reinterpret old logs as compliant. This evidence profile accepts UUID v4 only;
agree an explicit bounded legacy profile before changing that policy.

Use an allowlist, not arbitrary `...request`, `...config`, headers or error objects.
Exclude customer/account/vehicle identifiers, messages, bodies, tokens, cookies, URLs
with query parameters, addresses, coordinates, raw stack messages and tool arguments.
Routes and result codes are static contract metadata, not transformed customer content.
Evidence metadata still requires review; a regex is not a universal PII detector.

## Commands and evidence

```bash
make observability-test
make observability-check ARTIFACT=temp/testing/observability.json STAGE=local

# Credentials are supplied by the existing authorized operator profile, never this repo.
AWS_PROFILE=<authorized-profile> python3 scripts/observability/cloudwatch.py \
  --log-group /ecs/example-api --region us-east-2 \
  --service example-api --version <deployed-build> --environment uat \
  --request-id <uuid-v4> --start-time-ms <utc-start-ms> --end-time-ms <utc-end-ms> \
  > temp/testing/completion-receipt.json

# Startup uses its own bounded window and has no request ID.
python3 scripts/observability/cloudwatch.py \
  --log-group /ecs/example-api --region us-east-2 \
  --service example-api --version <deployed-build> --environment uat --event startup \
  --start-time-ms <startup-window-start> --end-time-ms <startup-window-end> \
  > temp/testing/startup-receipt.json

make observability-check ARTIFACT=temp/testing/observability.json STAGE=runtime
```

Start with [the synthetic example](../examples/observability-local.json). Top-level:
schemaVersion=1, service/version/environment, applicability=runtime, startup,
startupCloudwatch (receipt or null), scenarios, engram (verified reference or null).
Each scenario references named contract and grounding tests and contains expected and
observed response **codes**, their passed assertions, completion log and CloudWatch receipt.
Insert collector receipts directly; don't edit/create event IDs or reuse unrelated receipts.

Runtime requires startup and each completion receipt to exactly match observed logs,
identity and window. Receipts record `aws.logs.filter-log-events`, region, group,
query time/window, AWS eventId/timestamp and allowlisted fields. They are operator
evidence, **not cryptographic attestation**; reviewer verifies account/profile, deployed
build and original CloudWatch events. AWS receipt files stay in ignored temp/testing.

Read-only collector: filter-log-events only, no unmasking, no infrastructure changes,
no business requests. Pagination follows empty pages until no token, max 20 calls / 500
events, 30s per call. Missing/malformed/unsafe data fails without printing raw messages.
If there are multiple processes/startup events, narrow the window to the tested process.

## Engram memory, not a second log warehouse

Store a compact **What / Why / Where / Learned** diagnosis: service/environment/build,
scenario, expected versus observed outcome codes, cause/fix, PR/commit, CloudWatch
group/window/event references, test results, blockers and next steps. Never copy full
logs, request/response bodies, transcripts or source payloads. Raw sensitive acceptance
data stays in its governed system with access/retention controls, not Engram or Git.

Evidence reference: `observationId` (positive integer), `project`, stable `topicKey`,
`readbackVerified=true`, `searchVerified=true`. These attestations are completed only
after the MCP readback/search succeeds. Search by service, incident slug and error code
at the beginning of the next task; update the same topic when that diagnosis evolves.
Cloud replica verification is reported separately; don't claim team sync from a local save.

**Agent identity safety:** use only the runtime session registered by the host. If identity
is absent/unconfirmed after startup/compaction, do not invent/select/start a session, use
another session, invoke write hooks, or substitute CLI writes. Keep memory pending and
report the limitation. This rule takes precedence over automatic capture instructions
for agent-driven runs. The new collector and checker never write to Engram.

## Adoption and acceptance boundaries

- CI runs offline tests/fixtures, never UAT databases, production dependencies or live
  CloudWatch queries. Runtime evidence is an explicit **post-deploy acceptance gate**,
  not an impossible pre-merge requirement for an undeployed change.
- Existing Sonar/coverage/spec gates remain required. Disabled/skipped gates are disclosed,
  not presented as passed. Do not disable them to adopt this layer.
- Every runtime PR supplies local evidence or an explicit reviewed non-impact rationale.
  If it changes behavior, add successful and failed/degraded journeys. Post-deploy work
  stays open until runtime evidence and Engram are checked; local tests cannot close it.
- A library without a process declares applicability=`library_without_runtime`, a reason,
  null startup/receipts and empty scenarios. The checker reports **NOT_APPLICABLE_LIBRARY**,
  never runtime verified. Logging changes require acceptance in affected consumers.
- An emergency may defer runtime acceptance with owner/next step, never privacy checks,
  missing evidence reporting or honest status. There is no “success by bypass” here.

References: [AWS FilterLogEvents](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html),
[OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).
