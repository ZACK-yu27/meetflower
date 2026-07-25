"""数据库引擎/会话/Base（SQLAlchemy 2.x）。

生产环境（如 Render）通过 FLOWERS_DATABASE_URL 环境变量覆盖。
默认使用项目目录内的 flowers.db；若环境变量指定路径，自动确保父目录存在。
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent  # server/

# 优先读取环境变量；无则默认放在项目目录
DATABASE_URL = os.environ.get(
    "FLOWERS_DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'flowers.db'}"
)

# 若是文件型 SQLite，确保父目录存在（Render 等只读代码目录需要）
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:///:memory:"):
    raw = DATABASE_URL[10:]  # 去掉前缀
    db_path = Path(raw)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # 目录已存在或无权创建，后续 SQLAlchemy 会报更具体的错

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖：每请求一个会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
