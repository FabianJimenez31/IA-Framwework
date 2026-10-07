"""Strict, content-free observability evidence checks. No network or memory writes."""

import argparse
import json
import math
import re
import sys
import uuid
from datetime import datetime

IDENTIFIER = r"[a-z][a-z0-9-]{0,79}"
VERSION = r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}"
CODE = r"[A-Z][A-Z0-9_]{0,79}"
OUTCOMES = {"success", "degraded", "unavailable", "rejected", "cancelled"}
LEVELS = {"debug", "info", "warn", "error"}
BASE_LOG = {"event", "service", "version", "environment", "time", "level"}
COMPLETION = {
    "requestId",
    "method",
    "route",
    "statusCode",
    "durationMs",
    "outcome",
    "resultCode",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, required, optional=()):
    require(isinstance(value, dict), "Expected an object")
    require(set(value) >= set(required), "Missing required evidence fields")
    require(
        set(value) <= set(required) | set(optional),
        "Unexpected fields; privacy allowlist violated",
    )


def matches(value, pattern):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def timestamp(value):
    require(
        matches(value, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"),
        "Timestamp must be UTC ISO 8601",
    )
    try:
        return int(datetime.fromisoformat(value[:-1] + "+00:00").timestamp() * 1000)
    except (ValueError, OverflowError):
        raise ValueError("Invalid timestamp") from None


def number(value, minimum=0, maximum=10**15):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and minimum <= value <= maximum
    )


def request_id(value):
    # The evidence profile intentionally accepts UUID v4 only. A platform with
    # legacy IDs must agree a bounded non-sensitive profile before adapting it.
    try:
        parsed = uuid.UUID(value)
    except (ValueError, TypeError, AttributeError):
        raise ValueError(
            "requestId must be a UUID v4, never a customer identifier"
        ) from None
    require(
        parsed.version == 4 and str(parsed) == value,
        "requestId must be canonical UUID v4",
    )


def validate_result(result):
    keys(result, {"outcome", "resultCode"})
    require(result["outcome"] in OUTCOMES, "Unknown business outcome")
    require(
        matches(result["resultCode"], CODE), "resultCode must be a safe contract code"
    )


def validate_log(entry):
    require(isinstance(entry, dict), "Log must be a JSON object")
    event = entry.get("event")
    require(event in {"startup", "request.completed"}, "Unexpected log event")
    keys(entry, BASE_LOG | ({"logLevel"} if event == "startup" else COMPLETION))
    require(matches(entry["service"], IDENTIFIER), "Invalid service")
    require(matches(entry["version"], VERSION), "Invalid build version")
    require(
        entry["environment"] in {"test", "dev", "uat", "uat2", "staging", "prod"},
        "Invalid environment",
    )
    require(entry["level"] in LEVELS, "Invalid log level")
    timestamp(entry["time"])
    if event == "startup":
        require(entry["logLevel"] in LEVELS, "Invalid configured log level")
        return
    request_id(entry["requestId"])
    require(
        entry["method"]
        in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "GRPC", "JOB"},
        "Invalid method",
    )
    require(
        matches(entry["route"], r"/[a-z0-9_/:{}.-]{0,199}")
        and ".." not in entry["route"],
        "Use a static route template, never a URL or query string",
    )
    require(
        type(entry["statusCode"]) is int and 100 <= entry["statusCode"] <= 599,
        "Invalid statusCode",
    )
    require(number(entry["durationMs"]), "Invalid durationMs")
    validate_result({k: entry[k] for k in ("outcome", "resultCode")})


def validate_receipt(receipt, expected):
    keys(
        receipt,
        {
            "source",
            "region",
            "logGroup",
            "startTimeMs",
            "endTimeMs",
            "queriedAt",
            "events",
        },
    )
    require(
        receipt["source"] == "aws.logs.filter-log-events",
        "Receipt must come from the read-only collector",
    )
    require(
        matches(receipt["region"], r"[a-z]{2}(?:-[a-z]+)+-\d"), "Invalid AWS region"
    )
    require(
        matches(receipt["logGroup"], r"[A-Za-z0-9/_.-]{1,512}"), "Invalid log group"
    )
    start, end = receipt["startTimeMs"], receipt["endTimeMs"]
    require(
        type(start) is int
        and type(end) is int
        and 0 <= start < end
        and end - start <= 900000,
        "Query window must be bounded to 15 minutes",
    )
    require(
        timestamp(receipt["queriedAt"]) >= end,
        "Receipt queried before the window ended",
    )
    require(
        isinstance(receipt["events"], list) and 1 <= len(receipt["events"]) <= 500,
        "Missing or excessive CloudWatch events",
    )
    seen = set()
    for event in receipt["events"]:
        keys(event, {"eventId", "timestamp", "fields"})
        require(
            matches(event["eventId"], r"[A-Za-z0-9_-]{1,200}")
            and event["eventId"] not in seen,
            "Invalid or duplicate event ID",
        )
        seen.add(event["eventId"])
        require(
            type(event["timestamp"]) is int and start <= event["timestamp"] <= end,
            "Event outside query window",
        )
        validate_log(event["fields"])
        require(
            start <= timestamp(event["fields"]["time"]) <= end,
            "Application timestamp outside query window",
        )
        require(
            event["fields"] == expected,
            "CloudWatch event does not match the observed log",
        )
    # Multiple terminal events are not proof of exactly one result.
    require(len(seen) == 1, "Expected exactly one correlated event")


def validate_memory(memory):
    keys(
        memory,
        {"observationId", "project", "topicKey", "readbackVerified", "searchVerified"},
    )
    require(
        type(memory["observationId"]) is int and memory["observationId"] > 0,
        "Missing Engram observation ID",
    )
    require(matches(memory["project"], IDENTIFIER), "Invalid Engram project")
    require(
        matches(memory["topicKey"], r"[a-z0-9][a-z0-9/_.-]{0,199}"),
        "Invalid stable memory topic",
    )
    require(
        memory["readbackVerified"] is True and memory["searchVerified"] is True,
        "Engram must be checked by readback and search",
    )


def validate_evidence(document, stage):
    require(stage in {"local", "runtime"}, "Unknown evidence stage")
    keys(
        document,
        {
            "schemaVersion",
            "service",
            "version",
            "environment",
            "applicability",
            "startup",
            "startupCloudwatch",
            "scenarios",
            "engram",
        },
        {"reason"},
    )
    require(
        type(document["schemaVersion"]) is int and document["schemaVersion"] == 1,
        "Unknown evidence schema",
    )
    require(
        matches(document["service"], IDENTIFIER)
        and matches(document["version"], VERSION),
        "Invalid service or version",
    )
    require(
        document["environment"] in {"test", "dev", "uat", "uat2", "staging", "prod"},
        "Invalid environment",
    )
    if document["applicability"] == "library_without_runtime":
        require(
            isinstance(document.get("reason"), str)
            and 10 <= len(document["reason"]) <= 200,
            "Explain library N/A and affected consumers",
        )
        require(
            document["startup"] is None
            and document["startupCloudwatch"] is None
            and document["scenarios"] == [],
            "A library must not invent runtime evidence",
        )
        if document["engram"] is not None:
            validate_memory(document["engram"])
        return "NOT_APPLICABLE_LIBRARY"
    require(document["applicability"] == "runtime", "Unknown applicability")
    validate_log(document["startup"])
    require(document["startup"]["event"] == "startup", "Missing startup event")
    for field in ("service", "version", "environment"):
        require(
            document["startup"][field] == document[field], "Startup identity mismatch"
        )
    if document["startupCloudwatch"] is not None or stage == "runtime":
        validate_receipt(document["startupCloudwatch"], document["startup"])
    require(
        isinstance(document["scenarios"], list)
        and 1 <= len(document["scenarios"]) <= 100,
        "Provide named acceptance scenarios",
    )
    seen_names, seen_ids = set(), set()
    for scenario in document["scenarios"]:
        keys(
            scenario,
            {
                "name",
                "expected",
                "response",
                "contractTest",
                "groundingTest",
                "contractPassed",
                "groundingPassed",
                "completion",
                "cloudwatch",
            },
        )
        require(
            matches(scenario["name"], IDENTIFIER)
            and scenario["name"] not in seen_names,
            "Invalid or duplicate scenario",
        )
        seen_names.add(scenario["name"])
        for field in ("contractTest", "groundingTest"):
            require(
                matches(scenario[field], r"[A-Za-z0-9_./-]{1,200}")
                and ".." not in scenario[field],
                "Reference the contract and grounding tests",
            )
        require(
            scenario["contractPassed"] is True and scenario["groundingPassed"] is True,
            "Response contract or source grounding failed",
        )
        validate_result(scenario["expected"])
        validate_result(scenario["response"])
        completion = scenario["completion"]
        validate_log(completion)
        require(completion["event"] == "request.completed", "Missing completion log")
        for field in ("service", "version", "environment"):
            require(
                completion[field] == document[field], "Completion identity mismatch"
            )
        require(
            completion["requestId"] not in seen_ids,
            "Reuse of request ID between independent scenarios",
        )
        seen_ids.add(completion["requestId"])
        require(
            scenario["expected"]
            == scenario["response"]
            == {k: completion[k] for k in ("outcome", "resultCode")},
            "Expected outcome, response and log disagree",
        )
        if scenario["cloudwatch"] is not None or stage == "runtime":
            validate_receipt(scenario["cloudwatch"], completion)
    if document["engram"] is not None or stage == "runtime":
        validate_memory(document["engram"])
    return "RUNTIME_VERIFIED" if stage == "runtime" else "LOCAL_ONLY"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact")
    parser.add_argument("--stage", choices=("local", "runtime"), required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.artifact, encoding="utf-8") as handle:
            document = json.load(handle)
        print(validate_evidence(document, args.stage))
        return 0
    except (ValueError, OSError, TypeError, KeyError):
        # Never echo JSON, AWS errors, response text, values or arbitrary keys.
        print(
            "OBSERVABILITY_FAILED: invalid, incomplete or inconsistent safe evidence",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
