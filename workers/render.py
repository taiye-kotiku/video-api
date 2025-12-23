import os, uuid, subprocess, tempfile, httpx, aiofiles
from pathlib import Path
from arq import create_pool
from api.config import settings
from storage.r2 import upload_file
import logging
logger = logging.getLogger("arq")

# ---------- helpers ----------
def cents_cost(duration_s: float, quality: str) -> float:
    rate = 0.04 if quality == "final" else 0.008   # preview = 20 % price
    return round(duration_s * rate, 3)

def download(url: str, dest: Path):
    with httpx.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes(1024*64):
                f.write(chunk)

def ffmpeg_cmd(inputs: list[Path], output: Path, title: str, quality: str) -> list[str]:
    scale = "scale=720:1280" if quality == "preview" else "scale=1080:1920"
    vf = (
        f"[0:v]{scale},pad=iw:ih+400:(ow-iw)/2:oh-ih:color=black@0,"
        f"drawtext=text='{title}':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=100,"
        f"drawtext=text='@%H\\:%M\\:%S':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=200"
    )
    cmd = ["ffmpeg", "-y", "-i", str(inputs[0]), "-vf", vf, "-c:a", "copy", str(output)]
    return cmd

# ---------- main worker ----------
async def render_textoverlay(ctx, video_url: str, title: str, quality: str = "final"):
    job_id = uuid.uuid4().hex
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        video_in = tmp / "input.mp4"
        video_out = tmp / "output.mp4"

        logger.info("downloading %s", video_url)
        download(video_url, video_in)

        logger.info("rendering job=%s quality=%s", job_id, quality)
        cmd = ffmpeg_cmd([video_in], video_out, title.replace("'", "\\'"), quality)
        subprocess.run(cmd, check=True, capture_output=True)

        duration = float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_out)]
        ).strip())

        logger.info("uploading job=%s", job_id)
        r2_url = upload_file(str(video_out), f"renders/{job_id}.mp4")

        cost = cents_cost(duration, quality)
        logger.info("finished job=%s duration=%ss cost_cents=%s", job_id, duration, cost)

        return {"jobId": job_id, "url": r2_url, "duration": duration, "cost_cents": cost}