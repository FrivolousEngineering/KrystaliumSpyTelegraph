from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)



tags_metadata = [
    {"name": "Messages", "description": ""},
    {"name": "Groups", "description": ""},
    {"name": "Encryption Keys", "description": ""},
]




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


@app.get("/messages/", response_model=list[schemas.Message], tags = ["Messages"])
def get_all_messages(db: Session = Depends(get_db)):
    """
    Get all messages in the database
    """
    return crud.getAllMessages(db)


@app.get("/messages/unprinted/", response_model=list[schemas.Message], tags = ["Messages"])
def get_all_unprinted_messages(db: Session = Depends(get_db)):
    """
    Get all messages in the database
    """
    return crud.getAllUnprintedMessages(db)


@app.get("/messages/{message_id}/", response_model=schemas.Message, responses={404: {"model": schemas.NotFoundError}}, tags = ["Messages"])
def get_message_by_id(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")
    return db_message


@app.post("/messages/{message_id}/reprint",
          responses={400: {"model": schemas.BadRequestError}, 404: {"model": schemas.NotFoundError}}, tags = ["Messages"])
def reprint_message(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")

    if db_message.time_printed is None:
        raise HTTPException(status_code=400, detail=f"Can't reprint message as it's still waiting to be printed")

    crud.reprintMessage(message_id, db)


@app.post("/messages/{message_id}/mark_as_printed",
          responses={400: {"model": schemas.BadRequestError}, 404: {"model": schemas.NotFoundError}}, tags = ["Messages"])
def mark_message_as_printed(message_id: int, db: Session = Depends(get_db)):
    db_message = crud.getMessageById(message_id, db)
    if not db_message:
        raise HTTPException(status_code=404, detail=f"Message with ID [{message_id}] was not found")

    crud.markMessageAsPrinted(message_id, db)


@app.post("/messages/", response_model=schemas.Message, responses={400: {"model": schemas.BadRequestError}}, tags = ["Messages"])
def postMessage(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    return crud.createMessage(db, message)


@app.post("/groups/", response_model=schemas.Group, tags = ["Groups"])
def postGroup(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(group.name, db)
    if db_group:
        raise HTTPException(status_code=400, detail=f"Group with name [{group.name}] already exists")
    return crud.createGroup(group, db)


@app.get("/groups/", response_model=list[schemas.Group], tags = ["Groups"])
def getGroups(db: Session = Depends(get_db)):
    return crud.getAllGroups(db)

@app.get("/groups/{group_name}", response_model=schemas.Group, tags = ["Groups"])
def getGroupByName(group_name:str, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(group_name, db)
    if not db_group:
        raise HTTPException(status_code=404, detail=f"Group with name '{group_name}' doesn't exist")
    return db_group

@app.post("/groups/{group_name}/encryption_key/{key_type}", response_model=schemas.EncryptionKey, tags = ["Groups", "Encryption Keys"])
def createNewEncryptionKeyForGroup(group_name: str, key_type: str, db: Session = Depends(get_db)):
    db_group = crud.getGroupByName(group_name, db)
    if not db_group:
        raise HTTPException(status_code=404, detail=f"Group with name '{group_name}' doesn't exist")

    if not key_type in ["row", "row-plow", "skip", "skip-plow"]:
        raise HTTPException(status_code=400, detail=f"Encryption key {key_type} is unknown.")

    return crud.createEncryptionKeyForGroup(group_name, key_type, db)
    pass

@app.get("/encryption_keys/", response_model=list[schemas.EncryptionKey], tags = ["Encryption Keys"])
def getEncryptionKeys(db: Session = Depends(get_db)):
    return crud.getAllEncryptionKeys(db)