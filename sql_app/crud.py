from sqlalchemy.orm import Session
from . import models, schemas


def getAllMessages(db: Session):
    return db.query(models.Message).all()
