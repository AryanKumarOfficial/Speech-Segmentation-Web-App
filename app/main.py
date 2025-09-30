from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from .services.audio_processing import (
    AudioProcessingError,
    OUTPUT_ROOT,
    generate_demo_job,
    process_url,
)

app = FastAPI(title="Speech Segmentation Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

output_path = OUTPUT_ROOT
output_path.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_path)), name="output")




class ProcessRequest(BaseModel):
    url: HttpUrl


def _shape_response(result: dict) -> dict:
    job_id = result["job_id"]
    base_url = f"/output/{job_id}"

    response_payload = {
        "job_id": job_id,
        "input_file": f"{base_url}/{Path(result['input_file']).name}",
        "audio_file": f"{base_url}/{Path(result['audio_file']).name}",
        "timestamps_file": f"{base_url}/{Path(result['timestamps_file']).name}",
        "timestamps": result["timestamps"],
        "segments": [
            {
                "file": segment["file"],
                "start": segment["start"],
                "end": segment["end"],
                "url": f"{base_url}/segmented_clips/{segment['file']}"
            }
            for segment in result["segments"]
        ],
        "demo": result.get("demo", False),
    }
    return response_payload


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/process")
async def process_audio(req: ProcessRequest):
    try:
        result = process_url(req.url)
    except AudioProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _shape_response(result)


@app.post("/api/demo")
async def demo_audio():
    result = generate_demo_job()
    return _shape_response(result)


