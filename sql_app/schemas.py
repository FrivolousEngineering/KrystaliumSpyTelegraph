from datetime import datetime
from enum import Enum
from typing import Optional, List, Literal, Union

from pydantic import BaseModel, Field, computed_field


class Direction(str, Enum):
    incoming: str = "Incoming"
    outgoing: str = "Outgoing"

class MessageType(str, Enum):
    morse: str = "morse"
    grid: str = "grid"

class EncryptionType(str, Enum):
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
    direction: Direction
    target: Target
    author: Optional[str] = Field(None, description="If a message is sent by GM, this should be filled in. Just there"
                                                    "for bookkeeping!")

class MorseMessage(MessageBase):
    type: Literal[MessageType.morse] = MessageType.morse
    text: str


# Message intended for grid (encrypted) messages
class GridMessage(MessageBase):
    type: Literal[MessageType.grid] = MessageType.grid
    primary_message: str  # The decoded primary message
    primary_group: str    # Name of the group that should be able to read it
    secondary_message: Optional[str] = Field(
        None, description="Optional secondary hidden message"
    )
    secondary_group: Optional[str] = Field(
        None, description="If set, must be an existing group"
    )


# A discriminated union
MessageCreate = Union[GridMessage, MorseMessage]

class Message(MessageBase):
    id: int
    time_sent: datetime
    time_printed: Optional[datetime]
    encoded_text: str


class createEncryptedMessage(BaseModel):
    primary_message: str  # The actual message that is the result of decoding something
    primary_group: str  # What group needs to be able to read the message? This is the *name* of that group!
    secondary_message: Optional[str] = Field(None) # Optional secondary "hidden" message that is encoded next to the real message (SNEAAAKYYYY)
    secondary_group: Optional[str] = Field(None) # Who needs to be able to read this??
    target: Target
    author: Optional[str] = Field(None, description="If a message is sent by GM, this should be filled in. Just there"
                                                    "for bookkeeping!")

class Message(MessageBase):
    id: int
    time_sent: datetime
    time_printed: Optional[datetime]
    encoded_text: str
    text: str
    secondary_text: Optional[str]
    type: str


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
