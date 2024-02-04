from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Direction(str, Enum):
    incoming: str = "Incoming"
    outgoing: str = "Outgoing"


class Target(str, Enum):
    fire_control: int = "FireControl"
    university: int = "University"
    central_intel: int = "CentralIntel"
    relay: int = "Relay"
    logistics: int = "Logistics"
    local_civilian: int = "LocalCivilian"
    long_range: int = "LongRange"

    @staticmethod
    def getIndex(value):
        return list(Target).index(value)


class MessageBase(BaseModel):
    text: str
    morse: str
    direction: Direction
    target: Target


class MessageCreate(MessageBase):
    morse: Optional[str] = Field(None, pattern=r"^[.\-\s]*$")  # Only allow ". -" characters
    text: Optional[str] = Field(None)


class Message(MessageBase):
    id: int
    time_sent: datetime
    time_printed: Optional[datetime]


class BadRequestError(BaseModel):
    detail: str


class NotFoundError(BaseModel):
    detail: str
