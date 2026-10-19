from datetime import date

from dfb_publisher.period import parse_month, previous_month


def test_parse_month():
    p = parse_month("2026-09")
    assert p.year == 2026
    assert p.month == 9
    assert p.year_dir == "2026"
    assert p.month_dir == "9-SEPTIEMBRE"
    assert p.month_name == "SEPTIEMBRE"


def test_report_filename():
    p = parse_month("2026-04")
    assert p.report_filename() == "R_IT_AUD_002_ABRIL_2026.html"
    assert p.report_filename("R_IT_AUD_002") == "R_IT_AUD_002_ABRIL_2026.html"


def test_previous_month_january():
    p = previous_month(date(2026, 1, 15))
    assert p.year == 2025
    assert p.month == 12
    assert p.month_dir == "12-DICIEMBRE"


def test_previous_month_normal():
    p = previous_month(date(2026, 10, 19))
    assert p.year == 2026
    assert p.month == 9
