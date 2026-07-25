"""pytest 公共装置：隔离测试库 + 内存测试图生成。"""

import io
import os
import random
import tempfile
from pathlib import Path

# 在任何 app 模块导入前，把默认库文件指到临时目录（防御：避免触碰 server/flowers.db）
_TMP_DIR = Path(tempfile.mkdtemp(prefix="flowers_test_"))
os.environ["FLOWERS_DATABASE_URL"] = f"sqlite:///{(_TMP_DIR / 'default.db').as_posix()}"
# 测试强制 mock：不发起真实模型调用，保持离线、确定性
os.environ["AI_PROVIDER"] = "mock"

import pytest  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.db import Base  # noqa: E402
from app.services.garden import seed_db  # noqa: E402


def make_image_bytes(seed: int = 1) -> bytes:
    """构造内容随 seed 变化的 PNG 字节（mock VLM 按字节哈希确定性识花）。"""
    rnd = random.Random(seed)
    img = Image.new("RGB", (80, 80), (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
    d = ImageDraw.Draw(img)
    for _ in range(4):
        x0, y0 = rnd.randrange(60), rnd.randrange(60)
        d.rectangle(
            [x0, y0, x0 + rnd.randrange(8, 20), y0 + rnd.randrange(8, 20)],
            fill=(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)),
        )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def session(tmp_path):
    """每个测试一个独立的临时 SQLite 库，并播种 garden id=1。"""
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = Session()
    seed_db(s)
    try:
        yield s
    finally:
        s.close()
        engine.dispose()
