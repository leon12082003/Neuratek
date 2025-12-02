from fastapi import FastAPI, HTTPException
from config import BookingRequest, DeletionRequest, AvailabilityRequest, BookedSlot
from calendar_utils import book_appointment, delete_appointment, get_free_slots, get_next_available_slot, check_availability

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Neuratek Calendar Middleware is running."}


@app.post("/check-availability")
def check_avail(data: BookingRequest):
    if check_availability(data.date, data.time):
        return {"available": True}
    raise HTTPException(status_code=409, detail="Slot not available")


@app.post("/book")
def book(data: BookingRequest):
    success = book_appointment(data.name, data.company, data.date, data.time, data.phone)
    if success:
        return {"success": True}
    raise HTTPException(status_code=409, detail="Booking failed. Slot might already be taken.")


@app.post("/delete")
def delete(data: DeletionRequest):
    success = delete_appointment(data.name, data.date, data.time)
    if success:
        return {"success": True}
    raise HTTPException(status_code=404, detail="Appointment not found")


@app.post("/free-slots")
def free_slots(data: AvailabilityRequest):
    slots = get_free_slots(data.date)
    if slots:
        return {"date": data.date, "free_slots": slots}
    raise HTTPException(status_code=404, detail="No free slots available on this day")


@app.get("/next-free")
def next_free():
    slot = get_next_available_slot()
    return slot or {"message": "No free slots in the next 30 days"}
