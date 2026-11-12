
import os
import sqlite3
import logging
import argparse
import subprocess
import base64
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

BASE = Path(__file__).resolve().parent
PHOTO_DIR = BASE / "foto"
VIDEO_DIR = BASE / "videos"
DB = BASE / "history.db"

PAGE_ID = os.getenv("PAGE_ID", "")
PAGE_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "")
GRAPH_VERSION = os.getenv("GRAPH_API_VERSION", "v24.0")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
DURATION = int(os.getenv("VIDEO_DURATION", "15"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Jakarta")
SCHEDULE = os.getenv(
    "SCHEDULE_TIMES",
    "07:00,10:00,13:00,16:00,19:00,21:00"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def setup():
    PHOTO_DIR.mkdir(exist_ok=True)
    VIDEO_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DB) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS published (
                photo TEXT PRIMARY KEY,
                published_at TEXT
            )
        """)

def used_photos():
    with sqlite3.connect(DB) as db:
        return {
            row[0] for row in
            db.execute("SELECT photo FROM published")
        }

def get_photo():
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    used = used_photos()

    for photo in sorted(PHOTO_DIR.iterdir()):
        if photo.suffix.lower() in extensions:
            if photo.name not in used:
                return photo

    return None

def make_video(photo):
    output = VIDEO_DIR / (photo.stem + ".mp4")

    command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(photo),
        "-t", str(DURATION),
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "zoompan=z='min(zoom+0.0015,1.15)':"
        "d=1:s=1080x1920:fps=30,"
        "format=yuv420p",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        str(output)
    ]

    subprocess.run(command, check=True)
    return output

def make_caption(photo):
    fallback = "Video menarik hari ini! #FacebookReels"

    if not GEMINI_KEY:
        return fallback

    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(photo.suffix.lower(), "image/jpeg")

    image_data = base64.b64encode(
        photo.read_bytes()
    ).decode("utf-8")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash:generateContent"
        f"?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        "Buat caption Facebook Reels bahasa Indonesia "
                        "yang menarik berdasarkan foto ini. "
                        "Tambahkan hashtag yang relevan."
                    )
                },
                {
                    "inline_data": {
                        "mime_type": mime,
                        "data": image_data
                    }
                }
            ]
        }]
    }

    try:
        response = requests.post(
            url, json=payload, timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as error:
        logging.error("Gemini error: %s", error)
        return fallback

def publish_reel(video, caption):
    if DRY_RUN:
        logging.info("MODE TEST: tidak mengunggah video.")
        logging.info("Video: %s", video)
        logging.info("Caption: %s", caption)
        return True

    if not PAGE_ID or not PAGE_TOKEN:
        raise ValueError("Konfigurasi Facebook belum lengkap.")

    url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{PAGE_ID}/video_reels"
    )

    start = requests.post(
        url,
        data={
            "upload_phase": "start",
            "access_token": PAGE_TOKEN
        },
        timeout=60
    )
    start.raise_for_status()

    result = start.json()
    video_id = result["video_id"]
    upload_url = result["upload_url"]

    size = video.stat().st_size

    with video.open("rb") as file:
        upload = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {PAGE_TOKEN}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream"
            },
            data=file,
            timeout=300
        )
    upload.raise_for_status()

    finish = requests.post(
        url,
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
            "access_token": PAGE_TOKEN
        },
        timeout=120
    )
    finish.raise_for_status()

    logging.info("Reels berhasil dikirim: %s", video_id)
    return True

def run_job():
    logging.info("Memulai pembuatan Reels.")

    photo = get_photo()

    if photo is None:
        logging.warning("Tidak ada foto baru di folder foto.")
        return

    try:
        video = make_video(photo)
        caption = make_caption(photo)

        if publish_reel(video, caption):
            with sqlite3.connect(DB) as db:
                db.execute(
                    "INSERT OR REPLACE INTO published "
                    "(photo, published_at) VALUES (?, ?)",
                    (photo.name, datetime.now().isoformat())
                )

        logging.info("Proses selesai.")

    except Exception:
        logging.exception("Proses gagal.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    global DRY_RUN

    if args.dry_run:
        DRY_RUN = True

    setup()

    if args.once:
        run_job()
        return

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    for item in SCHEDULE.split(","):
        hour, minute = item.strip().split(":")
        scheduler.add_job(
            run_job,
            "cron",
            hour=int(hour),
            minute=int(minute)
        )

    logging.info("Jadwal aktif: %s", SCHEDULE)
    scheduler.start()

if __name__ == "__main__":
    main()
