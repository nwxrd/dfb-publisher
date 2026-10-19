"""Correo SMTP SSL: éxito, omisión o error técnico."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from html import escape

from dfb_publisher.drive_client import DriveFile
from dfb_publisher.period import Period
from dfb_publisher.settings import Settings


def _human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


class Notifier:
    def __init__(self, settings: Settings):
        self._settings = settings

    def send_skipped(self, period: Period, reason: str, status: str = "") -> None:
        subject = f"Publicación Drive omitida · {period.label}"
        body = f"""
        <html><body style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222">
          <p>No se publicó el respaldo de <b>{escape(period.label)}</b> en Google Drive.</p>
          <p><b>Motivo:</b> {escape(reason)}</p>
          {"<p><b>Estado job:</b> " + escape(status) + "</p>" if status else ""}
          <p>Revise el módulo en Issabel. Cuando el job quede en <code>done</code> para este mes, vuelva a ejecutar el publisher.</p>
        </body></html>
        """
        self._send(subject, body)

    def send_error(self, period: Period, error: str) -> None:
        subject = f"Error publicación Drive · {period.label}"
        body = f"""
        <html><body style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222">
          <p>Falló la publicación del respaldo de <b>{escape(period.label)}</b>.</p>
          <p><b>Error:</b> {escape(error)}</p>
        </body></html>
        """
        self._send(subject, body)

    def send_success(
        self,
        period: Period,
        inventory: list[DriveFile],
        report_name: str,
        zip_count: int,
    ) -> None:
        subject = f"Respaldo en Drive · {period.label}"
        rows = ""
        for item in inventory:
            rows += (
                "<tr>"
                f"<td style='border:1px solid #ddd;padding:6px'>{escape(item.name)}</td>"
                f"<td style='border:1px solid #ddd;padding:6px'>{escape(_human_size(item.size))}</td>"
                f"<td style='border:1px solid #ddd;padding:6px'>{escape(item.path)}</td>"
                "</tr>"
            )
        body = f"""
        <html><body style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222">
          <p>El respaldo de <b>{escape(period.label)}</b> quedó publicado en Google Drive.</p>
          <ul>
            <li>Programas (ZIP): {zip_count}</li>
            <li>Informe: {escape(report_name)}</li>
            <li>Ruta: {escape(period.year_dir)}/{escape(period.month_dir)}/</li>
          </ul>
          <table style="border-collapse:collapse;width:100%;font-size:12px;margin-top:12px">
            <tr style="background:#f1f5f9">
              <th style="border:1px solid #ddd;padding:6px;text-align:left">Archivo</th>
              <th style="border:1px solid #ddd;padding:6px;text-align:left">Tamaño</th>
              <th style="border:1px solid #ddd;padding:6px;text-align:left">Ubicación</th>
            </tr>
            {rows}
          </table>
        </body></html>
        """
        self._send(subject, body)

    def _send(self, subject: str, html_body: str) -> None:
        cfg = self._settings
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{cfg.smtp_from_name} <{cfg.smtp_from_email}>"
        msg["To"] = ", ".join(cfg.smtp_to)
        if cfg.smtp_cc:
            msg["Cc"] = ", ".join(cfg.smtp_cc)
        msg.add_alternative(html_body, subtype="html")

        recipients = list(cfg.smtp_to) + list(cfg.smtp_cc)
        with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=60) as smtp:
            smtp.login(cfg.smtp_user, cfg.smtp_password)
            smtp.send_message(msg, to_addrs=recipients)
