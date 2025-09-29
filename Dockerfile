# Use a stable Python version to avoid dependency issues
FROM python:3.11-slim

# Install ffmpeg, which is required by pydub and moviepy
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script into the container
COPY main.py .

# Command to run the script when the container starts
CMD ["python", "main.py"]