from transformers import pipeline
import librosa
import numpy as np

print("Loading sentiment model...")
sentiment_analyzer = pipeline("sentiment-analysis")

def analyze_emotion(text):
    result = sentiment_analyzer(text[:512])[0]
    return result['score'] if result['label'] == 'POSITIVE' else -result['score']


def analyze_prosody(audio_path):
    y, sr = librosa.load(audio_path, sr=None)

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitch_vals = [pitches[magnitudes[:, t].argmax(), t]
                  for t in range(pitches.shape[1])
                  if pitches[magnitudes[:, t].argmax(), t] > 0]

    energy = np.mean(librosa.feature.rms(y=y)[0])
    arousal = min(max((energy - 0.02) / 0.05, -1), 1)

    return arousal


def generate_follow_up(text, valence, arousal):
    prompts = {
        "positive_high": "What made today feel uplifting?",
        "positive_low": "What calm moment do you want more of?",
        "negative_high": "What support do you need right now?",
        "negative_low": "What small action could improve tomorrow?"
    }

    if valence > 0 and arousal > 0: return prompts["positive_high"]
    if valence > 0 and arousal <= 0: return prompts["positive_low"]
    if valence <= 0 and arousal > 0: return prompts["negative_high"]
    return prompts["negative_low"]
