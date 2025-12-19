from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import subprocess
import os
import uuid

app = FastAPI()

if not os.path.exists("temp"):
    os.makedirs("temp")

def delete_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

@app.get("/")
def home():
    return {"message": "Pluto Clipper Engine is Running!"}

@app.post("/download")
async def download_video(url: str, background_tasks: BackgroundTasks):
    
    file_id = str(uuid.uuid4())
    raw_path = f"temp/{file_id}_raw.mp4"
    final_path = f"temp/{file_id}_final.mp4"

    try:
        print(f"Downloading: {url}")
        
        # 1. DOWNLOAD
        # We add --cookies-from-browser if needed later, but standard first
        subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", raw_path,
            url
        ], check=True, capture_output=True) # Capture output to hide logs unless error

        # 2. CROP
        print("Cropping...")
        subprocess.run([
            "ffmpeg",
            "-i", raw_path,
            "-vf", "crop=ih*(9/16):ih:(iw-ow)/2:0",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "copy",
            "-y",
            final_path
        ], check=True, capture_output=True)

        # 3. SEND
        background_tasks.add_task(delete_file, raw_path)
        background_tasks.add_task(delete_file, final_path)
        
        return FileResponse(final_path, media_type="video/mp4", filename="clip.mp4")

    except subprocess.CalledProcessError as e:
        # This catches yt-dlp or ffmpeg errors
        error_message = e.stderr.decode() if e.stderr else str(e)
        print(f"Server Error: {error_message}")
        # IMPORTANT: This sends a 500 error code, not 200 OK
        raise HTTPException(status_code=500, detail=f"Process Failed: {error_message}")
        
    except Exception as e:
        print(f"General Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))