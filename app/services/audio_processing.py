import json
import os
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from uuid import uuid4

import requests
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.generators import Sine
from pydub.silence import detect_nonsilent

SAMPLE_RATE = 16000
MIN_SILENCE_LEN = 700
SILENCE_THRESH = -40
KEEP_SILENCE = 200


def _ensure_writable_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".permission_check"
        test_file.touch(exist_ok=True)
        test_file.unlink(missing_ok=True)
        return True
    except (PermissionError, OSError):
        return False


def _resolve_output_root() -> Path:
    candidates = []

    env_output = os.getenv("OUTPUT_DIR")
    if env_output:
        candidates.append(Path(env_output).expanduser().resolve())

    project_output = Path("output").resolve()
    candidates.append(project_output)

    temp_output = Path(tempfile.gettempdir()) / "speech-segmentation-output"
    candidates.append(temp_output)

    for candidate in candidates:
        if _ensure_writable_directory(candidate):
            return candidate

    raise RuntimeError("Unable to locate a writable output directory for audio processing.")


OUTPUT_ROOT = _resolve_output_root()


class AudioProcessingError(Exception):
    """Raised when the audio pipeline fails"""


class ProcessingResult(dict):
    """Convenience dict for JSON serialisation"""


def _make_job_dir(prefix: Optional[str] = None) -> Path:
    job_name = uuid4().hex
    if prefix:
        job_name = f"{prefix}_{job_name}"
    job_dir = OUTPUT_ROOT / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def _derive_filename(url: str, default_name: str) -> str:
    filename = os.path.basename(url)
    if not filename or filename.endswith('/'):
        filename = default_name
    return filename


def _download_file(url: str, destination: Path) -> Path:
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise AudioProcessingError(f"Failed to download file: {exc}") from exc

    filename = _derive_filename(url, "input.bin")
    download_path = destination / filename

    try:
        with open(download_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
    except OSError as exc:
        raise AudioProcessingError(
            f"Unable to write downloaded file: {exc}") from exc

    return download_path


def _ensure_wav(audio_segment: AudioSegment, output_path: Path) -> Path:
    audio_segment = audio_segment.set_channels(1).set_frame_rate(SAMPLE_RATE)
    audio_segment.export(output_path, format="wav")
    return output_path


def _extract_audio(input_path: Path, output_path: Path) -> Path:
    suffix = input_path.suffix.lower()

    if suffix in {".wav", ".mp3", ".m4a", ".aac", ".flac"}:
        segment = AudioSegment.from_file(input_path)
        return _ensure_wav(segment, output_path)

    try:
        clip = VideoFileClip(str(input_path))
    except OSError as exc:
        raise AudioProcessingError(
            f"Unable to open media file: {exc}") from exc

    try:
        clip.audio.write_audiofile(
            str(output_path),
            fps=SAMPLE_RATE,
            nbytes=2,
            codec="pcm_s16le"
        )
    finally:
        clip.close()

    segment = AudioSegment.from_wav(output_path)
    return _ensure_wav(segment, output_path)


def _detect_speech_timestamps(audio_path: Path) -> List[Tuple[float, float]]:
    try:
        audio_segment = AudioSegment.from_wav(audio_path)
    except Exception as exc:
        raise AudioProcessingError(
            f"Unable to read audio file: {exc}") from exc

    nonsilent_times = detect_nonsilent(
        audio_segment,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=SILENCE_THRESH,
        seek_step=1
    )

    timestamps = []
    for start_ms, end_ms in nonsilent_times:
        start_sec = max(0, (start_ms - KEEP_SILENCE) / 1000)
        end_sec = (end_ms + KEEP_SILENCE) / 1000
        timestamps.append((round(start_sec, 2), round(end_sec, 2)))
    return timestamps


def _export_segments(audio_path: Path, timestamps: List[Tuple[float, float]], output_dir: Path) -> List[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    original_audio = AudioSegment.from_wav(audio_path)

    exported = []
    for index, (start, end) in enumerate(timestamps, start=1):
        start_ms = int(start * 1000)
        end_ms = int(end * 1000)
        clip = original_audio[start_ms:end_ms]
        clip_name = f"segment_{index:03d}.wav"
        clip_path = output_dir / clip_name
        clip.export(clip_path, format="wav")
        exported.append({
            "file": clip_name,
            "start": start,
            "end": end,
            "path": str(clip_path)
        })
    return exported


def generate_demo_job() -> ProcessingResult:
    """Create a synthetic job so the UI can be explored without a real URL."""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    job_dir = _make_job_dir(prefix="demo")

    tone_specs = [
        {"freq": 440, "duration": 1800, "gap_after": 800},
        {"freq": 554, "duration": 1500, "gap_after": 900},
        {"freq": 659, "duration": 2100, "gap_after": 0},
    ]

    base_audio = AudioSegment.silent(duration=500)
    timestamps: List[Tuple[float, float]] = []

    for index, spec in enumerate(tone_specs):
        start_ms = len(base_audio)
        tone = Sine(spec["freq"]).to_audio_segment(
            duration=spec["duration"]).apply_gain(-6)
        base_audio += tone
        end_ms = len(base_audio)
        timestamps.append((round(start_ms / 1000, 2), round(end_ms / 1000, 2)))

        if spec.get("gap_after", 0) and index < len(tone_specs) - 1:
            base_audio += AudioSegment.silent(duration=spec["gap_after"])

    base_audio = base_audio.set_channels(1).set_frame_rate(SAMPLE_RATE)

    audio_path = job_dir / "extracted_audio.wav"
    base_audio.export(audio_path, format="wav")

    timestamps_payload = [
        {"start": start, "end": end}
        for start, end in timestamps
    ]

    timestamps_file = job_dir / "speech_timestamps.json"
    with open(timestamps_file, "w", encoding="utf-8") as fh:
        json.dump(timestamps_payload, fh, indent=2)

    segments_dir = job_dir / "segmented_clips"
    segments = _export_segments(audio_path, timestamps, segments_dir)

    input_file = job_dir / "demo_source.txt"
    input_file.write_text(
        "Synthetic audio generated by the demo endpoint."
        " Replace this with a real URL to process actual media.",
        encoding="utf-8"
    )

    return ProcessingResult({
        "job_id": job_dir.name,
        "input_file": str(input_file),
        "audio_file": str(audio_path),
        "timestamps_file": str(timestamps_file),
        "timestamps": timestamps_payload,
        "segments": segments,
        "demo": True,
    })


def process_url(url: str) -> ProcessingResult:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    job_dir = _make_job_dir()
    download_path = _download_file(url, job_dir)

    audio_path = job_dir / "extracted_audio.wav"
    audio_path = _extract_audio(download_path, audio_path)

    timestamps = _detect_speech_timestamps(audio_path)
    timestamps_payload = [
        {"start": start, "end": end}
        for start, end in timestamps
    ]

    timestamps_file = job_dir / "speech_timestamps.json"
    with open(timestamps_file, "w", encoding="utf-8") as fh:
        json.dump(timestamps_payload, fh, indent=2)

    segments_dir = job_dir / "segmented_clips"
    segments = _export_segments(audio_path, timestamps, segments_dir)

    return ProcessingResult({
        "job_id": job_dir.name,
        "input_file": str(download_path),
        "audio_file": str(audio_path),
        "timestamps_file": str(timestamps_file),
        "timestamps": timestamps_payload,
        "segments": segments
    })
