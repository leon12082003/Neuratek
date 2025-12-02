from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from calendar_utils import (
    is_slot_free, book_appointment, delete_appointment,
    get_free_slots_for_day, get_next_free_slots
)
from config import CALENDAR_ID
from datetime import datetime

app = FastAPI()


class BookingRequest(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    name: str
    company: str
    phone: str


class AvailabilityRequest(BaseModel):
    date: str
    time: str


class DeleteRequest(BaseModel):
    date: str
    time: str
    name: str


class FreeSlotsRequest(BaseModel):
    date: str


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
        req.name,
        req.company,
        req.phone,
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
