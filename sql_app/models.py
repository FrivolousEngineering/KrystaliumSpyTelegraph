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
    morse: Mapped[str]
    text: Mapped[str]

    time_sent: Mapped[datetime]

    # Can be either "outgoing" (sent by players to somewhere) or "incoming" (So sent to the players)
    direction: Mapped[str]

    # In case of outgoing, where was the message sent to, in case of incoming, where was the message sent from

    target: Mapped[str]

    # Has the message been printed already? If it's None it hasn't been printed yet
    time_printed: Mapped[Optional[datetime]]

    # Human readable string to indicate who sent the message. This should only be used to indicate what SL sent
    # something to the players
    author: Mapped[Optional[str]]