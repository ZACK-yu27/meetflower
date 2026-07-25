"""确定性 Pillow 资产动态渲染：阶段图 / 花朵特写。

URL 即参数（品种+颜色+阶段），每次请求即时渲染——不落盘、不入库，
Render 临时磁盘重启清空也不受影响。
"""

from fastapi import APIRouter, HTTPException, Response

from ..ai_gateway.art import flower_image_png, stage_image_png
from ..ai_gateway.catalog import STAGES

router = APIRouter(tags=["art"])

_CACHE = {"Cache-Control": "public, max-age=86400"}


@router.get("/art/stage/{species}/{color}/{stage}")
def stage_image(species: str, color: str, stage: str):
    stage = stage.removesuffix(".png")  # URL 形如 .../bloom.png
    if stage not in STAGES:
        raise HTTPException(status_code=404, detail="未知的成长阶段")
    return Response(
        content=stage_image_png(species, color, stage),
        media_type="image/png",
        headers=_CACHE,
    )


@router.get("/art/flower/{species}/{color}")
def flower_image(species: str, color: str):
    return Response(
        content=flower_image_png(species, color),
        media_type="image/png",
        headers=_CACHE,
    )
