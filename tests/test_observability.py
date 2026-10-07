import copy
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.observability.cloudwatch import collect
from scripts.observability.cloudwatch import main as cloudwatch_main
from scripts.observability.evidence import (
    main as evidence_main,
)
from scripts.observability.evidence import (
    timestamp,
    validate_evidence,
    validate_log,
    validate_receipt,
)

RID = "b16b7879-bbc9-4b27-af3e-3a0a3d74560f"
TIME = "2026-10-07T15:00:00Z"
MS = 1791385200000


def log(event="request.completed"):
    base = {
        "event": event,
        "service": "example-api",
        "version": "abc1234",
        "environment": "uat",
        "time": TIME,
        "level": "info",
    }
    if event == "startup":
        return dict(base, logLevel="info")
    return dict(
        base,
        requestId=RID,
        method="GET",
        route="/wallet",
        statusCode=200,
        durationMs=12,
        outcome="unavailable",
        resultCode="DEPENDENCY_UNAVAILABLE",
    )


def receipt(entry):
    return {
        "source": "aws.logs.filter-log-events",
        "region": "us-east-2",
        "logGroup": "/ecs/example-api",
        "startTimeMs": MS - 1000,
        "endTimeMs": MS + 1000,
        "queriedAt": "2026-10-07T15:00:02Z",
        "events": [{"eventId": "event-123", "timestamp": MS, "fields": entry}],
    }


def evidence():
    result = {"outcome": "unavailable", "resultCode": "DEPENDENCY_UNAVAILABLE"}
    return {
        "schemaVersion": 1,
        "service": "example-api",
        "version": "abc1234",
        "environment": "uat",
        "applicability": "runtime",
        "startup": log("startup"),
        "startupCloudwatch": None,
        "scenarios": [
            {
                "name": "dependency-timeout",
                "expected": result.copy(),
                "response": result.copy(),
                "contractTest": "tests/timeout.spec.ts",
                "groundingTest": "tests/grounding.spec.ts",
                "contractPassed": True,
                "groundingPassed": True,
                "completion": log(),
                "cloudwatch": None,
            }
        ],
        "engram": None,
    }


def runtime_evidence():
    doc = evidence()
    doc["startupCloudwatch"] = receipt(doc["startup"])
    doc["scenarios"][0]["cloudwatch"] = receipt(doc["scenarios"][0]["completion"])
    doc["engram"] = {
        "observationId": 123,
        "project": "example-api",
        "topicKey": "debug/example-api/dependency-timeout",
        "readbackVerified": True,
        "searchVerified": True,
    }
    return doc


class EvidenceTests(unittest.TestCase):
    def test_example_and_agent_mirrors(self):
        self.assertEqual(
            validate_evidence(
                json.loads((ROOT / "examples/observability-local.json").read_text()),
                "local",
            ),
            "LOCAL_ONLY",
        )
        self.assertEqual(
            (ROOT / "AGENTS.md").read_text(), (ROOT / "CLAUDE.md").read_text()
        )
        self.assertEqual(
            (ROOT / "AGENTS.md").read_text(),
            (ROOT / ".specify/templates/constitution-template.md").read_text(),
        )

    def test_optional_memory_and_receipts_checked_even_locally(self):
        self.assertEqual(validate_evidence(runtime_evidence(), "local"), "LOCAL_ONLY")
        doc = evidence()
        doc.update(
            applicability="library_without_runtime",
            startup=None,
            startupCloudwatch=None,
            scenarios=[],
            reason="No process, check consumers.",
            engram=runtime_evidence()["engram"],
        )
        self.assertEqual(validate_evidence(doc, "runtime"), "NOT_APPLICABLE_LIBRARY")

    def test_invalid_iso_and_cli_results(self):
        with self.assertRaises(ValueError):
            timestamp("2026-99-07T15:00:00Z")
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(evidence()))
            with patch("builtins.print"):
                self.assertEqual(evidence_main([str(path), "--stage", "local"]), 0)
                self.assertEqual(evidence_main([str(path), "--stage", "runtime"]), 1)
                self.assertEqual(
                    evidence_main([str(path) + "absent", "--stage", "local"]), 1
                )

    def test_local_and_runtime_are_distinct(self):
        self.assertEqual(validate_evidence(evidence(), "local"), "LOCAL_ONLY")
        self.assertEqual(
            validate_evidence(runtime_evidence(), "runtime"), "RUNTIME_VERIFIED"
        )

    def test_business_mismatch_despite_http_200(self):
        doc = evidence()
        doc["scenarios"][0]["response"]["outcome"] = "success"
        with self.assertRaises(ValueError):
            validate_evidence(doc, "local")

    def test_invalid_evidence_table(self):
        cases = [
            lambda d: d.update(schemaVersion=2),
            lambda d: d.update(unknown="value"),
            lambda d: d.update(scenarios=[]),
            lambda d: d["scenarios"].append(copy.deepcopy(d["scenarios"][0])),
            lambda d: d["scenarios"][0].update(contractPassed=False),
            lambda d: d["scenarios"][0].update(groundingPassed=False),
            lambda d: d["scenarios"][0].update(groundingTest=""),
            lambda d: d["scenarios"][0]["expected"].update(resultCode="wrong"),
            lambda d: d["scenarios"][0]["completion"].update(version="other"),
            lambda d: d["scenarios"][0]["completion"].update(event="startup"),
            lambda d: d["startup"].update(logLevel="invalid"),
            lambda d: d["startup"].update(service="other-api"),
        ]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                doc = evidence()
                mutate(doc)
                with self.assertRaises(ValueError):
                    validate_evidence(doc, "local")

    def test_sensitive_or_malformed_logs_fail(self):
        for field, value in [
            ("customerId", "PRIVATE"),
            ("authorization", "PRIVATE"),
            ("body", "PRIVATE"),
            ("requestId", "PRIVATE"),
            ("time", "bad"),
            ("time", "2026-10-07T15:00:00"),
            ("time", "2026-10-07Z"),
            ("durationMs", -1),
            ("statusCode", True),
            ("route", "/wallet?token=PRIVATE"),
            ("resultCode", "raw text"),
        ]:
            with self.subTest(field=field):
                entry = log()
                entry[field] = value
                with self.assertRaises(ValueError) as error:
                    validate_log(entry)
                self.assertNotIn("PRIVATE", str(error.exception))

    def test_unknown_stage_and_missing_memory_or_cloud_fail(self):
        with self.assertRaises(ValueError):
            validate_evidence(evidence(), "unknown")
        for target in [
            "startupCloudwatch",
            "engram",
            "completion-receipt",
            "readback",
            "search",
        ]:
            doc = runtime_evidence()
            if target == "completion-receipt":
                doc["scenarios"][0]["cloudwatch"] = None
            elif target in ["readback", "search"]:
                doc["engram"][target + "Verified"] = False
            else:
                doc[target] = None
            with self.assertRaises(ValueError):
                validate_evidence(doc, "runtime")

    def test_bad_receipts_fail(self):
        cases = [
            lambda r: r.update(events=[]),
            lambda r: r.update(source="manual"),
            lambda r: r.update(endTimeMs=MS + 9999999),
            lambda r: r.update(queriedAt=TIME),
            lambda r: r["events"][0].update(timestamp=MS + 5000),
            lambda r: r["events"][0]["fields"].update(
                requestId="ceef8b07-96db-47a1-a6d3-c757481a3e44"
            ),
            lambda r: r["events"][0]["fields"].update(version="older"),
            lambda r: r["events"].append(copy.deepcopy(r["events"][0])),
        ]
        for mutate in cases:
            doc = receipt(log())
            mutate(doc)
            with self.assertRaises(ValueError):
                validate_receipt(doc, log())

    def test_library_na_is_explicit(self):
        doc = evidence()
        doc.update(
            applicability="library_without_runtime",
            startup=None,
            startupCloudwatch=None,
            scenarios=[],
            reason="No deployed process; consumer acceptance required.",
        )
        self.assertEqual(validate_evidence(doc, "local"), "NOT_APPLICABLE_LIBRARY")
        doc["reason"] = ""
        with self.assertRaises(ValueError):
            validate_evidence(doc, "local")

    def test_cli_does_not_echo_payload_on_error(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"authorization":"PRIVATE"}')
            run = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/observability/evidence.py"),
                    str(path),
                    "--stage",
                    "local",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(run.returncode, 1)
            self.assertNotIn("PRIVATE", run.stdout + run.stderr)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        clock = patch("scripts.observability.cloudwatch.datetime")
        now = clock.start()
        now.now.return_value = datetime(2026, 10, 7, 15, 0, 2, tzinfo=timezone.utc)
        self.addCleanup(clock.stop)

    def run_collect(self):
        return collect(
            "/ecs/example-api",
            "us-east-2",
            MS - 1000,
            MS + 1000,
            "example-api",
            "abc1234",
            "uat",
            request_id=RID,
        )

    @patch("scripts.observability.cloudwatch.subprocess.run")
    def test_startup_and_cli(self, run):
        run.return_value = subprocess.CompletedProcess(
            [],
            0,
            json.dumps(
                {
                    "events": [
                        {
                            "eventId": "event-123",
                            "timestamp": MS,
                            "message": json.dumps(log("startup")),
                        }
                    ]
                }
            ),
        )
        doc = collect(
            "/ecs/example-api",
            "us-east-2",
            MS - 1000,
            MS + 1000,
            "example-api",
            "abc1234",
            "uat",
            event="startup",
        )
        validate_receipt(doc, log("startup"))
        args = [
            "--log-group",
            "/ecs/example-api",
            "--region",
            "us-east-2",
            "--service",
            "example-api",
            "--version",
            "abc1234",
            "--environment",
            "uat",
            "--event",
            "startup",
            "--start-time-ms",
            str(MS - 1000),
            "--end-time-ms",
            str(MS + 1000),
        ]
        with patch("builtins.print"):
            self.assertEqual(cloudwatch_main(args), 0)
            run.return_value = subprocess.CompletedProcess(
                [], 1, "PRIVATE", stderr="PRIVATE"
            )
            self.assertEqual(cloudwatch_main(args), 1)

    @patch("scripts.observability.cloudwatch.subprocess.run")
    def test_bounded_pagination_and_sensitive_data(self, run):
        run.side_effect = [
            subprocess.CompletedProcess(
                [], 0, json.dumps({"events": [], "nextToken": "repeat"})
            )
        ] * 2
        with self.assertRaises(ValueError):
            self.run_collect()
        run.side_effect = [
            subprocess.CompletedProcess(
                [], 0, json.dumps({"events": [], "nextToken": str(i)})
            )
            for i in range(20)
        ]
        with self.assertRaises(ValueError):
            self.run_collect()
        run.side_effect = None
        for mutate in [
            lambda entry: entry.update(customerId="PRIVATE"),
            lambda entry: entry.update(
                requestId="ceef8b07-96db-47a1-a6d3-c757481a3e44"
            ),
            lambda entry: entry.update(version="older"),
            lambda entry: entry.update(time="2026-10-07T15:01:00Z"),
        ]:
            entry = log()
            mutate(entry)
            run.return_value = subprocess.CompletedProcess(
                [],
                0,
                json.dumps(
                    {
                        "events": [
                            {
                                "eventId": "x",
                                "timestamp": MS,
                                "message": json.dumps(entry),
                            }
                        ]
                    }
                ),
            )
            with self.assertRaises(ValueError) as error:
                self.run_collect()
            self.assertNotIn("PRIVATE", str(error.exception))
        for error in [OSError("PRIVATE"), subprocess.TimeoutExpired("PRIVATE", 30)]:
            run.side_effect = error
            with self.assertRaises(ValueError) as raised:
                self.run_collect()
            self.assertNotIn("PRIVATE", str(raised.exception))

    def test_preflight_rejects_invalid_inputs_without_aws(self):
        with patch("scripts.observability.cloudwatch.subprocess.run") as run:
            for kwargs in [
                {"request_id": "invalid"},
                {"request_id": RID, "event": "startup"},
            ]:
                with self.assertRaises(ValueError):
                    collect(
                        "/ecs/example-api",
                        "us-east-2",
                        MS - 1000,
                        MS + 1000,
                        "example-api",
                        "abc1234",
                        "uat",
                        **kwargs
                    )
            run.assert_not_called()

    def test_direct_cli_paths_are_safe(self):
        for args in [[], ["--request-id", "PRIVATE"]]:
            command = [
                sys.executable,
                str(ROOT / "scripts/observability/cloudwatch.py"),
                "--log-group",
                "/ecs/example-api",
                "--region",
                "us-east-2",
                "--service",
                "example-api",
                "--version",
                "abc1234",
                "--environment",
                "uat",
                "--start-time-ms",
                str(MS - 1000),
                "--end-time-ms",
                str(MS + 1000),
            ] + args
            run = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 1)
            self.assertNotIn("PRIVATE", run.stdout + run.stderr)

    @patch("scripts.observability.cloudwatch.subprocess.run")
    def test_paginated_read_only_collection(self, run):
        run.side_effect = [
            subprocess.CompletedProcess(
                [], 0, json.dumps({"events": [], "nextToken": "page2"})
            ),
            subprocess.CompletedProcess(
                [],
                0,
                json.dumps(
                    {
                        "events": [
                            {
                                "eventId": "event-123",
                                "timestamp": MS,
                                "message": json.dumps(log()),
                            }
                        ]
                    }
                ),
            ),
        ]
        result = self.run_collect()
        self.assertEqual(len(result["events"]), 1)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][:3], ["aws", "logs", "filter-log-events"])
        self.assertIn("--next-token", run.call_args_list[1].args[0])

    @patch("scripts.observability.cloudwatch.subprocess.run")
    def test_failures_do_not_leak_aws_or_messages(self, run):
        for output, status in [
            ("PRIVATE", 1),
            ("PRIVATE", 0),
            (
                json.dumps(
                    {
                        "events": [
                            {"eventId": "x", "timestamp": MS, "message": "PRIVATE"}
                        ]
                    }
                ),
                0,
            ),
            (json.dumps({"events": []}), 0),
        ]:
            run.return_value = subprocess.CompletedProcess(
                [], status, output, stderr="PRIVATE"
            )
            with self.assertRaises(ValueError) as error:
                self.run_collect()
            self.assertNotIn("PRIVATE", str(error.exception))


if __name__ == "__main__":
    unittest.main()
