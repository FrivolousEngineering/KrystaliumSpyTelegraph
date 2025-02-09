from typing import Optional, List

from sqlalchemy.orm import Session

from MorseTranslator import MorseTranslator
from . import models, schemas

from datetime import datetime


def getAllMessages(db: Session):
    return db.query(models.Message).all()


def getMessageById(message_id: int, db: Session) -> Optional[models.Message]:
    return db.query(models.Message).filter(models.Message.id == message_id).first()


def getAllUnprintedMessages(db: Session) -> List[models.Message]:
    return db.query(models.Message).filter(models.Message.time_printed == None)


def reprintMessage(message_id: int, db: Session):
    db_message = getMessageById(message_id, db)
    db_message.time_printed = None
    db.commit()


def markMessageAsPrinted(message_id: int, db: Session):
    db_message = getMessageById(message_id, db)
    db_message.time_printed = datetime.now()
    db.commit()


def createMessage(db: Session, message: schemas.MessageCreate) -> models.Message:
    db_message = models.Message(**message.__dict__)
    db_message.time_sent = datetime.now()
    if db_message.type == "Morse":
        db_message.encoded_text = MorseTranslator.textToMorse(db_message.text)
    else:
        print("UNKNOWN TYPE!")

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def getGroupByName(group_name: str, db: Session) -> Optional[models.EncryptionGroup]:
    return db.query(models.EncryptionGroup).filter(models.EncryptionGroup.name == group_name).first()



def createGroup(group: schemas.GroupCreate, db: Session) -> models.EncryptionGroup:
    db_group = models.EncryptionGroup(**group.__dict__)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group