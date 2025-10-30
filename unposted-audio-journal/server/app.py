from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from datetime import datetime
from models.speech_to_text import transcribe_audio, SUPPORTED_LANGUAGES
from models.insights import generate_insights
from models.emotion import analyze_emotion, analyze_prosody, generate_follow_up
from utils.file_manager import save_audio, cleanup_old_files

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Clean up files older than 24 hours on startup
cleanup_old_files(UPLOAD_FOLDER, hours=24)

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Return list of supported languages for transcription."""
    return jsonify(languages=SUPPORTED_LANGUAGES)

@app.route('/api/process', methods=['POST'])
def process_audio():
    try:
        if 'audio' not in request.files:
            return jsonify(error="No audio file provided"), 400
        
        audio_file = request.files['audio']
        filepath = save_audio(audio_file)
        
        language_code = request.form.get('language', 'auto')
        topic = request.form.get('topic', '')

        # Transcribe audio
        transcript = transcribe_audio(filepath, language_code)
        
        # Generate insights
        insights = generate_insights(transcript, language=language_code if language_code != 'auto' else None)

        # Analyze emotions and prosody
        valence = analyze_emotion(transcript)
        arousal = analyze_prosody(filepath)
        followup = generate_follow_up(transcript, valence, arousal)

        # Prepare emotion summary for UI
        emotion_summary = get_emotion_summary(valence, arousal)

        # Prepare bullet types for insights
        result_bullets = []
        for insight in insights:
            bullet_type = get_bullet_type(insight, valence)
            result_bullets.append({"text": insight, "type": bullet_type})

        result = {
            "transcript": transcript,
            "bullets": result_bullets,
            "emotion": {
                "valence": float(valence),
                "arousal": float(arousal),
                "energy": float(arousal),  # energy mapped from arousal for UI use
                "summary": emotion_summary
            },
            "nextPrompt": followup,
            "topic": topic
        }

        return jsonify(result)
    
    except Exception as e:
        print("Error:", e)
        return jsonify(error=str(e)), 500

def get_emotion_summary(valence, arousal):
    """Generate a human-readable summary of the emotional state."""
    if valence > 0.3:
        if arousal > 0.3:
            return "Your reflection shows excitement and positivity."
        elif arousal < -0.3:
            return "You seem content and peaceful."
        else:
            return "You're expressing positive feelings in a balanced way."
    elif valence < -0.3:
        if arousal > 0.3:
            return "There's intensity and concern in your voice."
        elif arousal < -0.3:
            return "You're expressing some heavy emotions calmly."
        else:
            return "You're processing some challenging feelings."
    else:
        if arousal > 0.3:
            return "You're speaking with energy and engagement."
        elif arousal < -0.3:
            return "Your tone is thoughtful and measured."
        else:
            return "You're expressing yourself in a balanced way."

def get_bullet_type(insight, valence):
    """Determine the type of insight bullet: positive, negative, or neutral."""
    insight_sentiment = analyze_emotion(insight)
    if insight_sentiment > 0.3:
        return "positive"
    elif insight_sentiment < -0.3:
        return "negative"
    else:
        return "neutral"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
