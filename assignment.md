# Assignment: Speech Segmentation from Audio

## Objective

The goal of this assignment is to process an audio file and segment it into smaller clips based on speech activity. You will use audio processing techniques to identify portions of the audio where speech occurs and extract those segments into individual audio files.

## Download Video

For this assignment, download the video from this URL:
**https://filebin.net/1ycdsglo8k2szpj8**

## Tasks

### 1. Extract Audio

- Input will be an audio or video file.
- If the input is a video, extract and save only the audio track (e.g., in .wav format).
- Ensure the audio is converted into a standard format for further processing (e.g., mono, 16 kHz sample rate).

### 2. Detect Speech Segments

- Analyze the audio to identify timestamps where people are speaking.
- Use energy levels / amplitude thresholds or similar audio signal features to differentiate between:
  - Speech (high energy, variable amplitude)
  - Silence or background noise (low energy, stable amplitude)
- Store the detected speech segments in the form of start and end timestamps.

Example:
```json
[
  {"start": 1.25, "end": 3.80},
  {"start": 7.10, "end": 10.45},
  {"start": 15.00, "end": 18.75}
]
```

### 3. Segment and Export Audio Clips

- Using the timestamps from step 2, split the original audio file into multiple smaller files.
- Each file should correspond to a continuous speech segment.
- Save the clips in a suitable format (e.g., .wav or .mp3) with systematic file naming such as:
  - segment_01.wav
  - segment_02.wav
  - segment_03.wav

## Deliverables

- Source code (Python preferred) that implements the above steps.
- Output:
  - Extracted audio file (if input was video).
  - JSON or text file containing detected speech timestamps.
  - A folder with all segmented audio files.