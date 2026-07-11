from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_exists():
    assert (ROOT / "Dockerfile").is_file()
    assert (ROOT / "Dockerfile.dev").is_file()


def test_compose_files_exist():
    assert (ROOT / "docker-compose.yml").is_file()
    assert (ROOT / "docker-compose.prod.yml").is_file()
    assert (ROOT / "docker-compose.monitoring.yml").is_file()


def test_helm_chart_exists():
    chart = ROOT / "deploy" / "helm" / "voxera"
    assert (chart / "Chart.yaml").is_file()
    assert (chart / "values.yaml").is_file()
    assert (chart / "templates" / "deployment-api.yaml").is_file()


def test_ci_workflow_exists():
    assert (ROOT / ".github" / "workflows" / "ci.yml").is_file()


def test_health_scripts_exist():
    assert (ROOT / "scripts" / "healthcheck.py").is_file()
    assert (ROOT / "scripts" / "validate-env.py").is_file()
    assert (ROOT / "scripts" / "docker-entrypoint.sh").is_file()


def test_prometheus_config_valid():
    prom = ROOT / "deploy" / "monitoring" / "prometheus" / "prometheus.yml"
    content = prom.read_text()
    assert "voxera-api" in content
    assert "/api/v1/metrics" in content
