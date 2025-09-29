## Speech Segmentation Web App

Interactive FastAPI experience for the assignment in `assignment.md`. Paste the provided FileBin video (or any supported audio/video URL) and the app will:

- download the media
- extract mono 16 kHz audio
- detect speech activity ranges
- export the detected speech segments as individual clips
- expose all artefacts (timestamps JSON, extracted audio, segment files) for download

### Prerequisites

- Python 3.10+ (tested on 3.13)
- `ffmpeg` available on the system path (required by `pydub` / `moviepy`)

Create a virtual environment (recommended) and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** The requirements include `audioop-lts`, a shim that restores the standard-library `audioop` module on Python builds (3.13+) where it was removed. No extra setup is needed beyond installing the requirements.

### Run the web server

```bash
python main.py
```

Then open [http://localhost:8000](http://localhost:8000) and paste the assignment video URL (`https://filebin.net/1ycdsglo8k2szpj8`).

### No URL yet? Try the demo

If you just want to explore the interface, use the built-in demo workflow:

1. Launch the server (`python main.py`) and open the UI.
2. Click **Run demo walkthrough**.
3. The backend synthesises a short audio file, generates timestamps, and exports three sample segments.

You can download the demo artefacts like normal, and they are also stored under `output/demo_<job_id>/` for inspection. Replace the demo with a real URL whenever you have the assignment media handy.

### Docker (optional)

A container recipe is provided for reproducible runs:

```bash
docker build -t speech-segmentation .
docker run --rm -p 8000:8000 speech-segmentation
```

Navigate to [http://localhost:8000](http://localhost:8000) to interact with the UI as usual.

### Output

Each request is isolated in `output/<job_id>/` and contains:

- downloaded source file
- `extracted_audio.wav`
- `speech_timestamps.json`
- `segmented_clips/segment_XXX.wav`

The frontend shows the timestamps in-table and provides direct download links for every artefact. All files are also served under `/output/<job_id>/` so they can be accessed programmatically.

### Troubleshooting

- **`ModuleNotFoundError: No module named 'audioop'`** – ensure dependencies were installed from `requirements.txt`. If you are using a custom environment, explicitly install `audioop-lts`.
- **Missing `ffmpeg` binary** – install via your package manager (`sudo apt install ffmpeg`, `brew install ffmpeg`, etc.).
- **Large downloads** – the processing runs synchronously; very large media may take a minute or two to finish. The status message in the UI updates once segments are available.

### Validation

The app modules compile successfully:

```bash
python -m compileall app
```
