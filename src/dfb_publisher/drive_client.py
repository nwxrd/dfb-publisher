"""Google Drive: carpetas año/mes/programa, upload y listado."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from dfb_publisher.period import Period
from dfb_publisher.settings import Settings


@dataclass(frozen=True)
class DriveFile:
    name: str
    size: int
    path: str
    modified: str


class DriveClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._service = None

    def connect(self) -> None:
        creds = self._credentials()
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)

    @property
    def service(self):
        if self._service is None:
            raise RuntimeError("Drive no conectado")
        return self._service

    def _credentials(self) -> Credentials:
        scopes = self._settings.drive_scopes
        token_path = self._settings.token_path
        creds: Credentials | None = None
        if token_path.is_file():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json(), encoding="utf-8")
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._settings.credentials_path), scopes
            )
            creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    def ensure_folder(self, name: str, parent_id: str) -> str:
        safe = name.replace("'", "\\'")
        query = (
            "mimeType='application/vnd.google-apps.folder' "
            f"and name='{safe}' and trashed=false "
            f"and '{parent_id}' in parents"
        )
        result = (
            self.service.files()
            .list(q=query, fields="files(id, name)", pageSize=1)
            .execute()
        )
        files = result.get("files") or []
        if files:
            return files[0]["id"]
        meta = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        created = self.service.files().create(body=meta, fields="id").execute()
        return created["id"]

    def upload_or_replace(self, local: Path, folder_id: str, name: str, mime: str) -> str:
        existing = self._find_file(name, folder_id)
        media = MediaFileUpload(str(local), mimetype=mime, resumable=True)
        if existing:
            updated = (
                self.service.files()
                .update(fileId=existing, media_body=media, fields="id")
                .execute()
            )
            return updated["id"]
        meta = {"name": name, "parents": [folder_id]}
        created = (
            self.service.files()
            .create(body=meta, media_body=media, fields="id")
            .execute()
        )
        return created["id"]

    def _find_file(self, name: str, parent_id: str) -> str | None:
        safe = name.replace("'", "\\'")
        query = f"name='{safe}' and trashed=false and '{parent_id}' in parents"
        result = (
            self.service.files()
            .list(q=query, fields="files(id)", pageSize=1)
            .execute()
        )
        files = result.get("files") or []
        return files[0]["id"] if files else None

    def publish_month(
        self,
        period: Period,
        zips: list[tuple[str, Path]],
        report_local: Path,
        report_name: str,
    ) -> str:
        """Sube zips y reporte. Devuelve folder id del mes."""
        year_id = self.ensure_folder(period.year_dir, self._settings.drive_root_folder_id)
        month_id = self.ensure_folder(period.month_dir, year_id)
        for program, zip_path in zips:
            prog_id = self.ensure_folder(program, month_id)
            self.upload_or_replace(
                zip_path,
                prog_id,
                zip_path.name,
                "application/zip",
            )
        self.upload_or_replace(
            report_local,
            month_id,
            report_name,
            "text/html",
        )
        return month_id

    def list_month_inventory(self, month_folder_id: str, period: Period) -> list[DriveFile]:
        """Lista reporte + zips bajo el mes (un nivel de programas)."""
        base = f"{period.year_dir}/{period.month_dir}"
        items: list[DriveFile] = []
        for entry in self._list_children(month_folder_id):
            mime = entry.get("mimeType", "")
            name = entry["name"]
            if mime == "application/vnd.google-apps.folder":
                for child in self._list_children(entry["id"]):
                    if child.get("mimeType") == "application/vnd.google-apps.folder":
                        continue
                    items.append(
                        DriveFile(
                            name=child["name"],
                            size=int(child.get("size") or 0),
                            path=f"{base}/{name}/{child['name']}",
                            modified=str(child.get("modifiedTime") or ""),
                        )
                    )
            else:
                items.append(
                    DriveFile(
                        name=name,
                        size=int(entry.get("size") or 0),
                        path=f"{base}/{name}",
                        modified=str(entry.get("modifiedTime") or ""),
                    )
                )
        items.sort(key=lambda f: f.path)
        return items

    def _list_children(self, folder_id: str) -> list[dict[str, Any]]:
        result = (
            self.service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, size, modifiedTime, mimeType)",
                pageSize=200,
            )
            .execute()
        )
        return list(result.get("files") or [])
