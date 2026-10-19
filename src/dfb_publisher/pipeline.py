"""Orquesta: gate → SFTP → zip → Drive → correo."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from dfb_publisher.drive_client import DriveClient
from dfb_publisher.job_gate import evaluate_job
from dfb_publisher.notify import Notifier
from dfb_publisher.pack import report_path, zip_programs
from dfb_publisher.period import Period
from dfb_publisher.settings import Settings, require_runtime
from dfb_publisher.sftp_client import SftpClient

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    ok: bool
    exit_code: int
    message: str


def run_publish(settings: Settings, period: Period) -> PublishResult:
    require_runtime(settings)
    notifier = Notifier(settings)
    month_local = settings.work_dir / period.year_dir / period.month_dir
    zips_dir = settings.work_dir / "_zips" / period.year_dir / period.month_dir

    try:
        with SftpClient(settings) as sftp:
            job = sftp.read_job()
            gate = evaluate_job(job, period)
            if not gate.ok:
                logger.warning("Gate: %s", gate.reason)
                notifier.send_skipped(period, gate.reason, gate.status)
                return PublishResult(False, 1, gate.reason)

            if month_local.exists():
                shutil.rmtree(month_local)
            sftp.download_month(period, month_local)

        report = report_path(month_local)
        if report is None:
            reason = f"No existe reporte.html en {period.year_dir}/{period.month_dir}"
            logger.warning(reason)
            notifier.send_skipped(period, reason, "done")
            return PublishResult(False, 1, reason)

        if zips_dir.exists():
            shutil.rmtree(zips_dir)
        zips = zip_programs(month_local, zips_dir, settings.zip_password)
        if not zips:
            reason = "No hay carpetas de programa con manifiesto.csv"
            logger.warning(reason)
            notifier.send_skipped(period, reason, "done")
            return PublishResult(False, 1, reason)

        report_name = period.report_filename(settings.report_prefix)
        drive = DriveClient(settings)
        drive.connect()
        month_id = drive.publish_month(
            period,
            [(z.program, z.zip_path) for z in zips],
            report,
            report_name,
        )
        inventory = drive.list_month_inventory(month_id, period)
        notifier.send_success(period, inventory, report_name, len(zips))
        msg = f"Publicado {len(zips)} ZIP(s) + {report_name}"
        logger.info(msg)
        return PublishResult(True, 0, msg)

    except Exception as exc:
        logger.exception("Publicación fallida")
        try:
            notifier.send_error(period, str(exc))
        except Exception:
            logger.exception("Además falló el correo de error")
        return PublishResult(False, 1, str(exc))
    finally:
        # Liberar disco local tras el intento
        for path in (month_local, zips_dir):
            if path.exists():
                try:
                    shutil.rmtree(path)
                except OSError:
                    logger.warning("No se pudo limpiar %s", path)
