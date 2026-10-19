from pathlib import Path

import pyzipper
import pytest

from dfb_publisher.pack import program_dirs, report_path, zip_programs


def test_program_dirs_and_zip(tmp_path: Path):
    month = tmp_path / "9-SEPTIEMBRE"
    month.mkdir()
    (month / "reporte.html").write_text("<html></html>", encoding="utf-8")
    (month / "resumen.json").write_text("{}", encoding="utf-8")

    prog = month / "Az_Conectados"
    (prog / "IN").mkdir(parents=True)
    (prog / "IN" / "a.wav").write_bytes(b"audio")
    (prog / "manifiesto.csv").write_text("tipo,estado\n", encoding="utf-8")

    empty = month / "sin_manifest"
    empty.mkdir()

    dirs = program_dirs(month)
    assert [d.name for d in dirs] == ["Az_Conectados"]
    assert report_path(month) is not None

    out = tmp_path / "zips"
    results = zip_programs(month, out, "secret-test")
    assert len(results) == 1
    assert results[0].program == "Az_Conectados"
    assert results[0].zip_path.is_file()
    assert results[0].zip_path.name == "Az_Conectados.zip"

    with pyzipper.AESZipFile(results[0].zip_path, "r") as zf:
        zf.setpassword(b"secret-test")
        assert "IN/a.wav" in zf.namelist()
        assert zf.read("IN/a.wav") == b"audio"


def test_zip_requires_password(tmp_path: Path):
    month = tmp_path / "8-AGOSTO"
    month.mkdir()
    prog = month / "X"
    prog.mkdir()
    (prog / "manifiesto.csv").write_text("x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        zip_programs(month, tmp_path / "z", "")


def test_missing_report(tmp_path: Path):
    month = tmp_path / "8-AGOSTO"
    month.mkdir()
    assert report_path(month) is None
