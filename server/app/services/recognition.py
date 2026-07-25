"""识花服务：保存上传图（内容哈希命名去重）→ VLM → 预生成阶段资产 → 落库。

科普文案策略（识花首响优化）：
- mock 模式：本地模板瞬时生成，同步写入；
- ark 模式：真实 LLM 撰写约 15–20s，同步等待会把识花接口拖到 30s+，
  因此首响先返回（science_text=""），由 FastAPI BackgroundTasks 异步补齐，
  前端经 GET /api/v1/recognitions/{id} 轮询获取。
"""

import hashlib
import logging
import tempfile
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from .. import config
from ..ai_gateway import ensure_stage_images, flower_image_url, flower_profile, identify_flower
from ..ai_gateway import settings as ai_settings
from ..db import SessionLocal
from ..image_store import image_url, save_image
from ..models import Recognition
from ..schemas import RecognitionOut
from . import DomainError

logger = logging.getLogger("services.recognition")


def save_upload(session: Session, data: bytes, suffix: str) -> tuple[int, str]:
    """上传图入库（按内容哈希去重），并写临时文件供 VLM 读取，返回 (image_id, 临时路径)。"""
    digest = hashlib.sha256(data).hexdigest()[:12]
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    img = save_image(session, f"upload_{digest}{suffix}", data, mime)
    tmp_path = config.UPLOADS_DIR / f"{digest}{suffix}"
    try:
        if not tmp_path.exists():
            tmp_path.write_bytes(data)
    except OSError:  # 目录不可写时退到系统临时目录（VLM 仅需识别期间可读）
        tmp_path = Path(tempfile.gettempdir()) / f"flowers_upload_{digest}{suffix}"
        tmp_path.write_bytes(data)
    return img.id, str(tmp_path)


def _out(recognition: Recognition) -> RecognitionOut:
    return RecognitionOut(
        recognition_id=recognition.id,
        image_url=image_url(recognition.image_id),
        species=recognition.species,
        main_color=recognition.main_color,
        secondary_color=recognition.secondary_color,
        confidence=recognition.confidence,
        science_text=recognition.science_text or "",
        flower_image=recognition.flower_image,
        stage_images=recognition.stage_images,
    )


def fill_science_text(recognition_id: int, species: str, main_color: str, secondary_color: str) -> None:
    """后台任务：真实 LLM 撰写科普并回写（内部失败自动降级模板，不抛异常）。"""
    db = SessionLocal()
    try:
        recognition = db.get(Recognition, recognition_id)
        if recognition is None or recognition.science_text:
            return
        profile = flower_profile(species, main_color, secondary_color)
        recognition.science_text = profile.science_text
        db.commit()
    except Exception:  # noqa: BLE001 — 后台任务静默兜底，下次轮询重试由前端超时控制
        logger.exception("科普文案异步补齐失败 recognition_id=%s", recognition_id)
    finally:
        db.close()


def create_recognition(
    session: Session,
    garden_id: int,
    data: bytes,
    suffix: str,
    background: BackgroundTasks | None = None,
) -> RecognitionOut:
    image_id, path = save_upload(session, data, suffix)
    vlm = identify_flower(path)
    stage_images = ensure_stage_images(vlm.species, vlm.main_color)
    flower_image = flower_image_url(vlm.species, vlm.main_color)

    # mock 同步生成（瞬时）；ark 首响先返回、科普异步补齐
    async_science = ai_settings.AI_PROVIDER == "ark" and background is not None
    science_text = "" if async_science else flower_profile(
        vlm.species, vlm.main_color, vlm.secondary_color
    ).science_text

    recognition = Recognition(
        garden_id=garden_id,
        image_id=image_id,
        image_path=path,
        species=vlm.species,
        main_color=vlm.main_color,
        secondary_color=vlm.secondary_color,
        confidence=vlm.confidence,
        science_text=science_text,
        stage_images=stage_images,
        flower_image=flower_image,
    )
    session.add(recognition)
    session.commit()
    session.refresh(recognition)

    if async_science:
        background.add_task(
            fill_science_text, recognition.id, vlm.species, vlm.main_color, vlm.secondary_color
        )

    return _out(recognition)


def get_recognition(session: Session, recognition_id: int) -> RecognitionOut:
    """轮询用：按 id 取识花结果（科普文案补齐后 science_text 非空）。"""
    recognition = session.get(Recognition, recognition_id)
    if recognition is None:
        raise DomainError(404, "识花记录不存在")
    return _out(recognition)
