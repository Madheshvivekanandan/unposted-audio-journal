import whisper
import os
from typing import Optional

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "auto": "Auto Detect"
}

print("Loading Whisper model...")
model = whisper.load_model("medium", device="cpu")

def transcribe_audio(filepath: str, language_code: Optional[str] = None) -> str:
    """
    Transcribe audio file to text with language support.
    
    Args:
        filepath (str): Path to the audio file.
        language_code (Optional[str]): Language code ('en', 'hi', or 'auto'). Defaults to None.
    
    Returns:
        str: Transcribed text.
    
    Raises:
        ValueError: If file not found, unsupported language, or transcription fails.
    """
    if not os.path.exists(filepath):
        raise ValueError("Audio file not found")

    valid_languages = ", ".join(f"{code} ({name})" for code, name in SUPPORTED_LANGUAGES.items())

    if language_code and language_code != "auto" and language_code not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language code. Use one of: {valid_languages}")

    try:
        transcription_options = {
            "fp16": False,  # Use FP32 on CPU
            "temperature": 0.0  # Disable randomness in decoding for consistent results
        }
        if language_code and language_code != "auto":
            transcription_options["language"] = language_code

        result = model.transcribe(filepath, **transcription_options)
        transcript = result["text"].strip()

        if not transcript:
            raise ValueError("No speech detected in the audio")

        return transcript

    except Exception as e:
        raise ValueError(f"Transcription failed: {e}")
