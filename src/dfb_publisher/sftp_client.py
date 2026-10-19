"""SFTP: leer job.json y descargar el mes de respaldo."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any

import paramiko

from dfb_publisher.period import Period
from dfb_publisher.settings import Settings


def _load_private_key(path: Path) -> paramiko.PKey:
    errors: list[str] = []
    for loader in (paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey):
        try:
            return loader.from_private_key_file(str(path))
        except Exception as exc:  # noqa: BLE001 — probar varios formatos
            errors.append(f"{loader.__name__}: {exc}")
    raise RuntimeError("No se pudo leer la clave SFTP: " + "; ".join(errors))


class SftpClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None

    def __enter__(self) -> "SftpClient":
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def connect(self) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = _load_private_key(self._settings.sftp_private_key_path)
        client.connect(
            hostname=self._settings.sftp_host,
            username=self._settings.sftp_username,
            pkey=key,
            look_for_keys=False,
            allow_agent=False,
            timeout=60,
        )
        self._client = client
        self._sftp = client.open_sftp()

    def close(self) -> None:
        if self._sftp is not None:
            self._sftp.close()
            self._sftp = None
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def sftp(self) -> paramiko.SFTPClient:
        if self._sftp is None:
            raise RuntimeError("SFTP no conectado")
        return self._sftp

    def read_job(self) -> dict[str, Any]:
        with self.sftp.open(self._settings.job_path, "r") as fh:
            raw = fh.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("job.json inválido")
        return data

    def download_month(self, period: Period, dest: Path) -> Path:
        remote = f"{self._settings.backup_base}/{period.year_dir}/{period.month_dir}"
        dest.mkdir(parents=True, exist_ok=True)
        try:
            self.sftp.stat(remote)
        except OSError as exc:
            raise FileNotFoundError(f"No existe el mes remoto: {remote}") from exc
        self._download_tree(remote, dest)
        return dest

    def _download_tree(self, remote: str, local: Path) -> None:
        local.mkdir(parents=True, exist_ok=True)
        for entry in self.sftp.listdir_attr(remote):
            name = entry.filename
            if name in (".", ".."):
                continue
            remote_path = f"{remote}/{name}"
            local_path = local / name
            mode = entry.st_mode or 0
            if stat.S_ISDIR(mode):
                self._download_tree(remote_path, local_path)
            else:
                self.sftp.get(remote_path, str(local_path))
