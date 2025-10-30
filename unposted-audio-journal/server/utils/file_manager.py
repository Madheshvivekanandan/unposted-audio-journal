import os
import time
from datetime import datetime

UPLOAD_FOLDER = "uploads"

def save_audio(file) -> str:
    """
    Save uploaded audio file to UPLOAD_FOLDER with a timestamp.
    
    Args:
        file: File object from request.files
    
    Returns:
        str: Path to saved audio file
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filepath = os.path.join(UPLOAD_FOLDER, f"journal_{timestamp}.wav")
    file.save(filepath)
    return filepath

def cleanup_old_files(folder: str = UPLOAD_FOLDER, hours: int = 24):
    """
    Delete files older than the given number of hours in the specified folder.
    
    Args:
        folder (str): Path to folder to clean up
        hours (int): Age of files in hours to delete
    """
    now = time.time()
    cutoff = now - (hours * 3600)

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff:
                try:
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
