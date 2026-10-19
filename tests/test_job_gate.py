from dfb_publisher.job_gate import evaluate_job
from dfb_publisher.period import Period


def _job(**kwargs):
    base = {
        "status": "done",
        "year": 2026,
        "month": 9,
        "message": "Done",
    }
    base.update(kwargs)
    return base


def test_done_ok():
    r = evaluate_job(_job(), Period(2026, 9))
    assert r.ok is True


def test_error_blocks():
    r = evaluate_job(_job(status="error", message="Failed: X"), Period(2026, 9))
    assert r.ok is False
    assert "error" in r.reason.lower() or "Failed" in r.reason


def test_cancelled_blocks():
    r = evaluate_job(_job(status="cancelled"), Period(2026, 9))
    assert r.ok is False


def test_running_blocks():
    r = evaluate_job(_job(status="running"), Period(2026, 9))
    assert r.ok is False


def test_wrong_month_blocks():
    r = evaluate_job(_job(month=8), Period(2026, 9))
    assert r.ok is False
    assert "2026-08" in r.reason or "08" in r.reason
