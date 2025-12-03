from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from calendar_utils import (
    is_slot_free, book_appointment, delete_appointment,
    get_free_slots_for_day, get_next_free_slots
)
from config import CALENDAR_ID
from twilio.rest import Client
import os

app = FastAPI()


# ---------- Models ----------

class BookingRequest(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    name: str
    company: str | None = None
    phone: str | None = None


class AvailabilityRequest(BaseModel):
    date: str
    time: str


class DeleteRequest(BaseModel):
    date: str
    time: str
    name: str


class FreeSlotsRequest(BaseModel):
    date: str  # YYYY-MM-DD


class SmsRequest(BaseModel):
    to: str      # Ziel-Nummer im Format +49...
    text: str    # SMS-Text


# ---------- Google Calendar Endpoints ----------

@app.post("/check-availability")
def check_availability(req: AvailabilityRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    available = is_slot_free(CALENDAR_ID, dt)
    if not available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot not available"
        )
    return {"available": True}


@app.post("/book")
def book(req: BookingRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    success = book_appointment(
        CALENDAR_ID,
        dt,
        name=req.name,
        company=req.company,
        phone=req.phone
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot already booked"
        )
    return {"status": "booked"}


@app.post("/delete")
def delete(req: DeleteRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    success = delete_appointment(CALENDAR_ID, dt, req.name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return {"status": "deleted"}


@app.post("/free-slots")
def free_slots(req: FreeSlotsRequest):
    free = get_free_slots_for_day(CALENDAR_ID, req.date)
    if not free:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No free slots"
        )
    return {"free_slots": free}


@app.get("/next-free")
def next_free():
    slots = get_next_free_slots(CALENDAR_ID)
    return {"next_slots": slots}


# ---------- Twilio Helper ----------

def get_twilio_client() -> Client:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials missing in environment variables.")
    return Client(account_sid, auth_token)


# ---------- SMS Endpoint ----------

@app.post("/send-sms")
def send_sms(req: SmsRequest):
    """
    Sendet eine SMS über Twilio. Wird von ElevenLabs aufgerufen,
    nachdem der Kunde einer SMS-Bestätigung zugestimmt hat.
    """
    try:
        from_number = os.getenv("TWILIO_FROM_NUMBER")
        if not from_number:
            raise RuntimeError("TWILIO_FROM_NUMBER is not set.")

        client = get_twilio_client()

        message = client.messages.create(
            body=req.text,
            from_=from_number,
            to=req.to
        )

        return {"status": "sent", "sid": message.sid}
    except Exception as e:
        print(f"[ERROR] send_sms failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS"
        )
