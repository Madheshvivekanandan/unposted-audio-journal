# Unposted - Private Audio Journaling Assistant

A simple audio journaling app that provides instant AI-powered insights.

## Features
✅ Browser-based audio recording (60-90 seconds)
✅ Automatic speech-to-text transcription
✅ 3 key reflection bullets extracted from your entry
✅ Emotion analysis (positivity & energy levels)
✅ Personalized follow-up prompts
✅ Privacy-first: local processing

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The first run will download required models (~1-2GB):
- Whisper base model (~140MB)
- BART summarization model (~1.6GB)
- DistilBERT sentiment model (~250MB)

### 2. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:3000`

### 3. Use the App

1. Open your browser and navigate to `http://localhost:3000`
2. Click "Start Recording" and speak for 60-90 seconds
3. Click "Stop Recording" (or it auto-stops after 90 seconds)
4. Wait for processing (~10-30 seconds depending on your hardware)
5. View your insights, emotion analysis, and follow-up prompt!

## System Requirements

**Minimum:**
- Python 3.8+
- 8GB RAM
- 2GB free disk space
- Modern browser (Chrome, Firefox, Edge)

**Recommended:**
- 16GB RAM for smoother experience
- GPU (optional, but speeds up processing)

## Model Sizes

You can change the Whisper model size in `app.py` (line 18):
- `tiny` - Fastest, least accurate (~75MB)
- `base` - Good balance (~140MB) **[DEFAULT]**
- `small` - Better accuracy (~460MB)
- `medium` - Best accuracy (~1.5GB)

## Troubleshooting

### Microphone Access
Make sure to allow microphone permissions in your browser when prompted.

### Slow Processing
- Use a smaller Whisper model ('tiny' or 'base')
- Close other applications to free up RAM
- Consider using GPU acceleration (requires PyTorch with CUDA)

### Model Download Issues
If models fail to download, check your internet connection and try again.

## Privacy

- Audio is processed locally on your machine
- No data is sent to external servers
- Recordings are saved in the `uploads/` folder (optional - you can delete them)

## Project Structure

```
unposted-audio-journal/
│
├── index.html
│
├── assets/
│   ├── css/
│   │   └── styles.css
│   │
│   ├── js/
│       └── script.js
│
└── server/        <-- (backend folder)
    │
    ├─ app.py
    ├─ requirements.txt
    ├─ uploads/               # Saved audio files
    │
    ├─ models/                # ML/NLP model loading + processing
    │   ├─ __init__.py
    │   ├─ speech_to_text.py
    │   ├─ insights.py
    │   ├─ emotion.py
    │
    ├─ utils/
        ├─ __init__.py
        ├─ file_manager.py
```

## Next Steps / Enhancements

- [ ] Add local storage for journal history
- [ ] Export entries to JSON/CSV
- [ ] Implement streak counter
- [ ] Add conversation starter prompts
- [ ] Multi-language support
- [ ] On-device model optimization (ONNX)
- [ ] Progressive Web App (PWA) for mobile
