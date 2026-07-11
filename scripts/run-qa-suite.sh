#!/usr/bin/env bash
# Enterprise QA suite runner for VOXERA
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROFILE="${1:-pr}"

echo "==> VOXERA QA Suite (profile: ${PROFILE})"

run_unit() {
  python3 -m pytest tests/ \
    -m "unit and not slow" \
    --ignore=tests/load \
    -q "$@"
}

run_integration() {
  python3 -m pytest tests/integration/ -m integration -q "$@"
}

run_e2e() {
  python3 -m pytest tests/e2e/ -m e2e -q "$@"
}

run_security() {
  python3 -m pytest tests/security/ -m security -q "$@"
}

run_chaos() {
  python3 -m pytest tests/chaos/ -m chaos -q "$@"
}

run_benchmark() {
  python3 -m pytest tests/integration/performance/ -m benchmark -q "$@"
}

run_coverage() {
  python3 -m pytest tests/ \
    --ignore=tests/load \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:reports/coverage/html \
    --cov-report=xml:reports/coverage/coverage.xml \
    --cov-fail-under=65 \
    -q "$@"
}

case "$PROFILE" in
  pr)
    run_unit
    run_security
    run_e2e
    run_benchmark
    ;;
  full)
    run_unit
    run_integration
    run_e2e
    run_security
    run_chaos
    run_benchmark
    run_coverage
    ;;
  coverage)
    run_coverage
    ;;
  *)
    echo "Unknown profile: $PROFILE (use pr|full|coverage)"
    exit 1
    ;;
esac

echo "==> QA suite complete"
