from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, registry, relationship

from .database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key = True, index = True)

    # Text contains the "real" message
    text: Mapped[str]

    # Encoded text contains the cyphered text (where morse is considered a cypher!)
    encoded_text: Mapped[str]

    time_sent: Mapped[datetime]

    # Can be either "outgoing" (sent by players to somewhere) or "incoming" (So sent to the players)
    direction: Mapped[str]

    type: Mapped[str]

    # In case of outgoing, where was the message sent to, in case of incoming, where was the message sent from
    target: Mapped[str]

    # Has the message been printed already? If it's None it hasn't been printed yet
    time_printed: Mapped[Optional[datetime]]

    # Human-readable string to indicate who sent the message. This should only be used to indicate what SL sent
    # something to the players
    author: Mapped[Optional[str]]


class EncryptionGroup(Base):
    """
    This is to keep track of what players have what keys.
    A group will have at least a single player in it and has a
    number of EncryptionKeys associated with it.
    """
    __tablename__ = "encryption_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True) # Human-readable name of the group (eg: "Spies", "Double-agents")

    # Link to a list of EncryptionKeys that belong to this group.
    encryption_keys: Mapped[List["EncryptionKey"]] = relationship(
        "EncryptionKey", back_populates="group", cascade="all, delete-orphan"
    )


class EncryptionKey(Base):
    """
    A single encryption key.
    """
    __tablename__ = "encryption_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # There are several encryption types. Which of the types is it?
    encryption_type: Mapped[str] = mapped_column(String)

    # What is the actual key
    key: Mapped[List[int]] = mapped_column(JSON)

    # Foreign key linking this key to a specific encryption group.
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("encryption_groups.id"))

    # Link back to the parent group.
    group: Mapped["EncryptionGroup"] = relationship("EncryptionGroup", back_populates="encryption_keys")