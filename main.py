from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from calendar_utils import (
    get_free_slots,
    book_appointment,
    delete_appointment,
    get_next_available_slot,
    check_availability
)

app = FastAPI()


class SlotRequest(BaseModel):
    date: str


class BookingRequest(BaseModel):
    name: str
    company: str
    date: str
    time: str
    phone: str


class DeleteRequest(BaseModel):
    name: str
    date: str
    time: str


@app.post("/free-slots")
def free_slots(request: SlotRequest):
    try:
        return get_free_slots(request.date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/book")
def book(request: BookingRequest):
    try:
        result = book_appointment(request.name, request.company, request.date, request.time, request.phone)
        if result:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=409, detail="Slot already booked or invalid.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delete")
def delete(request: DeleteRequest):
    try:
        result = delete_appointment(request.name, request.date, request.time)
        if result:
            return {"status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="Appointment not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/next-free")
def next_free():
    try:
        slot = get_next_available_slot()
        if slot:
            return {"next_slot": slot}
        else:
            raise HTTPException(status_code=404, detail="No free slots available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-availability")
def check(request: BookingRequest):
    try:
        available = check_availability(request.date, request.time)
        return {"available": available}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
