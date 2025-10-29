import whisper
import os

print("Loading Whisper model...")
# Use smaller model for CPU, configure for better performance
model = whisper.load_model("base", device="cpu")

def transcribe_audio(file_path):
    if not os.path.exists(file_path):
        raise ValueError("Audio file not found")
        
    try:
        # Configure transcription parameters for better reliability
        result = model.transcribe(
            file_path,
            fp16=False,  # Ensure FP32 on CPU
            language='en',  # Specify English for better accuracy
            temperature=0.0  # Remove randomness in decoding
        )
        transcript = result['text'].strip()
        
        if not transcript:
            raise ValueError("No speech detected in the audio")
        
        return transcript
    except Exception as e:
        raise ValueError(f"Transcription failed: {str(e)}")
