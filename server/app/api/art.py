"""确定性 Pillow 资产动态渲染：阶段图 / 花朵特写。

URL 即参数（品种+颜色[+花型]+阶段），每次请求即时渲染——不落盘、不入库，
Render 临时磁盘重启清空也不受影响。

路由（段数区分，带 form 的给图鉴外品种传递 VLM 识别的花型）：
- /art/stage/{species}/{color}/{stage}.png
- /art/stage/{species}/{color}/{form}/{stage}.png
- /art/flower/{species}/{color}.png
- /art/flower/{species}/{color}/{form}.png
"""

from fastapi import APIRouter, HTTPException, Response

from ..ai_gateway.art import flower_image_png, stage_image_png
from ..ai_gateway.catalog import STAGES

router = APIRouter(tags=["art"])

# 缓存 5 分钟：渲染错误时能快速自愈，避免错误图被长缓存坑（历史教训：.png 后缀污染色名）
_CACHE = {"Cache-Control": "public, max-age=300"}


def _stage_png(species: str, color: str, stage: str, form: str | None) -> Response:
    stage = stage.removesuffix(".png")  # URL 形如 .../bloom.png
    if stage not in STAGES:
        raise HTTPException(status_code=404, detail="未知的成长阶段")
    return Response(
        content=stage_image_png(species, color, stage, form),
        media_type="image/png",
        headers=_CACHE,
    )


def _flower_png(species: str, color: str, form: str | None) -> Response:
    color = color.removesuffix(".png")  # URL 形如 .../红.png，必须剥后缀否则色名污染
    return Response(
        content=flower_image_png(species, color, form),
        media_type="image/png",
        headers=_CACHE,
    )


@router.get("/art/stage/{species}/{color}/{stage}")
def stage_image(species: str, color: str, stage: str):
    return _stage_png(species, color, stage, None)


@router.get("/art/stage/{species}/{color}/{form}/{stage}")
def stage_image_with_form(species: str, color: str, form: str, stage: str):
    return _stage_png(species, color, stage, form)


@router.get("/art/flower/{species}/{color}")
def flower_image(species: str, color: str):
    return _flower_png(species, color, None)


@router.get("/art/flower/{species}/{color}/{form}")
def flower_image_with_form(species: str, color: str, form: str):
    form = form.removesuffix(".png")  # URL 形如 .../ball.png
    return _flower_png(species, color, form)
