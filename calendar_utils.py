
from datetime import datetime, timedelta, time
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz
from config import CALENDAR_ID, TIMEZONE

SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file(
    'service_account.json', scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

tz = pytz.timezone(TIMEZONE)
SLOT_DURATION = timedelta(minutes=60)
START_HOUR = 8
END_HOUR = 18

def is_slot_free(calendar_id, dt):
    dt = dt.replace(tzinfo=None)
    start = tz.localize(dt)
    end = start + SLOT_DURATION

    events = service.events().list(
        calendarId=calendar_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True
    ).execute().get("items", [])

    return len(events) == 0

def get_free_slots_for_day(calendar_id, date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    free_slots = []
    for hour in range(START_HOUR, END_HOUR):
        start_dt = datetime.combine(date, time(hour))
        if is_slot_free(calendar_id, start_dt):
            free_slots.append(start_dt.isoformat())
    return free_slots

def find_next_free_slot(calendar_id):
    now = datetime.now(tz)
    current = now.replace(minute=0, second=0, microsecond=0)
    while True:
        if current.weekday() < 5 and START_HOUR <= current.hour < END_HOUR:
            if is_slot_free(calendar_id, current):
                return current.isoformat()
        current += timedelta(hours=1)
