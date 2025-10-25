let mediaRecorder;
let audioChunks = [];
let startTime;
let timerInterval;
let isRecording = false;

const recordBtn = document.getElementById('recordBtn');
const timer = document.getElementById('timer');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const errorDiv = document.getElementById('error');
const resetBtn = document.getElementById('resetBtn');

recordBtn.addEventListener('click', toggleRecording);
resetBtn.addEventListener('click', resetApp);

async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await processAudio(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        recordBtn.textContent = 'Stop Recording';
        recordBtn.classList.add('recording');

        startTime = Date.now();
        timerInterval = setInterval(updateTimer, 100);

        // Auto-stop after 90 seconds
        setTimeout(() => {
            if (isRecording) {
                stopRecording();
            }
        }, 90000);

    } catch (error) {
        showError('Could not access microphone. Please grant permission.');
        console.error(error);
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        recordBtn.textContent = 'Start Recording';
        recordBtn.classList.remove('recording');
        clearInterval(timerInterval);
    }
}

function updateTimer() {
    const elapsed = Date.now() - startTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    timer.textContent = `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

async function processAudio(audioBlob) {
    loading.style.display = 'block';
    errorDiv.style.display = 'none';

    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
        const response = await fetch('http://localhost:3000/process', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Processing failed');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        showError('Failed to process audio. Please try again.');
        console.error(error);
    } finally {
        loading.style.display = 'none';
    }
}

function displayResults(data) {
    // Transcript
    document.getElementById('transcript').textContent = data.transcript;

    // Insights
    const insightsList = document.getElementById('insights');
    insightsList.innerHTML = '';
    data.insights.forEach(insight => {
        const li = document.createElement('li');
        li.textContent = insight;
        insightsList.appendChild(li);
    });

    // Emotion
    const valence = (data.emotion.valence + 1) / 2 * 100; // Convert -1:1 to 0:100
    const arousal = (data.emotion.arousal + 1) / 2 * 100;

    document.getElementById('valence-bar').style.width = valence + '%';
    document.getElementById('arousal-bar').style.width = arousal + '%';

    // Follow-up
    document.getElementById('followUp').textContent = data.follow_up;

    // Show results
    results.style.display = 'block';
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function resetApp() {
    results.style.display = 'none';
    errorDiv.style.display = 'none';
    timer.textContent = '00:00';
}