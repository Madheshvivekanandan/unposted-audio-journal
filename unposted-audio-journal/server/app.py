from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from datetime import datetime

from models.speech_to_text import transcribe_audio
from models.insights import generate_insights
from models.emotion import analyze_emotion, analyze_prosody, generate_follow_up
from utils.file_manager import save_audio

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file_path = save_audio(request.files['audio'])

        transcript = transcribe_audio(file_path)
        insights = generate_insights(transcript)
        valence = analyze_emotion(transcript)
        arousal = analyze_prosody(file_path)
        follow_up = generate_follow_up(transcript, valence, arousal)

        result = {
            'transcript': transcript,
            'insights': insights,
            'emotion': {'valence': float(valence), 'arousal': float(arousal)},
            'follow_up': follow_up
        }

        return jsonify(result)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
