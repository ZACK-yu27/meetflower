"""FastAPI 入口：CORS 全开、/static 挂载 app/assets/、启动播种 garden id=1、统一错误响应。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .db import Base, SessionLocal, engine, get_db  # noqa: F401  (get_db 供路由依赖)
from . import models  # noqa: F401  注册全部表
from .api import art, badge, bouquets, demo, gardens, house, images, orders, recognitions
from .services import DomainError
from .services.garden import seed_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    _ensure_columns()  # 轻量迁移：给存量表补新列（create_all 不会改已有表）
    with SessionLocal() as session:
        seed_db(session)  # 播种 garden id=1 与 resource_accounts / badges 行（幂等）
    yield


def _ensure_columns() -> None:
    """给已存在的表补新增列（SQLite/Postgres 均支持 ADD COLUMN IF NOT EXISTS 的等价写法）。

    当前迁移：recognitions.form / plants.form（花型，2026-07-25 线稿花型系统）。
    """
    from sqlalchemy import inspect, text

    wanted = {
        "recognitions": {"form": "VARCHAR", "resemble_attrs": "JSON"},
        "plants": {"form": "VARCHAR"},
        "house_items": {"form": "VARCHAR"},
    }
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in wanted.items():
            existing = {c["name"] for c in insp.get_columns(table)}
            for col, ddl in cols.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


app = FastAPI(title="抖音花园 MVP", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    """Render 健康检查专用：不查库，只证明进程存活（DB 冷启动不应判为服务故障）。"""
    return {"ok": True}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源：server/app/assets/ → /static/（生成图 /static/gen/，上传图 /static/uploads/）
app.mount("/static", StaticFiles(directory=config.ASSETS_DIR), name="static")


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    error = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(x) for x in error.get("loc", []) if x not in ("body", "query", "path"))
    msg = error.get("msg", "参数错误")
    detail = f"参数错误：{loc} {msg}" if loc else f"参数错误：{msg}"
    return JSONResponse(status_code=422, content={"detail": detail})


API_PREFIX = "/api/v1"
for router in (
    recognitions.router,
    gardens.router,
    house.router,
    bouquets.router,
    orders.router,
    demo.router,
    badge.router,
    images.router,
    art.router,
):
    app.include_router(router, prefix=API_PREFIX)
