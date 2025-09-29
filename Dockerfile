# Use a stable Python version to avoid dependency issues
FROM python:3.11-slim

# Install ffmpeg, which is required by pydub and moviepy
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definition and install packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source (FastAPI app and assets)
COPY app/ ./app/
COPY main.py ./

# Expose the FastAPI port
EXPOSE 8000

# Command to launch the web server
CMD ["python", "main.py"]