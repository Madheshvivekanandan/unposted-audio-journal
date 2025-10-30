"""
Emotion analysis module for journal entries.
Analyzes emotional content, prosodic features, and generates follow-up questions.
"""

import warnings
from typing import Optional
import numpy as np
import librosa
from langdetect import detect, LangDetectException
from transformers import (
    pipeline,
    AutoTokenizer,
    T5ForConditionalGeneration,
)

# Constants
SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi"}
SENTIMENT_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"
LLM_MODEL = "google/flan-t5-base"
TEXT_MAX_LENGTH = 512  # FIX: This is used for text truncation
VALENCE_THRESHOLD = 0.3
AROUSAL_THRESHOLD = 0.3
ENERGY_NORMALIZATION = {"min": 0.02, "range": 0.05}
TEMPO_NORMALIZATION = {"center": 90, "range": 60}
PITCH_NORMALIZATION = {"center": 160, "range": 100}

# Global model instances (lazy-loaded)
_sentiment_analyzer = None
_generator_tokenizer = None
_generator_model = None


def _load_sentiment_model():
    """Lazily load the sentiment analysis model."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        print("Loading sentiment model...")
        _sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model=SENTIMENT_MODEL,
            device=-1,  # Use CPU
        )
    return _sentiment_analyzer


def _load_llm_models():
    """Lazily load the LLM models for follow-up generation."""
    global _generator_tokenizer, _generator_model
    if _generator_tokenizer is None or _generator_model is None:
        print("Loading LLM for follow-up generation...")
        _generator_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
        _generator_model = T5ForConditionalGeneration.from_pretrained(LLM_MODEL)


def detect_language(text: str) -> str:
    """
    Detect the language of the text with fallback to English.
    
    Args:
        text (str): Input text to analyze.
    
    Returns:
        str: Language code ('en', 'hi') or 'en' as default.
    """
    if not text or not isinstance(text, str):
        return "en"
    
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except (LangDetectException, Exception):
        return "en"


def analyze_emotion(text: str, language: Optional[str] = None) -> float:
    """
    Analyze the emotional content of text.
    
    Args:
        text (str): Input text to analyze.
        language (Optional[str]): Language code ('en', 'hi'). If None, auto-detects.
    
    Returns:
        float: Sentiment score between -1 (negative) and 1 (positive).
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    # Detect or validate language
    if language is None or language not in SUPPORTED_LANGUAGES:
        language = detect_language(text)
    
    # Truncate text to avoid model limits - FIX: Use TEXT_MAX_LENGTH (integer)
    text_truncated = text[:TEXT_MAX_LENGTH]
    
    try:
        sentiment_analyzer = _load_sentiment_model()
        result = sentiment_analyzer(text_truncated)[0]
        
        # Extract score and normalize
        score = float(result.get("score", 0.0))
        label = result.get("label", "").upper()
        
        # Adjust sign based on label
        if label in ["NEGATIVE", "NEG"]:
            score = -score
        
        # Clamp to [-1, 1] range
        return max(min(score, 1.0), -1.0)
    
    except Exception as e:
        print(f"Error in emotion analysis: {e}")
        return 0.0


def analyze_prosody(audio_path: str) -> float:
    """
    Analyze prosodic features of speech (energy, tempo, pitch).
    Language-agnostic as it analyzes acoustic properties.
    
    Args:
        audio_path (str): Path to the audio file.
    
    Returns:
        float: Arousal score between -1 (calm) and 1 (excited).
    
    Raises:
        ValueError: If audio file cannot be loaded.
    """
    import os
    
    if not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")
    
    try:
        # Load audio file
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            y, sr = librosa.load(audio_path, sr=None)
        
        if len(y) == 0:
            raise ValueError("Audio file is empty or invalid")
        
        # Extract prosodic features
        energy = np.mean(librosa.feature.rms(y=y)[0]) if len(y) > 0 else 0.0
        
        # Calculate tempo safely
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        except Exception:
            tempo = TEMPO_NORMALIZATION["center"]  # Fallback to neutral tempo
        
        # Calculate pitch safely
        try:
            pitch_values = librosa.yin(
                y,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
            )
            pitch_mean = np.nanmean(pitch_values) if len(pitch_values) > 0 else PITCH_NORMALIZATION["center"]
        except Exception:
            pitch_mean = PITCH_NORMALIZATION["center"]  # Fallback to neutral pitch
        
        # Normalize features to [-1, 1] range
        energy_score = _normalize_score(
            energy,
            ENERGY_NORMALIZATION["min"],
            ENERGY_NORMALIZATION["range"],
        )
        tempo_score = _normalize_score(
            tempo,
            TEMPO_NORMALIZATION["center"],
            TEMPO_NORMALIZATION["range"],
        )
        pitch_score = _normalize_score(
            pitch_mean,
            PITCH_NORMALIZATION["center"],
            PITCH_NORMALIZATION["range"],
        )
        
        # Weighted combination of features
        arousal = 0.5 * energy_score + 0.3 * tempo_score + 0.2 * pitch_score
        
        return max(min(arousal, 1.0), -1.0)
    
    except Exception as e:
        print(f"Error in prosody analysis: {e}")
        return 0.0


def _normalize_score(value: float, center: float, range_val: float) -> float:
    """
    Normalize a score to [-1, 1] range using min-max normalization.
    
    Args:
        value (float): Value to normalize.
        center (float): Center/expected value.
        range_val (float): Range around center.
    
    Returns:
        float: Normalized score in [-1, 1].
    """
    if range_val == 0:
        return 0.0
    normalized = (value - center) / range_val
    return max(min(normalized, 1.0), -1.0)


def _get_emotion_context(valence: float, arousal: float) -> str:
    """
    Generate emotional context description.
    
    Args:
        valence (float): Valence score [-1, 1].
        arousal (float): Arousal score [-1, 1].
    
    Returns:
        str: Description of emotional state.
    """
    valence_desc = ""
    if valence > VALENCE_THRESHOLD:
        valence_desc = "positive and "
    elif valence < -VALENCE_THRESHOLD:
        valence_desc = "challenging and "
    
    arousal_desc = ""
    if arousal > AROUSAL_THRESHOLD:
        arousal_desc = "energetic"
    elif arousal < -AROUSAL_THRESHOLD:
        arousal_desc = "calm"
    else:
        arousal_desc = "balanced"
    
    return valence_desc + arousal_desc


def generate_follow_up(
    text: str, 
    valence: float, 
    arousal: float, 
    language: Optional[str] = None
) -> str:
    """
    Generate a contextual follow-up question based on journal entry and emotions.
    Uses T5 model for multilingual question generation.
    
    Args:
        text (str): The journal entry text.
        valence (float): Emotional valence score [-1, 1].
        arousal (float): Emotional arousal score [-1, 1].
        language (Optional[str]): Language code ('en', 'hi'). Auto-detects if None.
    
    Returns:
        str: A contextually appropriate follow-up question.
    """
    if not text or not isinstance(text, str):
        return _get_fallback_question("en", valence)
    
    # Detect or validate language
    if language is None or language not in SUPPORTED_LANGUAGES:
        language = detect_language(text)
    
    # Get emotion context
    emotion_context = _get_emotion_context(valence, arousal)
    
    # Create language-specific prompt - FIX: Use TEXT_MAX_LENGTH (integer)
    text_sample = text[:TEXT_MAX_LENGTH]
    
    if language == "hi":
        prompt = (
            f"इस डायरी एंट्री से एक सहायक प्रश्न बनाएं। "
            f"भावना: {emotion_context}। टेक्स्ट: {text_sample}..."
        )
    else:
        prompt = (
            f"Generate a supportive follow-up question for this journal entry. "
            f"Emotion: {emotion_context}. Text: {text_sample}..."
        )
    
    try:
        _load_llm_models()
        
        # Generate question using T5
        inputs = _generator_tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True,
        )
        
        outputs = _generator_model.generate(
            inputs["input_ids"],
            max_length=100,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            top_k=50,
            top_p=0.95,
        )
        
        generated_text = _generator_tokenizer.decode(
            outputs[0], skip_special_tokens=True
        )
        
        # Clean up: take first line and remove artifacts
        question = generated_text.strip().split("\n")[0].strip()
        
        return question if question else _get_fallback_question(language, valence)
    
    except Exception as e:
        print(f"Error generating follow-up question: {e}")
        return _get_fallback_question(language, valence)


def _get_fallback_question(language: str, valence: float) -> str:
    """
    Get a fallback follow-up question based on language and emotional state.
    
    Args:
        language (str): Language code ('en', 'hi').
        valence (float): Emotional valence score.
    
    Returns:
        str: A fallback follow-up question.
    """
    if language == "hi":
        if valence > VALENCE_THRESHOLD:
            return "आपको और क्या बेहतर महसूस करा सकता है?"
        else:
            return "अपनी भावनाओं के बारे में और बताएं?"
    else:
        if valence > VALENCE_THRESHOLD:
            return "What else would make you feel even better?"
        else:
            return "Can you tell me more about how you're feeling?"
