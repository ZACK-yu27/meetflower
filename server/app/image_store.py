"""图片二进制存储：Image 表 get-or-create（按 name 去重）+ 访问 URL 构造。

仅用于不可再生的图片：上传原图（upload_ 前缀）、Seedream/Pillow 花束预览（bouquet_ 前缀）。
阶段图/花朵特写等确定性 Pillow 资产走 /api/v1/art/... 动态渲染，不入库。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai_gateway.settings import public_url
from .models import Image


def save_image(db: Session, name: str, data: bytes, mime: str) -> Image:
    """按 name 去重保存图片（已存在则复用），返回 Image 行。"""
    img = db.scalar(select(Image).where(Image.name == name))
    if img is None:
        img = Image(name=name, data=data, mime=mime)
        db.add(img)
        db.flush()  # 拿 id，由调用方提交事务
    return img


def image_url(image_id: int) -> str:
    return public_url(f"/api/v1/images/{image_id}")
