import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.harness import ci_lanes
from scripts.harness.ci_lanes import ZERO_SHA

pytestmark = pytest.mark.unit

CONFIG = ci_lanes.load_config()


@pytest.mark.parametrize(
    ("path", "lane"),
    [
        ("frontend/src/App.tsx", "frontend"),
        ("frontend/package-lock.json", "frontend"),
        ("src/services/orders.py", "backend"),
        ("tests/services/test_orders.py", "backend"),
        ("requirements.txt", "backend"),
        ("unclassified.cfg", "backend"),
        ("docs/architecture.md", None),
        ("specs/004-ci-lanes/spec.md", None),
        (".claude/hooks/pre-commit.sh", None),
        (".github/workflows/spec-compliance.yml", None),
        ("README.md", None),
        ("LICENSE", None),
        (".github/workflows/ci-quality-gate.yml", None),
        ("scripts/harness/lanes.json", None),
    ],
)
def test_lane_for_classifies_each_path(path: str, lane: str | None) -> None:
    assert ci_lanes.lane_for(path, CONFIG) == lane


def test_markdown_outside_the_root_is_not_neutral() -> None:
    assert ci_lanes.lane_for("src/prompts/system.md", CONFIG) == "backend"


def test_frontend_only_change_runs_and_deploys_only_frontend() -> None:
    files = ["frontend/src/index.css", "docs/theme.md"]

    assert ci_lanes.ci_lanes(files, CONFIG) == ("frontend",)
    assert ci_lanes.deploy_flags(ci_lanes.deploy_lanes(files, CONFIG), CONFIG) == "--frontend"


def test_backend_only_change_deploys_only_backend() -> None:
    files = ["src/api/orders.py", "tests/api/test_orders.py"]

    assert ci_lanes.ci_lanes(files, CONFIG) == ("backend",)
    assert ci_lanes.deploy_flags(ci_lanes.deploy_lanes(files, CONFIG), CONFIG) == "--backend"


def test_test_only_change_runs_ci_but_deploys_nothing() -> None:
    files = ["tests/services/test_orders.py"]

    assert ci_lanes.ci_lanes(files, CONFIG) == ("backend",)
    assert ci_lanes.deploy_lanes(files, CONFIG) == ()


def test_mixed_change_keeps_the_configured_order() -> None:
    files = ["src/main.py", "frontend/src/App.tsx"]

    lanes = ci_lanes.deploy_lanes(files, CONFIG)

    assert lanes == ("frontend", "backend")
    assert ci_lanes.deploy_flags(lanes, CONFIG) == "--frontend --backend"


def test_docs_only_change_activates_nothing() -> None:
    files = ["docs/guide.md", "README.md", " ", "docs\\other.md"]

    assert ci_lanes.ci_lanes(files, CONFIG) == ()
    assert ci_lanes.deploy_flags((), CONFIG) == ""


def test_pipeline_change_runs_every_ci_lane_but_deploys_nothing() -> None:
    files = [".github/workflows/ci-quality-gate.yml", "docs/pipeline.md"]

    assert ci_lanes.ci_lanes(files, CONFIG) == CONFIG.names
    assert ci_lanes.deploy_lanes(files, CONFIG) == ()


def _write_config(tmp_path: Path, lanes: list[dict]) -> Path:
    path = tmp_path / "lanes.json"
    path.write_text(json.dumps({"lanes": lanes}), encoding="utf-8")
    return path


def test_config_without_a_default_lane_ignores_unclassified_paths(tmp_path: Path) -> None:
    config = ci_lanes.load_config(_write_config(tmp_path, [{"name": "web", "paths": ["web/"]}]))

    assert config.default_lane is None
    assert ci_lanes.lane_for("anything.py", config) is None
    assert ci_lanes.lane_for("web/index.html", config) == "web"
    assert ci_lanes.deploy_flags(("web",), config) == ""


def test_config_rejects_two_default_lanes(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path, [{"name": "a", "default": True}, {"name": "b", "default": True}]
    )

    with pytest.raises(ValueError, match="at most one lane"):
        ci_lanes.load_config(path)


def test_changed_files_returns_none_without_a_usable_base() -> None:
    assert ci_lanes.changed_files("", "HEAD") is None
    assert ci_lanes.changed_files(ZERO_SHA, "HEAD") is None


def test_changed_files_reads_git_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock(return_value=SimpleNamespace(returncode=0, stdout="b.py\na.py\n\n"))
    monkeypatch.setattr(ci_lanes.subprocess, "run", run)

    assert ci_lanes.changed_files("base", "head") == ("a.py", "b.py")
    assert run.call_args.args[0] == ["git", "diff", "--name-only", "base", "head"]


def test_changed_files_returns_none_when_git_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ci_lanes.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=128, stdout=""))
    )

    assert ci_lanes.changed_files("base", "head") is None


def _outputs(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.strip().splitlines())


def test_main_ci_mode_writes_github_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr(ci_lanes, "changed_files", lambda base, head: ("frontend/src/App.tsx",))

    assert ci_lanes.main(["--base", "abc"]) == 0

    written = _outputs(output.read_text(encoding="utf-8"))
    assert written == _outputs(capsys.readouterr().out)
    assert written == {"frontend": "true", "backend": "false", "any": "true"}


def test_main_deploy_mode_emits_flags(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setattr(ci_lanes, "changed_files", lambda base, head: ("src/main.py",))

    assert ci_lanes.main(["--base", "abc", "--head", "def", "--mode", "deploy"]) == 0

    written = _outputs(capsys.readouterr().out)
    assert written["flags"] == "--backend"
    assert written["any"] == "true"


def test_main_deploy_mode_with_docs_only_has_nothing_to_deploy(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setattr(ci_lanes, "changed_files", lambda base, head: ("docs/a.md",))

    assert ci_lanes.main(["--base", "abc", "--mode", "deploy"]) == 0

    written = _outputs(capsys.readouterr().out)
    assert written["flags"] == ""
    assert written["any"] == "false"


@pytest.mark.parametrize(("mode", "flags"), [("ci", None), ("deploy", "--all")])
def test_main_falls_back_to_every_lane_without_a_diff(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str, flags: str | None
) -> None:
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setattr(ci_lanes, "changed_files", lambda base, head: None)

    assert ci_lanes.main(["--base", ZERO_SHA, "--mode", mode]) == 0

    captured = capsys.readouterr()
    written = _outputs(captured.out)
    assert all(written[name] == "true" for name in CONFIG.names)
    assert written.get("flags") == flags
    assert "every lane" in captured.err
