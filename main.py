# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from calendar_utils import (
    get_free_slots_for_day,
    find_next_free_slot,
    book_slot,
    delete_slot,
)

app = FastAPI()


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


class FreeDayRequest(BaseModel):
    date: str


@app.post("/book")
def api_book(req: BookingRequest):
    return book_slot(req.name, req.company, req.date, req.time, req.phone)


@app.post("/delete")
def api_delete(req: DeleteRequest):
    return delete_slot(req.name, req.date, req.time)


@app.post("/free-slots")
def api_free(req: FreeDayRequest):
    from datetime import datetime
    date_obj = datetime.strptime(req.date, "%Y-%m-%d").date()
    free = get_free_slots_for_day(date_obj)

    if not free:
        return {"free_slots": []}, 204

    return {"free_slots": free}, 200


@app.get("/next-free")
def api_next_free():
    result = find_next_free_slot()
    if not result:
        return {"next_slot": None}, 204

    date, time = result
    return {"next_slot": f"{date} {time}"}, 200
