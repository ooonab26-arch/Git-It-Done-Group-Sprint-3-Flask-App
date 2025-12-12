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
