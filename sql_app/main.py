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


@app.get("/unprinted_messages/", response_model=list[schemas.Message])
def get_all_unprinted_messages(db: Session = Depends(get_db)):
    """
    Get all messages in the database
    """
    return crud.getAllUnprintedMessages(db)


@app.post("/messages/", response_model=schemas.Message, responses={400: {"model": schemas.BadRequestError}})
def postMessage(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    if message.message_morse is not None and message.message_text is not None:
        raise HTTPException(status_code=400, detail=f"Can't set morse and text at the same time!")
    return crud.createMessage(db, message)
