from typing import Optional, List

from sqlalchemy.orm import Session

from MorseTranslator import MorseTranslator
from . import models, schemas

from datetime import datetime
import random
# Some hardcoded stuff regarding encryption. I know, not the greatest. Sue me
grid_width = 10
min_code_length = 6
max_code_length = 10
max_skip_value = 9

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


def createGridMessage(db: Session, primary_text, secondary_text, flat_grid_text: str, target: str) -> models.Message:

    # Since these are only sent *to* the players, ive hardcoded it
    db_message = models.Message(type="Grid", text=primary_text, secondary_text=secondary_text, encoded_text = flat_grid_text, direction = "incomming", target = target)

    db_message.time_sent = datetime.now()
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def getGroupByName(group_name: str, db: Session) -> Optional[models.EncryptionGroup]:
    return db.query(models.EncryptionGroup).filter(models.EncryptionGroup.name == group_name).first()

def getAllGroups(db: Session) -> List[models.EncryptionGroup]:
    return db.query(models.EncryptionGroup).all()


def createGroup(group: schemas.GroupCreate, db: Session) -> models.EncryptionGroup:
    db_group = models.EncryptionGroup(**group.__dict__)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def getAllEncryptionKeys(db: Session) -> List[models.EncryptionKey]:
    return db.query(models.EncryptionKey).all()


def getAllEncryptionKeysByGroup(group_name: str, db: Session) -> List[models.EncryptionKey]:
    return (
        db.query(models.EncryptionKey)
        .filter(models.EncryptionKey.group_id == getGroupByName(group_name, db).id)
        .all()
    )

def createEncryptionKeyForGroup(group_name: str, encryption_type: str, db: Session) -> models.EncryptionKey:
    group = getGroupByName(group_name, db)
    if not group:
        raise Exception(f"Group with name '{group_name}' doesn't exist")

    # TODO: Actually figure out a key that works. Now it's just hardcoded to be a specific one
    key_to_use = []
    while True:
        key_to_use = generateRandomKey(encryption_type)
        if validateKeyIsUnique(encryption_type, key_to_use, db):
            break
        else:
            print("key wasn't unique, trying again!")
    encryption_key = models.EncryptionKey(group_id=group.id, encryption_type=encryption_type, key=key_to_use)
    db.add(encryption_key)
    db.commit()
    db.refresh(encryption_key)
    return encryption_key


def generateRandomKey(encryption_type: str) -> List[int]:
    key_length = random.randint(min_code_length, max_code_length)
    if "row" in encryption_type:
        key = [random.randint(0, grid_width) for _ in range(key_length)]
    else:
        # Skip encryption!
        key = [random.randint(0, max_skip_value) for _ in range(key_length)]

    return key

def validateKeyIsUnique(encryption_type: str, key: List[int], db: Session):
    # So we first get all existing encryption keys with the same encryption type
    all_keys = db.query(models.EncryptionKey).filter(models.EncryptionKey.encryption_type == encryption_type).all()

    for encryption_key in all_keys:
        if encryption_key.key == key:
            return False

    return True