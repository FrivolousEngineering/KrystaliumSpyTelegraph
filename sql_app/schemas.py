from datetime import datetime

from pydantic import BaseModel, Field, computed_field


class MessageBase(BaseModel):
    message_morse: str
    message_text: str
    message_direction: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    time_message_sent: datetime
