"""Unit tests for job performance analytics."""

import os
import tempfile
import pytest
from runai_agent.functions.failure_analyzer import FailureDatabase
from runai_agent.functions.job_analytics import (
    JobAnalyticsConfig,
    runai_job_analytics,
    _format_duration,
)


@pytest.fixture
def temp_db():
    """Temporary SQLite DB with job_run_history table."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = FailureDatabase(path)
    yield db, path
    try:
        os.unlink(path)
    except OSError:
        pass


def test_format_duration():
    assert _format_duration(45) == "45s"
    assert _format_duration(120) == "2m"
    assert _format_duration(3661) == "1h 1m"


def test_record_and_aggregate(temp_db):
    db, path = temp_db
    db.record_job_run(
        job_id="job-1",
        job_name="train-1",
        project="p1",
        status="Succeeded",
        ended_at="2025-02-05T12:00:00Z",
        started_at="2025-02-05T10:00:00Z",
        image="pytorch:latest",
        gpu_count=2,
    )
    db.record_job_run(
        job_id="job-2",
        job_name="train-2",
        project="p1",
        status="Succeeded",
        ended_at="2025-02-05T13:00:00Z",
        started_at="2025-02-05T12:00:00Z",
        image="pytorch:latest",
        gpu_count=2,
    )
    agg = db.get_run_aggregates(days=7)
    assert agg["runs_count"] == 2
    assert agg["runs_with_duration"] == 2
    assert agg["by_project"]["p1"] == 5400  # 2h and 1h -> avg 1.5h = 5400s
    assert "pytorch:latest" in agg["by_image"]


def test_record_job_run_dedup(temp_db):
    db, path = temp_db
    ok1 = db.record_job_run(
        job_id="job-1",
        job_name="train-1",
        project="p1",
        status="Succeeded",
        ended_at="2025-02-05T12:00:00Z",
        started_at="2025-02-05T10:00:00Z",
        image="img",
        gpu_count=1,
    )
    ok2 = db.record_job_run(
        job_id="job-1",
        job_name="train-1",
        project="p1",
        status="Succeeded",
        ended_at="2025-02-05T12:00:00Z",
        started_at="2025-02-05T10:00:00Z",
        image="img",
        gpu_count=1,
    )
    assert ok1 is True
    assert ok2 is False
    history = db.get_job_run_history(days=7)
    assert len(history) == 1


@pytest.mark.asyncio
async def test_job_analytics_empty_db():
    """Analytics with no data returns helpful message."""
    import sys
    if "nat.builder.builder" not in sys.modules:
        try:
            from nat.builder.builder import Builder  # noqa: F401
        except ImportError:
            pytest.skip("NAT not installed")
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        prev = os.environ.get("RUNAI_FAILURE_DB_PATH")
        os.environ["RUNAI_FAILURE_DB_PATH"] = path
        FailureDatabase(path)  # init schema
        config = JobAnalyticsConfig(db_path=path, allowed_projects=["*"])
        from unittest.mock import MagicMock
        gen = runai_job_analytics(config, MagicMock())
        fn_info = await gen.__anext__()
        result = await fn_info.single_fn(lookback_days=7, project=None)
        assert "Job Performance Analytics" in result
        assert "Execution time trends" in result or "No run history" in result
    finally:
        if prev is not None:
            os.environ["RUNAI_FAILURE_DB_PATH"] = prev
        else:
            os.environ.pop("RUNAI_FAILURE_DB_PATH", None)
        try:
            os.unlink(path)
        except OSError:
            pass
