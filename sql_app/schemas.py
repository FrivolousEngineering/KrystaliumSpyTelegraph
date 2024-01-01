from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Direction(str, Enum):
    incoming: str = "Incoming"
    outgoing: str = "Outgoing"


class MessageBase(BaseModel):
    message_text: str
    message_morse: str
    message_direction: Direction


class MessageCreate(MessageBase):
    message_morse: Optional[str] = Field(None, pattern=r"^[.\-\s]*$")  # Only allow ". -" characters
    message_text: Optional[str] = Field(None)


class Message(MessageBase):
    id: int
    time_message_sent: datetime


class BadRequestError(BaseModel):
    error_message: str
