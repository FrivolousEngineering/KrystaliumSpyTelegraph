import uuid

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/messages/", response_model=list[schemas.Message])
def get_all_messages(db: Session = Depends(get_db)):
    """
    Get all messages in the database
    """
    return crud.getAllMessages(db)
