from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, registry, relationship

from .database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key = True, index = True)

    # Perhaps a bit redundant to store both. But storage really isn't an issue, so we might as well.
    message_morse: Mapped[str]
    message_text: Mapped[str]

    time_message_sent: Mapped[datetime]

    # Can be either "outgoing" (sent by players to somewhere) or "incoming" (So sent to the players)
    message_direction: Mapped[str]

    # Has the message been printed already? If it's None it hasn't been printed yet
    time_message_printed: Mapped[Optional[datetime]]
