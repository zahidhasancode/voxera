"""Disaster recovery procedure validation (documentation + asset checks)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_backup_restore_scripts_exist():
    assert (ROOT / "deploy/scripts/backup-postgres.sh").is_file()
    assert (ROOT / "deploy/scripts/restore-postgres.sh").is_file()


def test_backup_restore_docs_exist():
    doc = ROOT / "docs/operations/backup-restore.md"
    assert doc.is_file()
    content = doc.read_text()
    assert "pg_dump" in content
    assert "pg_restore" in content


def test_incident_response_doc_exists():
    assert (ROOT / "docs/operations/incident-response.md").is_file()


def test_production_checklist_exists():
    checklist = ROOT / "docs/operations/production-checklist.md"
    assert checklist.is_file()
    assert "Postgres backup" in checklist.read_text()
