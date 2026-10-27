
import os
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from starlette.background import BackgroundTask

app = FastAPI(
    title="Sani Downloader API",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ad41126-rgb.github.io",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class VideoRequest(BaseModel):
    url: HttpUrl
    format: str = "mp4"


ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtube-nocookie.com",
}


def validate_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise HTTPException(
            status_code=400,
            detail="Gunakan tautan HTTPS."
        )

    if (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise HTTPException(
            status_code=400,
            detail="Domain belum didukung."
        )

    return url


@app.get("/")
def home():
    return {
        "status": "online",
        "app": "Sani Downloader API",
        "message": "Backend berhasil dijalankan."
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check-url")
def check_url(data: VideoRequest):
    url = validate_url(str(data.url))

    if data.format.lower() not in {"mp4", "mp3"}:
        raise HTTPException(
            status_code=400,
            detail="Pilih format MP4 atau MP3."
        )

    return {
        "valid": True,
        "message": "Format tautan diterima.",
        "format": data.format.lower()
    }


@app.post("/download")
def download_video(data: VideoRequest):
    url = validate_url(str(data.url))
    file_format = data.format.lower()

    if file_format not in {"mp4", "mp3"}:
        raise HTTPException(
            status_code=400,
            detail="Pilih format MP4 atau MP3."
        )

    # Folder sementara dibuat khusus untuk setiap permintaan.
    temp_dir = tempfile.mkdtemp(prefix="sani_dl_")

    try:
        options = {
            "outtmpl": os.path.join(temp_dir, "%(title).100s.%(ext)s"),
            "noplaylist": True,
            "restrictfilenames": True,
            "max_filesize": 500 * 1024 * 1024,
            "socket_timeout": 20,
            "retries": 1,
            "quiet": True,
            "no_warnings": True,
        }

        if file_format == "mp4":
            options.update({
                "format": "best[ext=mp4]/best",
                "merge_output_format": "mp4",
            })
        else:
            options.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }],
            })

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        files = [
            p for p in Path(temp_dir).iterdir()
            if p.is_file() and p.suffix.lower() in {".mp4", ".mp3", ".webm", ".mkv"}
        ]

        if not files:
            raise RuntimeError(
                "Berkas hasil unduhan tidak ditemukan."
            )

        output_file = max(files, key=lambda p: p.stat().st_size)

        media_type = (
            "audio/mpeg"
            if file_format == "mp3"
            else "video/mp4"
        )

        return FileResponse(
            path=str(output_file),
            media_type=media_type,
            filename=output_file.name,
            background=BackgroundTask(
                shutil.rmtree, temp_dir, ignore_errors=True
            ),
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail=(
                "Unduhan gagal. Periksa tautan, ketersediaan video, "
                "batas ukuran, dan dukungan FFmpeg."
            ),
        )
