import os
import json
import requests
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

# --- Configuration ---
VIDEO_URL = "https://filebin.net/1ycdsglo8k2szpj8/download"
INPUT_VIDEO_FILENAME = "input_video.mp4"
EXTRACTED_AUDIO_FILENAME = "extracted_audio.wav"
TIMESTAMPS_FILENAME = "speech_timestamps.json"
OUTPUT_CLIPS_DIR = "segmented_clips"
SAMPLE_RATE = 16000  # 16 kHz, a standard for speech processing

# --- Parameters for Speech Detection (can be tuned) ---
# The minimum length of a silence to be considered a split point (in milliseconds)
MIN_SILENCE_LEN = 700

# The upper bound for how quiet a sound can be to be considered silence (in dBFS)
# A lower value is more strict and will detect more silence.
SILENCE_THRESH = -40

# A duration to keep at the start and end of each speech segment (in milliseconds)
KEEP_SILENCE = 200


def download_file(url, filename):
    """Downloads a file from a given URL."""
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
    """
    Extracts audio from a video file, converts it to mono,
    and sets the sample rate.
    """
    print(f"Extracting audio from {video_path}...")
    try:
        video_clip = VideoFileClip(video_path)
        # set_channels(1) for mono, set_fps for sample rate
        video_clip.audio.write_audiofile(
            audio_path,
            fps=SAMPLE_RATE,
            nbytes=2,  # 16-bit audio
            codec='pcm_s16le'  # Standard WAV codec
        )
        print(f"Audio extracted and saved to {audio_path}")
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False


def detect_speech_timestamps(audio_path):
    """
    Analyzes the audio file and returns a list of speech segments.
    """
    print("Detecting speech segments...")
    audio_segment = AudioSegment.from_wav(audio_path)

    # detect_nonsilent returns a list of [start, end] timestamps in milliseconds
    nonsilent_times = detect_nonsilent(
        audio_segment,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=SILENCE_THRESH,
        seek_step=1
    )

    # Add padding (keep_silence) to the start and end of each segment
    # and convert from milliseconds to seconds
    speech_timestamps = []
    for start_ms, end_ms in nonsilent_times:
        start_sec = (start_ms - KEEP_SILENCE) / 1000
        end_sec = (end_ms + KEEP_SILENCE) / 1000

        speech_timestamps.append({
            # Ensure start is not negative
            "start": max(0, round(start_sec, 2)),
            "end": round(end_sec, 2)
        })

    print(f"Detected {len(speech_timestamps)} speech segments.")
    return speech_timestamps


def export_audio_segments(audio_path, timestamps, output_dir):
    """
    Exports the detected speech segments into individual audio files.
    """
    print(f"Exporting segments to '{output_dir}/'...")
    os.makedirs(output_dir, exist_ok=True)

    original_audio = AudioSegment.from_wav(audio_path)

    for i, segment in enumerate(timestamps):
        start_ms = segment['start'] * 1000
        end_ms = segment['end'] * 1000

        # Extract the segment
        clip = original_audio[start_ms:end_ms]

        # Define output filename
        output_filename = os.path.join(output_dir, f"segment_{i+1:03d}.wav")

        # Export the clip
        clip.export(output_filename, format="wav")

    print(f"Successfully exported {len(timestamps)} clips.")


def main():
    """Main function to orchestrate the entire process."""
    # Task 0: Download the video file
    if not download_file(VIDEO_URL, INPUT_VIDEO_FILENAME):
        return  # Stop if download fails

    # Task 1: Extract and standardize audio
    if not extract_and_prepare_audio(INPUT_VIDEO_FILENAME, EXTRACTED_AUDIO_FILENAME):
        return  # Stop if audio extraction fails

    # Task 2: Detect speech segments and get timestamps
    timestamps = detect_speech_timestamps(EXTRACTED_AUDIO_FILENAME)

    # Save the timestamps to a JSON file
    with open(TIMESTAMPS_FILENAME, 'w') as f:
        json.dump(timestamps, f, indent=2)
    print(f"Timestamps saved to {TIMESTAMPS_FILENAME}")

    # Task 3: Segment and export audio clips
    export_audio_segments(EXTRACTED_AUDIO_FILENAME,
                          timestamps, OUTPUT_CLIPS_DIR)

    print("\n✅ Assignment completed successfully!")


if __name__ == "__main__":
    main()
