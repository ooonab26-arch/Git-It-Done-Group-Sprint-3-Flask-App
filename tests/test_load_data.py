from load_data import clean_cell, parse_time, parse_flexible_date

def test_load_data_csv_fallback(app):
    app.config["GOOGLE_SHEETS_CREDENTIALS"] = None
    app.config["GOOGLE_SHEETS_SHEET_ID"] = None
    from load_data import get_sheet_rows
    rows = get_sheet_rows()
    assert isinstance(rows, list)

def test_load_data_empty_rows(app, monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_TABS", "")
    from load_data import get_sheet_rows
    with app.app_context():
        rows = get_sheet_rows()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_clean_cell_none():
    assert clean_cell(None) is None
    assert clean_cell("None") is None
    assert clean_cell("  none ") is None


def test_clean_cell_valid():
    assert clean_cell(" Hello ") == "Hello"


def test_parse_time_valid():
    assert parse_time("3pm").hour == 15
    assert parse_time("3:30pm").minute == 30
    assert parse_time("8.30pm").hour == 20


def test_parse_time_invalid():
    assert parse_time("") is None
    assert parse_time("badtime") is None


def test_parse_flexible_date_standard():
    d = parse_flexible_date("25-Jul-24")
    assert d.year == 2024
    assert d.month == 7
    assert d.day == 25


def test_parse_flexible_date_long():
    d = parse_flexible_date("November 6, 2024")
    assert d.year == 2024
    assert d.month == 11
    assert d.day == 6


def test_parse_flexible_date_range():
    d = parse_flexible_date("November 6-7, 2024")
    assert d.day == 6


def test_parse_flexible_date_invalid():
    assert parse_flexible_date("") is None
    assert parse_flexible_date("nonsense") is None


def test_load_data_skips_invalid_rows(app, monkeypatch):
    """Ensure invalid rows do not crash load_events"""
    from load_data import load_events

    monkeypatch.setenv("GOOGLE_SHEETS_TABS", "")
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")

    with app.app_context():
        # Should not raise
        load_events()
