from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import subprocess
import os
import uuid

app = FastAPI()

# Make a temp folder to store videos if it doesn't exist
if not os.path.exists("temp"):
    os.makedirs("temp")

def delete_file(path: str):
    """Deletes the video file after it has been sent to the phone to save space."""
    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted: {path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

@app.get("/")
def home():
    return {"message": "Pluto Clipper Engine is Running!"}

@app.post("/download")
async def download_video(url: str, background_tasks: BackgroundTasks):
    
    # Create unique names for files so multiple users don't clash
    file_id = str(uuid.uuid4())
    raw_path = f"temp/{file_id}_raw.mp4"
    final_path = f"temp/{file_id}_final.mp4"

    try:
        # 1. Download from YouTube using yt-dlp
        print(f"Downloading: {url}")
        subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", raw_path,
            url
        ], check=True)

        # 2. Crop to Vertical (9:16) using FFmpeg
        print("Cropping to vertical...")
        subprocess.run([
            "ffmpeg",
            "-i", raw_path,
            "-vf", "crop=ih*(9/16):ih:(iw-ow)/2:0", # The magic crop formula
            "-c:v", "libx264",
            "-preset", "ultrafast", # Fast processing
            "-c:a", "copy",
            "-y",
            final_path
        ], check=True)

        # 3. Schedule cleanup (Delete files after sending)
        background_tasks.add_task(delete_file, raw_path)
        background_tasks.add_task(delete_file, final_path)
        
        # 4. Send the final video file back to the app
        return FileResponse(final_path, media_type="video/mp4", filename="clip.mp4")

    except subprocess.CalledProcessError:
        return {"error": "Processing failed. YouTube might have blocked the server or the link is invalid."}
    except Exception as e:
        return {"error": str(e)}