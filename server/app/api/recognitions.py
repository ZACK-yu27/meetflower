"""1.1 识花：POST /api/v1/recognitions（multipart/form-data，字段 image，jpg/png ≤10MB）；
POST /api/v1/recognitions/video（广义的"花"，字段 video，mp4/mov/webm ≤30MB，规则见 docs/flower_resemble.md）；
GET /api/v1/recognitions/{id}（轮询：ark 模式科普文案异步补齐后 science_text 非空）。"""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import config
from ..ai_gateway.video import VideoFrameError
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


@router.post("/recognitions/video", response_model=RecognitionOut)
async def create_resemble_recognition(
    video: UploadFile = File(...),
    background: BackgroundTasks = None,
    garden_id: int = Depends(resolve_garden_id),
    db: Session = Depends(get_db),
):
    suffix = Path(video.filename or "").suffix.lower()
    content_type = (video.content_type or "").lower()
    if suffix not in config.ALLOWED_VIDEO_SUFFIXES:
        if content_type.startswith("video/"):
            suffix = ".mp4"  # 无扩展名但确为视频：按 mp4 交给 ffmpeg 探测
        else:
            raise HTTPException(status_code=422, detail="仅支持 mp4/mov/webm 格式的视频")

    data = await video.read()
    if not data:
        raise HTTPException(status_code=422, detail="视频内容为空")
    if len(data) > config.MAX_VIDEO_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail="视频大小不能超过 30MB")

    try:
        return recognition_service.create_resemble_recognition(db, garden_id, data, suffix, background)
    except VideoFrameError:
        raise HTTPException(status_code=422, detail="视频无法解析，换一个试试") from None
