"""Comprime cada carpeta de programa en un ZIP."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

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


def zip_programs(month_dir: Path, out_dir: Path) -> list[ZipResult]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[ZipResult] = []
    for folder in program_dirs(month_dir):
        zip_path = out_dir / f"{folder.name}.zip"
        _zip_dir(folder, zip_path)
        results.append(ZipResult(program=folder.name, zip_path=zip_path))
    return results


def _zip_dir(source: Path, zip_path: Path) -> None:
    if zip_path.is_file():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            arcname = path.relative_to(source).as_posix()
            zf.write(path, arcname)


def report_path(month_dir: Path) -> Path | None:
    path = month_dir / "reporte.html"
    return path if path.is_file() else None
