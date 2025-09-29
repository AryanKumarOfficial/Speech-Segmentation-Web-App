import os
import json
import requests
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

# --- Configuration ---
VIDEO_URL = "https://filebin.net/1ycdsglo8k2szpj8/download"
OUTPUT_DIR = "output"  # All results will go here
INPUT_VIDEO_FILENAME = os.path.join(OUTPUT_DIR, "input_video.mp4")
EXTRACTED_AUDIO_FILENAME = os.path.join(OUTPUT_DIR, "extracted_audio.wav")
TIMESTAMPS_FILENAME = os.path.join(OUTPUT_DIR, "speech_timestamps.json")
OUTPUT_CLIPS_DIR = os.path.join(OUTPUT_DIR, "segmented_clips")
SAMPLE_RATE = 16000

# --- Parameters for Speech Detection ---
MIN_SILENCE_LEN = 700
SILENCE_THRESH = -40
KEEP_SILENCE = 200


def download_file(url, filename):
    print(f"Downloading video from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Successfully downloaded to {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False


def extract_and_prepare_audio(video_path, audio_path):
    print(f"Extracting audio from {video_path}...")
    try:
        video_clip = VideoFileClip(video_path)
        video_clip.audio.write_audiofile(
            audio_path,
            fps=SAMPLE_RATE,
            nbytes=2,
            codec='pcm_s16le'
        )
        print(f"Audio extracted and saved to {audio_path}")
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False


def detect_speech_timestamps(audio_path):
    print("Detecting speech segments...")
    audio_segment = AudioSegment.from_wav(audio_path)
    nonsilent_times = detect_nonsilent(
        audio_segment,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=SILENCE_THRESH,
        seek_step=1
    )
    speech_timestamps = []
    for start_ms, end_ms in nonsilent_times:
        start_sec = (start_ms - KEEP_SILENCE) / 1000
        end_sec = (end_ms + KEEP_SILENCE) / 1000
        speech_timestamps.append({
            "start": max(0, round(start_sec, 2)),
            "end": round(end_sec, 2)
        })
    print(f"Detected {len(speech_timestamps)} speech segments.")
    return speech_timestamps


def export_audio_segments(audio_path, timestamps, output_dir):
    print(f"Exporting segments to '{output_dir}/'...")
    os.makedirs(output_dir, exist_ok=True)
    original_audio = AudioSegment.from_wav(audio_path)
    for i, segment in enumerate(timestamps):
        start_ms = segment['start'] * 1000
        end_ms = segment['end'] * 1000
        clip = original_audio[start_ms:end_ms]
        output_filename = os.path.join(output_dir, f"segment_{i+1:03d}.wav")
        clip.export(output_filename, format="wav")
    print(f"Successfully exported {len(timestamps)} clips.")


def main():
    # Create the main output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not download_file(VIDEO_URL, INPUT_VIDEO_FILENAME):
        return
    if not extract_and_prepare_audio(INPUT_VIDEO_FILENAME, EXTRACTED_AUDIO_FILENAME):
        return
    timestamps = detect_speech_timestamps(EXTRACTED_AUDIO_FILENAME)
    with open(TIMESTAMPS_FILENAME, 'w') as f:
        json.dump(timestamps, f, indent=2)
    print(f"Timestamps saved to {TIMESTAMPS_FILENAME}")
    export_audio_segments(EXTRACTED_AUDIO_FILENAME,
                          timestamps, OUTPUT_CLIPS_DIR)
    print("\n✅ Docker task completed successfully!")


if __name__ == "__main__":
    main()
