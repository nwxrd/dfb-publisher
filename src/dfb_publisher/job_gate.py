"""Validación de job.json de Issabel antes de publicar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dfb_publisher.period import Period


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str
    status: str
    message: str
    job: dict[str, Any]


def evaluate_job(job: dict[str, Any], period: Period) -> GateResult:
    status = str(job.get("status") or "idle")
    message = str(job.get("message") or "")
    job_year = int(job.get("year") or 0)
    job_month = int(job.get("month") or 0)

    if status == "running":
        return GateResult(False, "Respaldo en curso (job.status=running)", status, message, job)
    if status == "cancelled":
        return GateResult(False, "Respaldo cancelado (job.status=cancelled)", status, message, job)
    if status == "error":
        detail = message or "sin detalle"
        return GateResult(False, f"Respaldo con error: {detail}", status, message, job)
    if status != "done":
        return GateResult(
            False,
            f"Respaldo no listo (job.status={status})",
            status,
            message,
            job,
        )
    if job_year != period.year or job_month != period.month:
        return GateResult(
            False,
            (
                f"El job es {job_year}-{job_month:02d}, "
                f"pero se pidió publicar {period.year}-{period.month:02d}"
            ),
            status,
            message,
            job,
        )
    return GateResult(True, "OK", status, message, job)
