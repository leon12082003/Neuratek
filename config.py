import os
import json
from google.oauth2 import service_account

# Lade die Google Credentials aus der Umgebungsvariable
service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/calendar"]
)

# Kalender-ID – hier bitte nichts ändern
CALENDAR_ID = "neuratek-calendar-service@neuratek-479922.iam.gserviceaccount.com"

# Öffnungszeiten (keine Slots außerhalb dieser Zeiten)
OPENING_HOURS = {
    "monday":    {"start": "08:00", "end": "18:00"},
    "tuesday":   {"start": "08:00", "end": "18:00"},
    "wednesday": {"start": "08:00", "end": "18:00"},
    "thursday":  {"start": "08:00", "end": "18:00"},
    "friday":    {"start": "08:00", "end": "18:00"},
    "saturday":  {"start": "10:00", "end": "14:00"},
    "sunday":    {"start": "10:00", "end": "14:00"},
}

# Slot-Dauer in Minuten
SLOT_DURATION_MINUTES = 60

# Kein Versatz zwischen Terminen
SLOT_PADDING_MINUTES = 0

# Pflichtangaben für Buchungen
REQUIRED_FIELDS = ["name", "company", "date", "time", "phone"]

# Zeitzone – gebraucht in calendar_utils
TIMEZONE = "Europe/Berlin"
