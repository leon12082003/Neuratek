from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

SERVICE_ACCOUNT_FILE = 'service_account.json'
CALENDAR_ID = 'neuratek-calendar-service@neuratek-479922.iam.gserviceaccount.com'
TIMEZONE = 'Europe/Berlin'
OPENING_HOURS = {
    "monday": ("08:00", "18:00"),
    "tuesday": ("08:00", "18:00"),
    "wednesday": ("08:00", "18:00"),
    "thursday": ("08:00", "18:00"),
    "friday": ("08:00", "18:00"),
    "saturday": ("10:00", "14:00"),
    "sunday": ("10:00", "14:00"),
}
SLOT_DURATION_MINUTES = 60
NO_GAP_BETWEEN_SLOTS = True

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/calendar']
)
service = build('calendar', 'v3', credentials=credentials)


def get_day_opening_hours(date_obj):
    weekday = date_obj.strftime('%A').lower()
    return OPENING_HOURS.get(weekday, (None, None))


def get_free_slots(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    start_str, end_str = get_day_opening_hours(date_obj)
    if not start_str or not end_str:
        return []

    tz = pytz.timezone(TIMEZONE)
    day_start = tz.localize(datetime.combine(date_obj, datetime.strptime(start_str, "%H:%M").time()))
    day_end = tz.localize(datetime.combine(date_obj, datetime.strptime(end_str, "%H:%M").time()))

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    slots = []
    current = day_start

    while current + timedelta(minutes=SLOT_DURATION_MINUTES) <= day_end:
        overlap = False
        for event in events:
            event_start = datetime.fromisoformat(event['start']['dateTime']).astimezone(tz)
            event_end = datetime.fromisoformat(event['end']['dateTime']).astimezone(tz)
            if not (current + timedelta(minutes=SLOT_DURATION_MINUTES) <= event_start or current >= event_end):
                overlap = True
                break
        if not overlap:
            slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=SLOT_DURATION_MINUTES)

    return slots


def book_appointment(name, company, date, time, phone):
    tz = pytz.timezone(TIMEZONE)
    start = tz.localize(datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
    end = start + timedelta(minutes=SLOT_DURATION_MINUTES)

    if not check_availability(date, time):
        return False

    event = {
        'summary': f"{name} ({company})",
        'description': f"Telefon: {phone}",
        'start': {'dateTime': start.isoformat(), 'timeZone': TIMEZONE},
        'end': {'dateTime': end.isoformat(), 'timeZone': TIMEZONE},
    }

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return True


def delete_appointment(name, date, time):
    tz = pytz.timezone(TIMEZONE)
    start = tz.localize(datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
    end = start + timedelta(minutes=SLOT_DURATION_MINUTES)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True
    ).execute()

    for event in events_result.get('items', []):
        if name.lower() in event.get('summary', '').lower():
            service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
            return True
    return False


def get_next_available_slot():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    for day_offset in range(30):  # bis 30 Tage in die Zukunft
        date_obj = now.date() + timedelta(days=day_offset)
        date_str = date_obj.strftime("%Y-%m-%d")
        slots = get_free_slots(date_str)
        for slot in slots:
            slot_time = tz.localize(datetime.strptime(f"{date_str} {slot}", "%Y-%m-%d %H:%M"))
            if slot_time > now:
                return {"date": date_str, "time": slot}
    return None


def check_availability(date, time):
    return time in get_free_slots(date)
