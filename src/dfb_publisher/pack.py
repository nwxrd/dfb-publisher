"""Comprime cada carpeta de programa en un ZIP AES-256 con clave."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyzipper

MANIFEST = "manifiesto.csv"


@dataclass(frozen=True)
class ZipResult:
    program: str
    zip_path: Path


def program_dirs(month_dir: Path) -> list[Path]:
    """Carpetas de programa: tienen manifiesto.csv."""
    if not month_dir.is_dir():
        return []
    out: list[Path] = []
    for child in sorted(month_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / MANIFEST).is_file():
            out.append(child)
    return out


def zip_programs(month_dir: Path, out_dir: Path, password: str) -> list[ZipResult]:
    if not password:
        raise ValueError("ZIP_PASSWORD vacío: se requiere clave para AES-256")
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[ZipResult] = []
    for folder in program_dirs(month_dir):
        zip_path = out_dir / f"{folder.name}.zip"
        _zip_dir_aes(folder, zip_path, password)
        results.append(ZipResult(program=folder.name, zip_path=zip_path))
    return results


def _zip_dir_aes(source: Path, zip_path: Path, password: str) -> None:
    if zip_path.is_file():
        zip_path.unlink()
    pwd = password.encode("utf-8")
    with pyzipper.AESZipFile(
        zip_path,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(pwd)
        zf.setencryption(pyzipper.WZ_AES, nbits=256)
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            arcname = path.relative_to(source).as_posix()
            zf.write(path, arcname)


def report_path(month_dir: Path) -> Path | None:
    path = month_dir / "reporte.html"
    return path if path.is_file() else None
