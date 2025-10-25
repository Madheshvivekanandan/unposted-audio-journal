import whisper

print("Loading Whisper model...")
model = whisper.load_model("base")

def transcribe_audio(file_path):
    result = model.transcribe(file_path)
    transcript = result['text'].strip()
    
    if len(transcript) < 5:
        raise ValueError("Could not transcribe properly")

    return transcript
