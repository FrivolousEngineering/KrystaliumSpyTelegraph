from sqlalchemy.orm import Session

from MorseTranslator import MorseTranslator
from . import models, schemas

from datetime import datetime


def getAllMessages(db: Session):
    return db.query(models.Message).all()


def createMessage(db: Session, message: schemas.MessageCreate) -> models.Message:
    db_message = models.Message(**message.__dict__)
    db_message.time_message_sent = datetime.now()

    if db_message.message_text:
        db_message.message_morse = MorseTranslator.textToMorse(db_message.message_text)
    else:
        db_message.message_text = MorseTranslator.morseToText(db_message.message_morse)

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
