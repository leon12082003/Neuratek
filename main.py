
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from calendar_utils import get_free_slots_for_day, find_next_free_slot, service, CALENDAR_ID, tz

app = FastAPI()

class CheckRequest(BaseModel):
    date: str
    time: str

class BookRequest(BaseModel):
    name: str
    company: str
    phone: str
    date: str
    time: str

class DeleteRequest(BaseModel):
    name: str
    date: str
    time: str

@app.post("/check-availability")
def check_availability(req: CheckRequest):
    dt = tz.localize(datetime.strptime(f"{req.date} {req.time}", "%Y-%m-%d %H:%M"))
    free = get_free_slots_for_day(CALENDAR_ID, req.date)
    if dt.isoformat() in free:
        return {"available": True}
    raise HTTPException(status_code=409, detail="Slot not available")

@app.post("/book")
def book(req: BookRequest):
    dt = tz.localize(datetime.strptime(f"{req.date} {req.time}", "%Y-%m-%d %H:%M"))
    if not is_slot_free(CALENDAR_ID, dt):
        raise HTTPException(status_code=409, detail="Slot already taken")
    event = {
        'summary': f"{req.name} ({req.company})",
        'description': f"Telefon: {req.phone}",
        'start': {'dateTime': dt.isoformat(), 'timeZone': tz.zone},
        'end': {'dateTime': (dt + timedelta(minutes=60)).isoformat(), 'timeZone': tz.zone},
    }
    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {"booked": True}

@app.post("/delete")
def delete(req: DeleteRequest):
    dt = tz.localize(datetime.strptime(f"{req.date} {req.time}", "%Y-%m-%d %H:%M"))
    events = service.events().list(calendarId=CALENDAR_ID, timeMin=dt.isoformat(), timeMax=(dt + timedelta(hours=1)).isoformat()).execute().get("items", [])
    for event in events:
        if req.name.lower() in event.get("summary", "").lower():
            service.events().delete(calendarId=CALENDAR_ID, eventId=event["id"]).execute()
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="No matching event found")

@app.post("/free-slots")
def free_slots(req: CheckRequest):
    slots = get_free_slots_for_day(CALENDAR_ID, req.date)
    if not slots:
        raise HTTPException(status_code=404, detail="No free slots")
    return {"free_slots": slots}

@app.get("/next-free-slot")
def next_free_slot():
    next_slot = find_next_free_slot(CALENDAR_ID)
    return {"next_free_slot": next_slot}
