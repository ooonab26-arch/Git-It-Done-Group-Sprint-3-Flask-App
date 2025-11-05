import csv
import os
from datetime import datetime
from models import db, Events, Advertisement, Partners, Organizer, Event_Type, event_organizers, event_partners

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


def load_events():
    csv_path = os.path.join(os.path.dirname(__file__), 'SW_Events.csv')
    
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse date safely
            try:
                date = datetime.strptime(row['Date'], "%d-%b-%y").date()
            except ValueError:
                print(f"Skipping row due to invalid date: {row.get('Date')}")
                continue
            
            start_time = parse_time(clean_cell(row.get('Start Time')))
            end_time = parse_time(clean_cell(row.get('End Time')))
            if not start_time or not end_time:
                print(f"Skipping row due to invalid time: {row.get('Start Time')} or {row.get('End Time')}")
                continue

            # Event type
            type_name = clean_cell(row.get('Type'))
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
                db.session.execute(event_organizers.insert().values(event_id=event.id, organizer_id=oid))
            if organizer_ids:
                event.lead_organizer = organizer_ids[0]  # main FK
            
            # Handle multiple partners
            partner_cells = [clean_cell(p) for p in (row.get('Partners','').split(',')) if clean_cell(p)]
            partner_ids = [return_id(Partners, p) for p in partner_cells]
            for pid in partner_ids:
                db.session.execute(event_partners.insert().values(event_id=event.id, partner_id=pid))
            if partner_ids:
                event.partner_id = partner_ids[0]  # main FK
            
            # Commit once per row
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Skipping row due to DB error: {e}")

    print("Data loaded successfully from CSV!")
