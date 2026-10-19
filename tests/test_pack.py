from pathlib import Path

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
    results = zip_programs(month, out)
    assert len(results) == 1
    assert results[0].program == "Az_Conectados"
    assert results[0].zip_path.is_file()
    assert results[0].zip_path.name == "Az_Conectados.zip"


def test_missing_report(tmp_path: Path):
    month = tmp_path / "8-AGOSTO"
    month.mkdir()
    assert report_path(month) is None
