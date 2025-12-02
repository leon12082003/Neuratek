from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from config import WORK_HOURS, CALENDAR_ID, APPOINTMENT_DURATION_MINUTES
import pytz
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'


def get_service():
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"[ERROR] Failed to load Google service account: {e}")
        raise


def is_slot_free(calendar_id, dt):
    try:
        service = get_service()
        tz = pytz.timezone("Europe/Berlin")
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        end_dt = dt + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)

        events = service.events().list(
            calendarId=calendar_id,
            timeMin=dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True
        ).execute()

        for event in events.get("items", []):
            event_start = event["start"].get("dateTime")
            event_end = event["end"].get("dateTime")
            if event_start and event_end:
                start_dt = datetime.fromisoformat(event_start)
                end_dt_expected = datetime.fromisoformat(event_end)
                if start_dt == dt and end_dt_expected == dt + timedelta(minutes=APPOINTMENT_DURATION_MINUTES):
                    return False
        return True
    except Exception as e:
        print(f"[ERROR] is_slot_free failed: {e}")
        raise


def book_appointment(calendar_id, dt, name, company=None, phone=None):
    try:
        if not is_slot_free(calendar_id, dt):
            return False

        service = get_service()
        tz = pytz.timezone("Europe/Berlin")
        if dt.tzinfo is None:
            dt = tz.localize(dt)

        # Summary nach Vorgabe:
        # "Telefontermin mit - {name} - von - {company} - unter ({phone})"
        summary_parts = [f"Telefontermin mit - {name}"]
        if company:
            summary_parts.append(f"- von - {company}")
        if phone:
            summary_parts.append(f"- unter ({phone})")
        summary = " ".join(summary_parts)

        description_lines = [
            f"Name: {name}",
            f"Unternehmen: {company or '-'}",
            f"Telefonnummer: {phone or '-'}",
            "Quelle: ElevenLabs Telefonassistent Neuratek",
        ]
        description = "\n".join(description_lines)

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': dt.isoformat(),
                'timeZone': 'Europe/Berlin'
            },
            'end': {
                'dateTime': (dt + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)).isoformat(),
                'timeZone': 'Europe/Berlin'
            },
        }

        service.events().insert(calendarId=calendar_id, body=event).execute()
        return True
    except Exception as e:
        print(f"[ERROR] book_appointment failed: {e}")
        raise


def delete_appointment(calendar_id, dt, name):
    try:
        service = get_service()
        tz = pytz.timezone("Europe/Berlin")
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        end_dt = dt + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)

        events = service.events().list(
            calendarId=calendar_id,
            timeMin=dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True
        ).execute()

        for event in events.get("items", []):
            if event.get("summary", "").lower() == name.lower():
                service.events().delete(
                    calendarId=calendar_id,
                    eventId=event["id"]
                ).execute()
                return True
        return False
    except Exception as e:
        print(f"[ERROR] delete_appointment failed: {e}")
        raise


def get_free_slots_for_day(calendar_id, date_str, after_time=None):
    try:
        print(f"[DEBUG] Checking free slots for: {date_str}")
        service = get_service()
        date = datetime.fromisoformat(date_str)
        weekday = date.strftime('%a').lower()
        start_time, end_time = WORK_HOURS.get(weekday, (None, None))
        if not start_time:
            return []

        tz = pytz.timezone("Europe/Berlin")
        start_dt = datetime.strptime(f"{date_str}T{start_time}", "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(f"{date_str}T{end_time}", "%Y-%m-%dT%H:%M")
        if start_dt.tzinfo is None:
            start_dt = tz.localize(start_dt)
        if end_dt.tzinfo is None:
            end_dt = tz.localize(end_dt)

        if after_time:
            after_dt = datetime.strptime(f"{date_str}T{after_time}", "%Y-%m-%dT%H:%M")
            if after_dt.tzinfo is None:
                after_dt = tz.localize(after_dt)
            if after_dt > start_dt:
                start_dt = after_dt

        free_slots = []
        while start_dt < end_dt:
            if is_slot_free(calendar_id, start_dt):
                free_slots.append(start_dt.strftime("%H:%M"))
            start_dt += timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
        return free_slots
    except Exception as e:
        print(f"[ERROR] get_free_slots_for_day failed: {e}")
        raise


def get_next_free_slots(calendar_id, count=3):
    try:
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        slots = []
        for i in range(14):  # 2 Wochen
            date = now + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            after_time = None
            if i == 0:
                # Runde auf nächste volle Stunde (bzw. nächste Slot-Grenze)
                minute = 0
                base = now.replace(minute=0, second=0, microsecond=0)
                if now.minute > 0:
                    base += timedelta(hours=1)
                after_time = base.strftime("%H:%M")

            slots_today = get_free_slots_for_day(calendar_id, date_str, after_time)
            for slot in slots_today:
                slots.append(f"{date_str} {slot}")
                if len(slots) == count:
                    return slots
        return slots
    except Exception as e:
        print(f"[ERROR] get_next_free_slots failed: {e}")
        raise
