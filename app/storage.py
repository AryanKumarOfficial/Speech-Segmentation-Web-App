# app/storage.py
import os
from pathlib import Path
import shutil

BASE_DATA_DIR = os.getenv("DATA_DIR", "/app/data")

def ensure_job_dir(job_id: str):
    job_dir = Path(BASE_DATA_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return str(job_dir)

def list_outputs(job_id: str):
    job_dir = Path(BASE_DATA_DIR) / job_id
    if not job_dir.exists(): 
        return []
    return [str(p) for p in sorted(job_dir.iterdir()) if p.is_file()]

def save_uploaded_file(tmp_path: str, dest_path: str):
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(tmp_path, dest)
    return str(dest)
