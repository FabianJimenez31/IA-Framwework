"""Collect a bounded, safe CloudWatch receipt. Uses existing AWS CLI credentials."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

try:
    from .evidence import (
        IDENTIFIER,
        VERSION,
        matches,
        require,
        timestamp,
        validate_log,
    )
    from .evidence import (
        request_id as validate_request_id,
    )
except ImportError:  # Direct CLI execution from any working directory.
    from evidence import (
        IDENTIFIER,
        VERSION,
        matches,
        require,
        timestamp,
        validate_log,
    )
    from evidence import (
        request_id as validate_request_id,
    )


def collect(
    log_group,
    region,
    start,
    end,
    service,
    version,
    environment,
    request_id=None,
    event="request.completed",
):
    require(matches(log_group, r"[A-Za-z0-9/_.-]{1,512}"), "Invalid log group")
    require(matches(region, r"[a-z]{2}(?:-[a-z]+)+-\d"), "Invalid AWS region")
    require(
        type(start) is int
        and type(end) is int
        and 0 <= start < end
        and end - start <= 900000,
        "Bound the query to 15 minutes",
    )
    require(
        matches(service, IDENTIFIER) and matches(version, VERSION),
        "Invalid service or version",
    )
    require(
        environment in {"test", "dev", "uat", "uat2", "staging", "prod"},
        "Invalid environment",
    )
    require(event in {"startup", "request.completed"}, "Invalid event selector")
    if event == "request.completed":
        validate_request_id(request_id)
    else:
        require(request_id is None, "Startup has no request ID")
    queried = datetime.now(timezone.utc)
    require(end <= int(queried.timestamp() * 1000), "Query window must have ended")
    clauses = [
        f'$.{key} = "{value}"'
        for key, value in (
            ("service", service),
            ("version", version),
            ("environment", environment),
            ("event", event),
        )
    ]
    if request_id:
        clauses.append(f'$.requestId = "{request_id}"')
    command = [
        "aws",
        "logs",
        "filter-log-events",
        "--log-group-name",
        log_group,
        "--region",
        region,
        "--start-time",
        str(start),
        "--end-time",
        str(end),
        "--filter-pattern",
        "{ " + " && ".join(clauses) + " }",
        "--no-paginate",
        "--no-unmask",
        "--limit",
        "100",
        "--output",
        "json",
        "--no-cli-pager",
    ]
    token, seen_tokens, events = None, set(), []
    for _ in range(20):
        try:
            result = subprocess.run(
                command + (["--next-token", token] if token else []),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            require(
                result.returncode == 0,
                "CloudWatch read failed; check authorized profile and region",
            )
            page = json.loads(result.stdout)
            require(
                isinstance(page, dict) and isinstance(page.get("events"), list),
                "Invalid CloudWatch page",
            )
            for raw in page["events"]:
                require(isinstance(raw, dict), "Invalid CloudWatch event")
                fields = json.loads(raw["message"])
                validate_log(fields)
                require(
                    fields["event"] == event
                    and fields["service"] == service
                    and fields["version"] == version
                    and fields["environment"] == environment,
                    "CloudWatch event identity mismatch",
                )
                if request_id:
                    require(
                        fields.get("requestId") == request_id,
                        "CloudWatch request ID mismatch",
                    )
                require(
                    isinstance(raw.get("eventId"), str)
                    and re.fullmatch(r"[A-Za-z0-9_-]{1,200}", raw["eventId"])
                    is not None,
                    "Invalid CloudWatch event ID",
                )
                require(
                    type(raw.get("timestamp")) is int
                    and start <= raw["timestamp"] <= end,
                    "CloudWatch event outside window",
                )
                require(
                    start <= timestamp(fields["time"]) <= end,
                    "Application timestamp outside window",
                )
                events.append(
                    {
                        "eventId": raw["eventId"],
                        "timestamp": raw["timestamp"],
                        "fields": fields,
                    }
                )
                require(len(events) <= 500, "Too many CloudWatch events")
            token = page.get("nextToken")
            if token is None:
                break
            require(
                isinstance(token, str)
                and 1 <= len(token) <= 2048
                and token not in seen_tokens,
                "Repeated or invalid pagination token",
            )
            seen_tokens.add(token)
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError):
            raise ValueError(
                "CloudWatch receipt unavailable or unsafe; raw messages suppressed"
            ) from None
    else:
        raise ValueError("CloudWatch pagination exceeded the bounded limit")
    require(
        len(events) == 1,
        "Missing or duplicate correlated event; acceptance remains pending",
    )
    return {
        "source": "aws.logs.filter-log-events",
        "region": region,
        "logGroup": log_group,
        "startTimeMs": start,
        "endTimeMs": end,
        "queriedAt": queried.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "events": events,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("log-group", "region", "service", "version", "environment"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--start-time-ms", type=int, required=True)
    parser.add_argument("--end-time-ms", type=int, required=True)
    parser.add_argument(
        "--event", choices=("startup", "request.completed"), default="request.completed"
    )
    parser.add_argument("--request-id")
    args = parser.parse_args(argv)
    try:
        result = collect(
            args.log_group,
            args.region,
            args.start_time_ms,
            args.end_time_ms,
            args.service,
            args.version,
            args.environment,
            args.request_id,
            args.event,
        )
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except (ValueError, TypeError):
        print(
            "CLOUDWATCH_PENDING: no valid safe receipt; do not claim runtime verification",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
