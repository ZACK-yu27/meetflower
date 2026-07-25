"""视频抽帧：imageio-ffmpeg 自带静态 ffmpeg 二进制（Render 免装系统依赖）。

规则见 docs/flower_resemble.md §2：每 3 秒 1 帧、最多 8 帧、宽 512px JPEG。
仅 ark 路径调用（mock 识别按视频字节哈希，不依赖 ffmpeg，保持离线可测）。
"""

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

FRAME_INTERVAL_SECONDS = 3
MAX_FRAMES = 4        # 帧数是 VLM 延时主因，4 帧覆盖 12 秒足够判断主体（超时治理后再次瘦身）
FRAME_WIDTH = 320     # 320px + detail=low：控制 payload 与模型延时


class VideoFrameError(Exception):
    """视频无法解析（损坏 / 格式不支持 / ffmpeg 不可用）。"""


def extract_frames(video_path: str) -> tuple[list[Path], bytes]:
    """抽帧，返回 (帧文件列表, 首帧 JPEG 字节作封面)。失败抛 VideoFrameError。"""
    out_dir = Path(tempfile.mkdtemp(prefix="flowers_frames_"))
    out_pattern = str(out_dir / "f_%02d.jpg")
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-loglevel", "error",
        "-i", video_path,
        "-vf", f"fps=1/{FRAME_INTERVAL_SECONDS},scale={FRAME_WIDTH}:-2",
        "-frames:v", str(MAX_FRAMES),
        "-q:v", "5",
        "-y",
        out_pattern,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise VideoFrameError(f"ffmpeg 执行失败: {e}") from e
    if proc.returncode != 0:
        raise VideoFrameError(f"ffmpeg 退出码 {proc.returncode}: {proc.stderr.decode(errors='ignore')[:200]}")

    frames = sorted(out_dir.glob("f_*.jpg"))
    if not frames:
        raise VideoFrameError("未抽到任何帧（视频过短或无法解码）")
    poster = frames[0].read_bytes()
    return frames, poster
