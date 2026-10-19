"""Carga settings.toml + .env."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    root: Path
    sftp_host: str
    sftp_username: str
    sftp_private_key_path: Path
    job_path: str
    backup_base: str
    work_dir: Path
    drive_root_folder_id: str
    drive_scopes: list[str]
    credentials_path: Path
    token_path: Path
    report_prefix: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    zip_password: str
    smtp_to: list[str] = field(default_factory=list)
    smtp_cc: list[str] = field(default_factory=list)


def _split_emails(raw: str) -> list[str]:
    out: list[str] = []
    for part in raw.replace(";", ",").split(","):
        email = part.strip()
        if email:
            out.append(email)
    return out


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path


def load_settings(root: Path | None = None) -> Settings:
    root = root or ROOT
    load_dotenv(root / ".env")

    settings_path = root / "config" / "settings.toml"
    if not settings_path.is_file():
        example = root / "config" / "settings.example.toml"
        raise FileNotFoundError(
            f"Falta {settings_path}. Copie {example.name} a settings.toml"
        )

    with settings_path.open("rb") as fh:
        data = tomllib.load(fh)

    issabel = data.get("issabel", {})
    paths = data.get("paths", {})
    drive = data.get("drive", {})
    report = data.get("report", {})

    key_path = os.getenv("SFTP_PRIVATE_KEY_PATH", "secrets/key.pem")
    root_folder = os.getenv("DRIVE_ROOT_FOLDER_ID") or drive.get("root_folder_id", "")

    smtp_to = _split_emails(os.getenv("SMTP_TO", ""))
    smtp_cc = _split_emails(os.getenv("SMTP_CC", ""))

    return Settings(
        root=root,
        sftp_host=os.getenv("SFTP_HOST", "").strip(),
        sftp_username=os.getenv("SFTP_USERNAME", "").strip(),
        sftp_private_key_path=_resolve(root, key_path),
        job_path=str(issabel.get("job_path", "")),
        backup_base=str(issabel.get("backup_base", "")).rstrip("/"),
        work_dir=_resolve(root, paths.get("work_dir", "work")),
        drive_root_folder_id=str(root_folder).strip(),
        drive_scopes=list(drive.get("scopes") or ["https://www.googleapis.com/auth/drive"]),
        credentials_path=_resolve(root, drive.get("credentials_path", "secrets/credentials.json")),
        token_path=_resolve(root, drive.get("token_path", "secrets/token.json")),
        report_prefix=str(report.get("prefix", "R_IT_AUD_002")),
        smtp_host=os.getenv("SMTP_HOST", "smtp.sendgrid.net").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "465")),
        smtp_user=os.getenv("SMTP_USER", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", "").strip(),
        smtp_from_name=os.getenv("SMTP_FROM_NAME", "Analisis&Tecnologia").strip(),
        zip_password=os.getenv("ZIP_PASSWORD", ""),
        smtp_to=smtp_to,
        smtp_cc=smtp_cc,
    )


def require_runtime(settings: Settings) -> None:
    missing: list[str] = []
    if not settings.sftp_host:
        missing.append("SFTP_HOST")
    if not settings.sftp_username:
        missing.append("SFTP_USERNAME")
    if not settings.sftp_private_key_path.is_file():
        missing.append(f"clave SFTP ({settings.sftp_private_key_path})")
    if not settings.job_path:
        missing.append("issabel.job_path")
    if not settings.backup_base:
        missing.append("issabel.backup_base")
    if not settings.drive_root_folder_id or settings.drive_root_folder_id == "YOUR_FOLDER_ID":
        missing.append("drive.root_folder_id")
    if not settings.credentials_path.is_file():
        missing.append(f"credentials Drive ({settings.credentials_path})")
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        missing.append("SMTP_HOST/USER/PASSWORD")
    if not settings.smtp_from_email or not settings.smtp_to:
        missing.append("SMTP_FROM_EMAIL / SMTP_TO")
    if not settings.zip_password:
        missing.append("ZIP_PASSWORD")
    if missing:
        raise RuntimeError("Config incompleta: " + ", ".join(missing))
