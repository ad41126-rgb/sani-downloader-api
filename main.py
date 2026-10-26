
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from urllib.parse import urlparse

app = FastAPI(
    title="Sani Downloader API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ad41126-rgb.github.io"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class VideoRequest(BaseModel):
    url: HttpUrl

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
    parsed = urlparse(str(data.url))

    allowed_hosts = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtube-nocookie.com",
    }

    if parsed.scheme != "https":
        return {
            "valid": False,
            "message": "Gunakan tautan HTTPS."
        }

    if parsed.hostname not in allowed_hosts:
        return {
            "valid": False,
            "message": "Domain belum didukung."
        }

    return {
        "valid": True,
        "message": (
            "Format tautan diterima. "
            "Ini baru pemeriksaan tautan, "
            "belum mengunduh video."
        )
    }
