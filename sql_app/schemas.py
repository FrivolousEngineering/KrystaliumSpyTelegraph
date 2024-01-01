from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class Direction(str, Enum):
    incoming: str = "Incoming"
    outgoing: str = "Outgoing"


class MessageBase(BaseModel):
    message_text: str
    message_direction: Direction


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    message_morse: str
    time_message_sent: datetime


class BadRequestError(BaseModel):
    error_message: str
