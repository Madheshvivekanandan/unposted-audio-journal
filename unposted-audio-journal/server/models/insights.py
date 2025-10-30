from transformers import pipeline
from langdetect import detect
import re

# Language-specific model configs and fallback prompts
LANGUAGE_CONFIGS = {
    "en": {
        "model": "facebook/bart-large-cnn",
        "fallback_prompts": [
            "Reflect on your day.",
            "Consider how you felt during these moments.",
            "Think about what you learned today."
        ]
    },
    "hi": {
        "model": "google/mt5-small",
        "fallback_prompts": [
            "अपने दिन पर विचार करें।",
            "इन पलों के दौरान आपने कैसा महसूस किया।",
            "आज आपने क्या सीखा, उसके बारे में सोचें।"
        ]
    }
}

# Initialize summarization pipelines for each language
print("Loading summarizers...")
summarizers = {}
for lang, config in LANGUAGE_CONFIGS.items():
    summarizers[lang] = pipeline("summarization", model=config["model"], device=-1)  # CPU device

def detect_language(text: str) -> str:
    """
    Detect language of the text with fallback to English.
    """
    try:
        lang = detect(text)
        if lang in LANGUAGE_CONFIGS:
            return lang
        else:
            return "en"
    except:
        return "en"

def clean_text(text: str) -> str:
    """
    Clean and normalize text for better sentence splitting.
    Converts various punctuation marks to periods.
    """
    text = re.sub(r"[।।?]", ".", text)
    return text

def get_sentences(text: str, min_length: int = 20) -> list[str]:
    """
    Extract sentences from text with proper handling of different sentence endings.
    Returns a list of sentences longer than min_length.
    """
    text = clean_text(text)
    sentences = [s.strip() for s in re.split(r"\.\s*", text) if len(s.strip()) >= min_length]
    return sentences

def generate_insights(text: str, language: str = None) -> list[str]:
    """
    Generate 3 insights from text in specified language.
    Returns fallback prompts if text is empty.
    """
    if not text:
        return LANGUAGE_CONFIGS["en"]["fallback_prompts"][:3]

    if language is None or language not in LANGUAGE_CONFIGS:
        language = detect_language(text)

    summarizer = summarizers.get(language)
    config = LANGUAGE_CONFIGS[language]

    sentences = get_sentences(text, 20)

    insights = []
    try:
        if len(sentences) >= 3 and len(text) > 100:
            summary_results = summarizer(text, max_length=100, min_length=30)
            summary_text = summary_results[0]["summary_text"]
            sentences = get_sentences(summary_text, 20)
    except Exception as e:
        print("Summarization error:", e)

    # Keep first 3 sentences or fallback prompts if not enough
    while len(sentences) < 3 and len(text) >= 100:
        sentences.append(config["fallback_prompts"][len(sentences) % len(config["fallback_prompts"])])

    insights = sentences[:3]

    # Fill remaining slots with fallback prompts if needed
    while len(insights) < 3:
        prompt_index = len(insights) % len(config["fallback_prompts"])
        insights.append(config["fallback_prompts"][prompt_index])

    return insights
