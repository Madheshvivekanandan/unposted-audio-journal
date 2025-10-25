import os
from datetime import datetime

UPLOAD_FOLDER = "uploads"

def save_audio(file):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(UPLOAD_FOLDER, f"journal_{timestamp}.wav")
    file.save(file_path)
    return file_path
