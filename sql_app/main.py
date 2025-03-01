from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from GridBasedEncryption import EncryptionGrid
from . import crud, models, schemas
from .database import SessionLocal, engine
import random

from .schemas import EncryptionKeyCreate

models.Base.metadata.create_all(bind=engine)

import logging

tags_metadata = [
    {"name": "Messages", "description": ""},
    {"name": "Groups", "description": ""},
    {"name": "Encryption Keys", "description": ""},
]

logger = logging.getLogger('uvicorn.error')

# Mount the swagger & redoc stuff locally.
app = FastAPI(docs_url=None, redoc_url=None, openapi_tags=tags_metadata)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    # This function is required to locally host the swagger API. This means that the docs will work without internet
    # connection
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    # This function is required to locally host the swagger API. This means that the docs will work without internet
    # connection
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    # This function is required to locally host the swagger API. This means that the docs will work without internet
    # connection
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/messages/", response_model=list[schemas.Message], tags=["Messages"])
def get_all_messages(db: Session = Depends(get_db)):
    """
    Get all messages in the database
    """
    return crud.getAllMessages(db)





@app.get("/messages/unprinted/", response_model=list[schemas.Message], tags=["Messages"])
def get_all_unprinted_messages(db: Session = Depends(get_db)):
    """
    Get all messages in the database
    """
    return crud.getAllUnprintedMessages(db)


@app.get("/messages/{message_id}/", response_model=schemas.Message, responses={404: {"model": schemas.NotFoundError}},
         tags=["Messages"])
def get_message_by_id(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")
    return db_message


@app.delete("/messages/{message_id}/", responses = {404: {"model": schemas.NotFoundError}},
            tags = ["Messages"])
def delete_message_by_id(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")
    crud.deleteMessageById(message_id, db)

@app.post("/messages/{message_id}/reprint",
          responses={400: {"model": schemas.BadRequestError}, 404: {"model": schemas.NotFoundError}}, tags=["Messages"])
def reprint_message(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")

    if db_message.time_printed is None:
        raise HTTPException(status_code=400, detail=f"Can't reprint message as it's still waiting to be printed")

    crud.reprintMessage(message_id, db)


@app.post("/messages/{message_id}/mark_as_printed",
          responses={400: {"model": schemas.BadRequestError}, 404: {"model": schemas.NotFoundError}}, tags=["Messages"])
def mark_message_as_printed(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")

    crud.markMessageAsPrinted(message_id, db)


def _handleGridMessage(grid_msg: schemas.GridMessage, db: Session):
    # Check primary group exists.
    primary_group = crud.getGroupByName(grid_msg.primary_group, db)
    if not primary_group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with name '{grid_msg.primary_group}' doesn't exist"
        )

    # If secondary_group is provided, check it exists.
    secondary_group = None
    if grid_msg.secondary_group:
        secondary_group = crud.getGroupByName(grid_msg.secondary_group, db)
        if not secondary_group:
            raise HTTPException(
                status_code=404,
                detail=f"Group with name '{grid_msg.secondary_group}' doesn't exist"
            )

    # Retrieve and shuffle keys for primary (and secondary if applicable)
    all_primary_group_keys = crud.getAllEncryptionKeysByGroup(primary_group.name, db)
    random.shuffle(all_primary_group_keys)

    if secondary_group:
        all_secondary_group_keys = crud.getAllEncryptionKeysByGroup(secondary_group.name, db)
        random.shuffle(all_secondary_group_keys)
    else:
        all_secondary_group_keys = []

    estimated_rows_needed = max(len(grid_msg.primary_message), len(grid_msg.secondary_message))

    # About 10% of row messages is "skip this row" so make the entire thing a tad bit longer
    estimated_rows_needed *= 1.15
    estimated_rows_needed = int(estimated_rows_needed)
    grid = EncryptionGrid(10, estimated_rows_needed)
    primary_key_id = None
    primary_encryption_type = ""
    primary_key = []
    secondary_key_id = None
    secondary_key = []
    secondary_encryption_type = ""

    is_successful = False

    for primary_encryption_key in all_primary_group_keys:

        primary_key_id = primary_encryption_key.id
        primary_key = primary_encryption_key.key
        primary_encryption_type = primary_encryption_key.encryption_type
        try:
            grid.addMessage(
                primary_encryption_key.encryption_type,
                grid_msg.primary_message,
                primary_encryption_key.key
            )
        except Exception as e:
            logger.error(f"failed to add for {primary_encryption_key.encryption_type}: {e}")
            continue
        is_successful = True
        if not grid_msg.secondary_message:
            break  # No secondary message; use current grid.

        secondary_message_added = False
        for secondary_encryption_key in all_secondary_group_keys:
            secondary_key_id = secondary_encryption_key.id
            secondary_key = secondary_encryption_key.key
            secondary_encryption_type = secondary_encryption_key.encryption_type
            try:
                grid.addMessage(
                    secondary_encryption_key.encryption_type,
                    grid_msg.secondary_message,
                    secondary_encryption_key.key
                )
            except Exception:
                continue
            secondary_message_added = True
            break

        if secondary_message_added:
            break
        else:
            # Reset grid and try the next primary key.
            grid = EncryptionGrid(10, estimated_rows_needed)
            is_successful = False

    # Debug prints to check if the encoding went well
    logger.info(
        f"Attempting to decode primary message encoded with {primary_encryption_type} and key {primary_key}: {grid.decodeMethod(primary_encryption_type, primary_key)}")
    if secondary_encryption_type:
        logger.info(
            f"Attempting to decode Secondary message encoded with {secondary_encryption_type} and key {secondary_key}: {grid.decodeMethod(secondary_encryption_type, secondary_key)}")

    if not is_successful:
        raise HTTPException(
            status_code=400,
            detail=f"Could not encode provided messages with any combination. Consider changing the message or making them shorter"
        )

    # Flatten the grid into text.
    flat_grid_text = "\n".join(" ".join(row) for row in grid.getRawGrid())
    # Create and return the grid message.
    return crud.createGridMessage(
        db,
        grid_msg.primary_message,
        grid_msg.secondary_message,
        flat_grid_text,
        grid_msg.target,
        grid_msg.author
    )


@app.post("/messages/", response_model=schemas.Message, responses={400: {"model": schemas.BadRequestError}},
          tags=["Messages"])
def post_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    if message.type == schemas.MessageType.morse:
        # Call your existing plain message creation logic.
        return crud.createMessage(db, message)

    elif message.type == schemas.MessageType.grid:
        return _handleGridMessage(message, db)
    else:
        # Should never get here because the union is discriminated by "type".
        raise HTTPException(status_code=400, detail="Invalid message type")


@app.post("/groups/", response_model=schemas.Group, tags=["Groups"])
def postGroup(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(group.name, db)
    if db_group:
        raise HTTPException(status_code=400, detail=f"Group with name [{group.name}] already exists")
    return crud.createGroup(group, db)


@app.get("/groups/", response_model=list[schemas.Group], tags=["Groups"])
def getGroups(db: Session = Depends(get_db)):
    return crud.getAllGroups(db)


@app.get("/groups/{group_name}", response_model=schemas.Group, tags=["Groups"])
def getGroupByName(group_name: str, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(group_name, db)
    if not db_group:
        raise HTTPException(status_code=404, detail=f"Group with name '{group_name}' doesn't exist")
    return db_group


@app.post("/groups/{group_name}/encryption_key/{key_type}", response_model=schemas.EncryptionKey,
          tags=["Groups", "Encryption Keys"])
def createNewEncryptionKeyForGroup(group_name: str, key_type: str, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(group_name, db)
    if not db_group:
        raise HTTPException(status_code=404, detail=f"Group with name '{group_name}' doesn't exist")

    if not key_type in ["row", "row-plow", "skip", "skip-plow"]:
        raise HTTPException(status_code=400, detail=f"Encryption key {key_type} is unknown.")

    return crud.createEncryptionKeyForGroup(group_name, key_type, db)
    pass


@app.get("/encryption_keys/", response_model=list[schemas.EncryptionKey], tags=["Encryption Keys"])
def getEncryptionKeys(db: Session = Depends(get_db)):
    return crud.getAllEncryptionKeys(db)



@app.post("/encryption_keys")
def postEncryptionKey(key: EncryptionKeyCreate, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(key.group_name, db)
    if not db_group:
        raise HTTPException(status_code=404, detail=f"Group with name '{key.group_name}' doesn't exist")
    return crud.createEncryptionKey(key, db)
    pass