# Use Python 3.11 (Slim version for speed)
FROM python:3.11-slim

# 1. Install FFmpeg (Crucial for video cropping)
# We update the package list, install ffmpeg, and clean up to keep the image small
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code
COPY . .

# 5. Run the application
# Render uses the PORT environment variable, defaulting to 8080 if not set
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]