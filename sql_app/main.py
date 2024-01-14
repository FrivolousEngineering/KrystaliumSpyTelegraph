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


@app.get("/messages/{message_id}/", response_model=schemas.Message, responses={404: {"model": schemas.NotFoundError}})
def get_message_by_id(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")
    return db_message


@app.post("/messages/{message_id}/reprint",
          responses={400: {"model": schemas.BadRequestError}, 404: {"model": schemas.NotFoundError}})
def reprint_message(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")

    if db_message.time_message_printed is None:
        raise HTTPException(status_code=400, detail=f"Can't reprint message as it's still waiting to be printed")

    crud.reprintMessage(message_id, db)


@app.post("/messages/{message_id}/mark_as_printed",
          responses={400: {"model": schemas.BadRequestError}, 404: {"model": schemas.NotFoundError}})
def mark_message_as_printed(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")

    crud.markMessageAsPrinted(message_id, db)


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
