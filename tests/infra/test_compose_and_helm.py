import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_docker_compose_prod_config_valid():
    if not shutil.which("docker"):
        return
    env = {**os.environ, "POSTGRES_PASSWORD": "test-secret-for-compose-config"}
    (ROOT / ".env.production").touch(exist_ok=True)
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.prod.yml", "config"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr


def test_docker_compose_dev_config_valid():
    if not shutil.which("docker"):
        return
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "config"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_helm_chart_lint():
    if not shutil.which("helm"):
        return
    result = subprocess.run(
        ["helm", "lint", "deploy/helm/voxera"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
