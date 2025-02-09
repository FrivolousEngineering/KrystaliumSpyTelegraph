from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Direction(str, Enum):
    incoming: str = "Incoming"
    outgoing: str = "Outgoing"


class MessageType(str, Enum):
    morse: str = "Morse"


class Target(str, Enum):
    fire_control: int = "FireControl"
    university: int = "University"
    central_intel: int = "CentralIntelligence"
    relay: int = "Relay"
    logistics: int = "Logistics"
    local_civilian: int = "LocalCivilian"
    long_range: int = "LongRange"

    @staticmethod
    def getIndex(value):
        return list(Target).index(value)


class MessageBase(BaseModel):
    text: str

    direction: Direction
    target: Target
    author: Optional[str] = Field(None, description="If a message is sent by GM, this should be filled in. Just there"
                                                    "for bookkeeping!")
    type: MessageType = "Morse"


class MessageCreate(MessageBase):
    text: Optional[str] = Field(None)


class Message(MessageBase):
    id: int
    time_sent: datetime
    time_printed: Optional[datetime]
    encoded_text: str


class GroupBase(BaseModel):
    name: str

class Group(GroupBase):
    id: int

class GroupCreate(GroupBase):
    pass

class BadRequestError(BaseModel):
    detail: str


class NotFoundError(BaseModel):
    detail: str
