from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

# --- Google Calendar Setup ---

# Entweder Credentials als JSON-String in der ENV-Variable GOOGLE_SERVICE_ACCOUNT_JSON
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    """
    Initialisiert den Google-Calendar-Service über Service Account.
    Entweder aus GOOGLE_SERVICE_ACCOUNT_JSON oder aus service_account.json.
    """
    if SERVICE_ACCOUNT_JSON:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
    else:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    service = build("calendar", "v3", credentials=creds)
    return service


DEFAULT_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")


# --- Request-Modell von ElevenLabs ---


class ScheduleRequest(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    topic: Optional[str] = None
    notes: Optional[str] = None
    # ISO 8601, z. B. "2025-12-05T09:00:00+01:00"
    start: str
    end: str
    timezone: str = "Europe/Berlin"


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/schedule-meeting")
def schedule_meeting(payload: ScheduleRequest):
    """
    Wird von ElevenLabs als Tool/Webhook aufgerufen.
    Erstellt einen Termin im Google-Kalender und gibt Basisinfos zurück.
    """
    try:
        service = get_calendar_service()

        summary = f"Neuratek KI-Beratung: {payload.name}"
        description_lines = [
            f"Name: {payload.name}",
            f"Firma: {payload.company or '-'}",
            f"Telefon: {payload.phone or '-'}",
            f"E-Mail: {payload.email or '-'}",
            f"Branche: {payload.industry or '-'}",
            f"Anliegen/Thema: {payload.topic or '-'}",
            f"Notizen (aus Gespräch): {payload.notes or '-'}",
        ]
        description = "\n".join(description_lines)

        event_body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": payload.start,
                "timeZone": payload.timezone,
            },
            "end": {
                "dateTime": payload.end,
                "timeZone": payload.timezone,
            },
        }

        event = (
            service.events()
            .insert(calendarId=DEFAULT_CALENDAR_ID, body=event_body)
            .execute()
        )

        return {
            "status": "ok",
            "event_id": event.get("id"),
            "html_link": event.get("htmlLink"),
            "start": event.get("start"),
            "end": event.get("end"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
