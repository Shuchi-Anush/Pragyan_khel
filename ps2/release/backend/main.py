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
async def upload_video(file: UploadFile = File(...)):
    # ── Content-type guard
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {sorted(ALLOWED_MIME)}",
        )

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # ── Stream to disk with size cap
    size = 0
    with open(file_path, "wb") as buf:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                buf.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail="File too large (max 500 MB)")
            buf.write(chunk)

    # ── Run CPU-heavy processing in a thread so the event loop stays free
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        partial(process_video, file_path, output_dir=OUTPUT_FOLDER),
    )

    return {
        "status":          "processed",
        "annotated_video": result["annotated_video"],
        "report":          result["report"],
        "report_file":     result.get("report_file"),
        "csv_file":        result.get("csv_file"),
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
