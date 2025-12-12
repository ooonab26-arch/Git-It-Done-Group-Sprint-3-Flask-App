import csv
import os
import re
from googleapiclient.discovery import build
from flask import current_app
from google.oauth2.service_account import Credentials
from datetime import datetime
from models import db, Events, Advertisement, Partners, Organizer, Event_Type, event_organizers, event_partners


def get_sheet_rows():
    """Load from Google Sheets if configured. Otherwise fallback to CSV."""

    creds_dict = current_app.config.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = current_app.config.get("GOOGLE_SHEETS_SHEET_ID")
    tabs = current_app.config.get("GOOGLE_SHEETS_TABS")

    # If ANY required Google value is missing → fallback
    if not creds_dict or not sheet_id or not tabs:
        print("No Google Sheets configuration found — loading from CSV instead.")
        return load_from_csv()

    print("Google Sheets detected — loading remotely")

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

    service = build("sheets", "v4", credentials=creds)
    sheet_api = service.spreadsheets()

    tab_list = [t.strip() for t in tabs.split(",")]
    all_rows = []

    for sheet_name in tab_list:
        result = sheet_api.values().get(
            spreadsheetId=sheet_id,
            range=sheet_name
        ).execute()

        rows = result.get("values", [])
        if not rows:
            print(f"⚠ No data in sheet: {sheet_name}")
            continue

        headers = rows[0]
        for r in rows[1:]:
            row_dict = {headers[i]: r[i] if i < len(r) else "" for i in range(len(headers))}
            all_rows.append(row_dict)

    return all_rows


def load_from_csv():
    """Load rows from SW_Events.csv for local testing."""
    # Use the CSV that actually exists in /data
    csv_path = os.path.join(
        os.path.dirname(__file__), "data", "SW_Events.csv"
    )

    if not os.path.exists(csv_path):
        print(f"⚠ {csv_path} not found — returning 0 rows")
        return []

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Loaded {len(rows)} rows from {os.path.basename(csv_path)}")
    return rows


def return_id(model, name):
    """Get or create a record by name and return its ID."""
    instance = db.session.query(model).filter_by(name=name).first()
    if not instance:
        instance = model(name=name)
        db.session.add(instance)
        db.session.commit()  # commit to get ID
    return instance.id

def clean_cell(cell):
    """Return None if cell is empty or 'None', else stripped value."""
    if not cell or cell.strip().lower() == 'none':
        return None
    return cell.strip()

def parse_time(tstr):
    """
    Parse a time string like '3pm', '8.30pm', or '3:30pm' into a datetime.time object.
    Returns None if invalid.
    """
    if not tstr:
        return None
    tstr = tstr.strip().lower().replace('.', ':')  # convert 3.30pm -> 3:30pm
    # Add :00 if missing minutes
    if ':' not in tstr[:-2]:
        tstr = tstr[:-2] + ':00' + tstr[-2:]  # 3pm -> 3:00pm
    try:
        return datetime.strptime(tstr, "%I:%M%p").time()
    except ValueError:
        return None

def parse_flexible_date(value):
    """
    Accept formats like:
      - 25-Jul-24
      - November 6, 2024
      - November 6-7, 2024  → take the 6th
      - Nov 6-7 2024
    """
    if not value:
        return None

    v = value.strip()

    # Case 1: standard dd-Mon-yy
    try:
        return datetime.strptime(v, "%d-%b-%y").date()
    except:
        pass

    # Case 2: long format (November 6, 2024)
    try:
        return datetime.strptime(v, "%B %d, %Y").date()
    except:
        pass

    # Case 3: extract first date from ranges (e.g., "November 6-7, 2024")
    m = re.search(r"([A-Za-z]+)\s+(\d+)", v)
    y = re.search(r"(\d{4})", v)

    if m and y:
        month = m.group(1)
        day = m.group(2)
        year = y.group(1)
        try:
            return datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()
        except:
            pass

    return None


def load_events():
    rows = get_sheet_rows()
    
    for row in rows:
        # Parse date safely
        try:
            date = parse_flexible_date(row['Date'])
            date_cell = clean_cell(row.get("Date"))
            if not date and date_cell and date_cell.lower() == "recurring":
                date = None
            elif not date:
                print(f"Skipping row due to invalid date: {row.get('Date')}")
                continue
        except ValueError:
            print(f"Skipping row due to invalid date: {row.get('Date')}")
            continue
        
        start_time = parse_time(clean_cell(row.get('Start Time')))
        end_time = parse_time(clean_cell(row.get('End Time')))
        if not start_time or not end_time:
            print(f"Skipping row due to invalid time: {row.get('Start Time')} or {row.get('End Time')}")
            continue

        # Event type
        type_name = clean_cell(row.get('EventType'))
        type_id = return_id(Event_Type, type_name) if type_name else None
        
        # Create Event
        event = Events(
            title=clean_cell(row.get('Name of Event/Activity')) or "Untitled Event",
            date=date,
            start_time=start_time,
            end_time=end_time,
            attendance=int(row['Attendance']) if row.get('Attendance') else None,
            location=clean_cell(row.get('Location')),
            description=clean_cell(row.get('Description')),
            type_id=type_id
        )
        db.session.add(event)
        db.session.flush()  # get event.id without committing yet
        
        # Handle multiple advertisements
        advert_cells = [clean_cell(a) for a in (row.get('Advertisement','').split(',')) if clean_cell(a)]
        advert_ids = [return_id(Advertisement, a) for a in advert_cells]
        if advert_ids:
            event.advert_id = advert_ids[0]  # main FK
        
        # Handle multiple organizers
        organizer_cells = [clean_cell(o) for o in (row.get('Lead Organizer','').split(',')) if clean_cell(o)]
        organizer_ids = [return_id(Organizer, o) for o in organizer_cells]
        for oid in organizer_ids:
            db.session.execute(event_organizers.insert().values(event_id=event.id, organizer_id=oid).prefix_with("OR IGNORE"))
        if organizer_ids:
            event.lead_organizer = organizer_ids[0]  # main FK
        
        # Handle multiple partners
        partner_cells = [clean_cell(p) for p in (row.get('Partners','').split(',')) if clean_cell(p)]
        partner_ids = [return_id(Partners, p) for p in partner_cells]
        for pid in partner_ids:
            db.session.execute(event_partners.insert().values(event_id=event.id, partner_id=pid).prefix_with("OR IGNORE"))
        if partner_ids:
            event.partner_id = partner_ids[0]  # main FK
        
        # Commit once per row
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Skipping row due to DB error: {e}")

    print("Data loaded successfully from CSV!")