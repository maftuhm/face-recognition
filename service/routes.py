from http.client import HTTPException
from io import BytesIO
from typing import List
from PIL import Image
from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.orm import Session

from .database import Base, engine, SessionLocal
from .controllers import EngineController

Base.metadata.create_all(bind=engine)

router = APIRouter()
controller = EngineController()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.on_event('startup')
def load_model():
    controller.load_model()


def open_image(contents):
    image = Image.open(BytesIO(contents))

    if image.mode != 'RGB':
        image = image.convert('RGB')

    image.thumbnail((640, 640))

    return image


async def upload_files(files: List[UploadFile]):
    images = []
    for file in files:
        contents = await file.read()
        image = open_image(contents)
        images.append(image)

    return images


@router.post("/register")
async def register_face(name: str, files: List[UploadFile] = File(...), session: Session = Depends(get_db)):
    try:
        images = await upload_files(files)
        response = controller.register_face(session, name, images)
        return response
    except Exception as e:
        raise HTTPException(e)


@router.post("/recognize")
async def recognize_face(file: UploadFile = File(...), session: Session = Depends(get_db)):
    try:
        contents = await file.read()
        image = open_image(contents)
        response = controller.recognize(session, image)
        return response
    except Exception as e:
        raise HTTPException(e)
