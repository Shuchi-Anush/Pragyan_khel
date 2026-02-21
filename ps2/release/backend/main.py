from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import json
import asyncio
from functools import partial
from detector import process_video

app = FastAPI(title="Ball Detection API")

# ─── CORS ─── explicit origins, no credentials ────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB
ALLOWED_MIME = {
    "video/mp4", "video/avi", "video/x-msvideo",
    "video/quicktime", "video/x-matroska", "video/webm",
}


def _safe_path(folder: str, filename: str) -> str:
    """Resolve filename inside folder; raise 403 if path traversal detected."""
    real_folder = os.path.realpath(folder)
    candidate   = os.path.realpath(os.path.join(real_folder, filename))
    # Must start with the folder path followed by OS separator (or equal it)
    if not (candidate.startswith(real_folder + os.sep) or candidate == real_folder):
        raise HTTPException(status_code=403, detail="Forbidden")
    return candidate


# ─── Health check — validates model weight exists ─────────────────────
@app.get("/health")
async def health():
    model_path = os.path.join(os.path.dirname(__file__), "best.pt")
    model_ok   = os.path.exists(model_path)
    return {"status": "ok", "model": "loaded" if model_ok else "missing"}

@app.post("/upload")
async def upload_video():
    import os
    import asyncio
    from functools import partial

    # Base directory of backend
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Go up: backend → release → ps2 → project root
    project_root = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

    demo_video_path = os.path.join(
        project_root,
        "ps2",
        "sample_videos",
        "final.mp4"   # <- use exact filename here
    )

    if not os.path.exists(demo_video_path):
        raise HTTPException(status_code=500, detail=f"Demo video not found at {demo_video_path}")

    # Run heavy processing in executor
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        partial(process_video, demo_video_path, output_dir=OUTPUT_FOLDER),
    )

    return {
        "status":          "processed",
        "annotated_video": result["annotated_video"],
        "report":          result["report"],
        "report_file":     result.get("report_file"),
        "csv_file":        result.get("csv_file"),
        "thumbnail":       result.get("thumbnail"),
    }

@app.get("/video/{filename}")
async def get_video(filename: str):
    path = _safe_path(OUTPUT_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="video/mp4")


@app.get("/download/{filename}")
async def download_file(filename: str):
    path = _safe_path(OUTPUT_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)


@app.get("/report/{filename}")
async def get_report(filename: str):
    """Return the JSON report for a processed video."""
    path = _safe_path(OUTPUT_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(path, "r") as f:
        data = json.load(f)
    return data
