"""图片访问：GET /api/v1/images/{id}（Image 表二进制，含上传原图与花束预览图）。"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Image

router = APIRouter(tags=["images"])

_CACHE = {"Cache-Control": "public, max-age=31536000, immutable"}


@router.get("/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    img = db.get(Image, image_id)
    if img is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    return Response(content=img.data, media_type=img.mime, headers=_CACHE)
