# calendar_utils.py

import datetime
import pytz
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import CALENDAR_ID, TIMEZONE, WORK_HOURS

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service():
    creds = Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=creds)


def is_slot_free(service, start_dt, end_dt):
    events = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return len(events.get("items", [])) == 0


def get_free_slots_for_day(date):
    tz = pytz.timezone(TIMEZONE)
    weekday = date.strftime("%a").lower()

    if weekday not in WORK_HOURS:
        return []

    start_str, end_str = WORK_HOURS[weekday]

    start_dt = tz.localize(datetime.datetime.combine(date, datetime.datetime.strptime(start_str, "%H:%M").time()))
    end_dt = tz.localize(datetime.datetime.combine(date, datetime.datetime.strptime(end_str, "%H:%M").time()))

    service = get_service()
    free_slots = []

    current = start_dt
    while current + datetime.timedelta(hours=1) <= end_dt:
        next_hour = current + datetime.timedelta(hours=1)
        if is_slot_free(service, current, next_hour):
            free_slots.append(current.strftime("%H:%M"))
        current = next_hour

    return free_slots


def find_next_free_slot():
    tz = pytz.timezone(TIMEZONE)
    today = datetime.datetime.now(tz).date()

    for i in range(14):
        date = today + datetime.timedelta(days=i)
        free_today = get_free_slots_for_day(date)
        if free_today:
            return (date.strftime("%Y-%m-%d"), free_today[0])

    return None


def book_slot(name, company, date, time, phone):
    tz = pytz.timezone(TIMEZONE)
    start_dt = tz.localize(datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
    end_dt = start_dt + datetime.timedelta(hours=1)

    service = get_service()

    if not is_slot_free(service, start_dt, end_dt):
        return {"error": "Slot besetzt"}, 409

    event = {
        "summary": f"Termin: {name} ({company})",
        "description": f"Name: {name}\nUnternehmen: {company}\nTelefon: {phone}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
    }

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {"status": "success"}, 200


def delete_slot(name, date, time):
    tz = pytz.timezone(TIMEZONE)

    service = get_service()
    start_dt = tz.localize(datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))

    events = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start_dt.isoformat(),
            timeMax=(start_dt + datetime.timedelta(hours=1)).isoformat(),
            singleEvents=True,
        )
        .execute()
    )

    items = events.get("items", [])

    if not items:
        return {"error": "Nicht gefunden"}, 404

    target = None
    for e in items:
        if name.lower() in e.get("summary", "").lower():
            target = e
            break

    if not target:
        return {"error": "Name nicht gefunden"}, 404

    service.events().delete(calendarId=CALENDAR_ID, eventId=target["id"]).execute()
    return {"status": "deleted"}, 200
