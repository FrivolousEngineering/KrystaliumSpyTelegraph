from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, computed_field


class Direction(str, Enum):
    incoming: str = "Incoming"
    outgoing: str = "Outgoing"


class EncryptionType(str, Enum):
    morse: str = "morse"
    row: str = "row"
    row_plow: str = "row-plow"
    skip: str = "skip"
    skip_plow: str = "skip-plow"

    @staticmethod
    def getIndex(value):
        return list(EncryptionType).index(value)



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
    type: EncryptionType = "morse"


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

    class Config:
        orm_mode = True

class GroupCreate(GroupBase):
    pass


class EncryptionKeyBase(BaseModel):
    key: List[int]
    group_id: int
    encryption_type: EncryptionType

class EncryptionKey(EncryptionKeyBase):
    id: int
    group: Group  # Nested group information

    class Config:
        orm_mode = True

class EncryptionKeyCreate(EncryptionKeyBase):
    pass

class BadRequestError(BaseModel):
    detail: str


class NotFoundError(BaseModel):
    detail: str
