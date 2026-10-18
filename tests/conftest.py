import pytest


@pytest.fixture(autouse=True)
def _audit_log_in_a_temp_folder(tmp_path_factory, monkeypatch):
    """Reviews made by a test must not be written to the real audit log."""
    from app.ui import audit
    monkeypatch.setattr(audit, "LOG", tmp_path_factory.mktemp("audit") / "audit_log.jsonl")
