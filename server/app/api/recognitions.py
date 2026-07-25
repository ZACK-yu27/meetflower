"""1.1 识花：POST /api/v1/recognitions（multipart/form-data，字段 image，jpg/png ≤10MB）；
GET /api/v1/recognitions/{id}（轮询：ark 模式科普文案异步补齐后 science_text 非空）。"""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..schemas import RecognitionOut
from ..services import recognition as recognition_service
from ..sessions import resolve_garden_id

router = APIRouter(tags=["recognitions"])


@router.post("/recognitions", response_model=RecognitionOut)
async def create_recognition(
    image: UploadFile = File(...),
    background: BackgroundTasks = None,
    garden_id: int = Depends(resolve_garden_id),
    db: Session = Depends(get_db),
):
    suffix = Path(image.filename or "").suffix.lower()
    content_type = (image.content_type or "").lower()
    if suffix not in config.ALLOWED_IMAGE_SUFFIXES:
        if content_type == "image/png":
            suffix = ".png"
        elif content_type == "image/jpeg":
            suffix = ".jpg"
        else:
            raise HTTPException(status_code=422, detail="仅支持 jpg/png 格式的图片")
    if suffix == ".jpeg":
        suffix = ".jpg"

    data = await image.read()
    if not data:
        raise HTTPException(status_code=422, detail="图片内容为空")
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail="图片大小不能超过 10MB")

    return recognition_service.create_recognition(db, garden_id, data, suffix, background)


@router.get("/recognitions/{recognition_id}", response_model=RecognitionOut)
def read_recognition(recognition_id: int, db: Session = Depends(get_db)):
    return recognition_service.get_recognition(db, recognition_id)
