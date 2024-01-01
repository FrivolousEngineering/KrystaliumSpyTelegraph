from sqlalchemy import Column, Integer, String, DateTime

from .database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    # Perhaps a bit redundant to store both. But storage really isn't an issue, so we might as well.
    message_morse = Column(String)
    message_text = Column(String)

    time_message_sent = Column(DateTime)

    # Can be either "outgoing" (sent by players to somewhere) or "incoming" (So sent to the players)
    message_direction = Column(String)
