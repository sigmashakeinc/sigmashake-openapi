"""Integration tests for the CLI validation scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
OPENAPI_DIR = SCRIPTS_DIR.parent
SPEC_PATH = OPENAPI_DIR / "openapi.yaml"
PYTHON_MODELS = OPENAPI_DIR.parent / "sigmashake-sdk-python" / "src" / "sigmashake" / "models.py"
NODE_MODELS = OPENAPI_DIR.parent / "sigmashake-sdk-node" / "src" / "models.ts"


class TestValidatePythonSdkCli:
    def test_exits_nonzero_when_drift_exists(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_python_sdk.py")],
            capture_output=True,
            text=True,
        )
        # Current SDKs have known drift, so exit code should be 1
        assert result.returncode == 1

    def test_json_output_is_valid(self) -> None:
        import json

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_python_sdk.py"), "--json"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["sdk"] == "python"
        assert "total_schemas" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_reports_missing_schemas(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_python_sdk.py")],
            capture_output=True,
            text=True,
        )
        assert "MISSING SCHEMA" in result.stdout

    def test_reports_missing_fields(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_python_sdk.py")],
            capture_output=True,
            text=True,
        )
        assert "MISSING FIELD" in result.stdout


class TestValidateNodeSdkCli:
    def test_exits_nonzero_when_drift_exists(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_node_sdk.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_json_output_is_valid(self) -> None:
        import json

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_node_sdk.py"), "--json"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["sdk"] == "node"
        assert "total_schemas" in data
        assert isinstance(data["items"], list)

    def test_reports_missing_schemas(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_node_sdk.py")],
            capture_output=True,
            text=True,
        )
        assert "MISSING SCHEMA" in result.stdout


class TestValidateSdksShell:
    def test_validate_sdks_script_runs(self) -> None:
        result = subprocess.run(
            [str(OPENAPI_DIR / "validate-sdks.sh")],
            capture_output=True,
            text=True,
        )
        # Should detect drift in both SDKs
        assert result.returncode == 1
        assert "Python SDK" in result.stdout or "DRIFT" in result.stdout

    def test_python_only_flag(self) -> None:
        result = subprocess.run(
            [str(OPENAPI_DIR / "validate-sdks.sh"), "--python"],
            capture_output=True,
            text=True,
        )
        assert "Python SDK" in result.stdout
        assert "Node SDK" not in result.stdout

    def test_node_only_flag(self) -> None:
        result = subprocess.run(
            [str(OPENAPI_DIR / "validate-sdks.sh"), "--node"],
            capture_output=True,
            text=True,
        )
        assert "Node SDK" in result.stdout
        assert "Python SDK" not in result.stdout
