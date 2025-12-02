from pydantic import BaseModel

class BookingRequest(BaseModel):
    name: str
    company: str
    date: str
    time: str
    phone: str

class DeletionRequest(BaseModel):
    name: str
    date: str
    time: str

class AvailabilityRequest(BaseModel):
    date: str

class BookedSlot(BaseModel):
    date: str
    time: str
