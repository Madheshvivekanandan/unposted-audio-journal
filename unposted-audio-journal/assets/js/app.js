document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const views = {
        landing: document.getElementById('landing-view'),
        recording: document.getElementById('recording-view'),
        processing: document.getElementById('processing-view'),
        insights: document.getElementById('insights-view'),
        settings: document.getElementById('settings-view')
    };

    // Navigation buttons
    const recordButton = document.getElementById('record-button');
    const pauseButton = document.getElementById('pause-button');
    const stopButton = document.getElementById('stop-button');
    const cancelButton = document.getElementById('cancel-button');
    const newReflectionButton = document.getElementById('new-reflection-button');
    const settingsButton = document.getElementById('settings-button');
    const closeSettingsButton = document.getElementById('close-settings-button');
    const transcriptToggle = document.getElementById('transcript-toggle');
    const playButton = document.getElementById('play-button');

    // Settings page buttons
    const exportDataButton = document.getElementById('export-data-button');
    const deleteDataButton = document.getElementById('delete-data-button');

    // Starter options
    const starterOptions = document.querySelectorAll('.starter-option');
    const customStarter = document.querySelector('.custom-starter');

    // Timer element
    const timerElement = document.querySelector('.timer');

    // Audio recording variables
    let mediaRecorder;
    let audioChunks = [];
    let audioBlob;
    let audioUrl;
    let audioElement;
    let startTime;
    let pausedTime = 0;
    let timerInterval;
    let isRecording = false;
    let isPaused = false;
    let isCancelled = false;

    // Initialize calendar view
    initCalendar();

    // Event listeners
    recordButton?.addEventListener('click', startRecording);
    pauseButton?.addEventListener('click', togglePause);
    stopButton?.addEventListener('click', stopRecording);
    cancelButton?.addEventListener('click', cancelRecording);
    newReflectionButton?.addEventListener('click', () => showView('landing'));
    settingsButton?.addEventListener('click', () => showView('settings'));
    closeSettingsButton?.addEventListener('click', () => showView('landing'));
    playButton?.addEventListener('click', togglePlay);
    transcriptToggle?.addEventListener('click', toggleTranscript);

    // Settings button event listeners
    exportDataButton?.addEventListener('click', exportAllData);
    deleteDataButton?.addEventListener('click', deleteAllData);

    starterOptions.forEach(option => {
        option.addEventListener('click', function() {
            starterOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            if (customStarter) customStarter.value = '';
        });
    });

    if (customStarter) {
        customStarter.addEventListener('input', function() {
            if (this.value) {
                starterOptions.forEach(opt => opt.classList.remove('selected'));
            }
        });
    }

    // View management
    function showView(viewName) {
        for (const key in views) {
            views[key]?.classList.remove('active');
        }
        if (views[viewName]) {
            views[viewName].classList.add('active');
        }
    }

    // Recording functions
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener('stop', () => {
                // Only process audio if not cancelled
                if (!isCancelled) {
                    processAudio();
                }
                // Stop all audio tracks after recording stops
                stream.getTracks().forEach(track => track.stop());
            });

            mediaRecorder.start();
            isRecording = true;
            isPaused = false;
            isCancelled = false;
            startTime = Date.now();
            pausedTime = 0;

            // Initialize timer display
            if (timerElement) {
                timerElement.textContent = '00:00';
            }

            // Start timer - update every 100ms for smooth display
            startTimer();
            startWaveform(stream);
            showView('recording');
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Could not access microphone. Please check permissions and try again.');
        }
    }

    function togglePause() {
        if (!isRecording || !mediaRecorder) return;

        if (isPaused) {
            mediaRecorder.resume();
            isPaused = false;
            pauseButton.innerHTML = '<i class="fas fa-pause"></i>';
            // Adjust start time for the pause duration
            startTime = Date.now() - (pausedTime - startTime);
        } else {
            mediaRecorder.pause();
            isPaused = true;
            pauseButton.innerHTML = '<i class="fas fa-play"></i>';
            pausedTime = Date.now();
        }
    }

    function stopRecording() {
        if (!isRecording || !mediaRecorder) return;
        isCancelled = false;
        mediaRecorder.stop();
        clearInterval(timerInterval);
        isRecording = false;

        showView('processing');
    }

    function cancelRecording() {
        if (!isRecording || !mediaRecorder) return;
        isCancelled = true;
        mediaRecorder.stop();
        clearInterval(timerInterval);
        isRecording = false;

        // Stop all audio tracks
        mediaRecorder.stream?.getTracks().forEach(track => track.stop());

        showView('landing');
    }

    // Timer functions
    function startTimer() {
        // Update immediately
        updateTimer();

        // Update every 100ms for smooth display
        timerInterval = setInterval(updateTimer, 100);
    }

    function updateTimer() {
        if (!isRecording || !timerElement) return;

        const elapsed = isPaused ? pausedTime - startTime : Date.now() - startTime;
        const totalSeconds = Math.floor(elapsed / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        const displayMinutes = String(minutes).padStart(2, '0');
        const displaySeconds = String(seconds).padStart(2, '0');

        timerElement.textContent = `${displayMinutes}:${displaySeconds}`;
    }

    // Waveform display
    function startWaveform(stream) {
        const canvas = document.getElementById('waveform');
        if (!canvas) return;

        const canvasCtx = canvas.getContext('2d');
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioCtx.createAnalyser();

        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 256;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

        function drawWaveform() {
            if (!isRecording) return;
            requestAnimationFrame(drawWaveform);

            analyser.getByteTimeDomainData(dataArray);

            canvasCtx.fillStyle = '#f7fafc';
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

            canvasCtx.lineWidth = 2;
            canvasCtx.strokeStyle = '#3182ce';
            canvasCtx.beginPath();

            const sliceWidth = canvas.width / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = (v * canvas.height) / 2;

                if (i === 0) {
                    canvasCtx.moveTo(x, y);
                } else {
                    canvasCtx.lineTo(x, y);
                }
                x += sliceWidth;
            }

            canvasCtx.lineTo(canvas.width, canvas.height / 2);
            canvasCtx.stroke();
        }

        drawWaveform();
    }

    // Audio processing
    async function processAudio() {
        audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        audioUrl = URL.createObjectURL(audioBlob);
        audioElement = new Audio(audioUrl);

        // Prepare form data for backend processing
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        // Determine topic
        let topic = '';
        const selectedOption = document.querySelector('.starter-option.selected');
        if (selectedOption) {
            topic = selectedOption.textContent.trim();
        } else if (customStarter && customStarter.value.trim()) {
            topic = customStarter.value.trim();
        } else {
            topic = 'General reflection';
        }
        formData.append('topic', topic);

        try {
            showView('processing');
            const response = await fetch('http://localhost:3000/api/process', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayInsights(data, topic);
        } catch (error) {
            console.error('Error processing audio:', error);
            alert('Sorry, there was an error processing your audio. Please try again.\n\nError: ' + error.message);
            showView('landing');
        }
    }

    // Display insights
    function displayInsights(data, topic) {
        try {
            if (!data.transcript || !data.bullets || !data.emotion || !data.nextPrompt) {
                throw new Error('Invalid data format received from server.');
            }

            // Transcript - SHOW FULL TEXT BY DEFAULT
            const transcriptContent = document.getElementById('transcript-content');
            if (transcriptContent) {
                transcriptContent.textContent = data.transcript;
                // Remove collapsed class to show full text
                transcriptContent.classList.remove('collapsed');
            }

            // Update toggle button to show "up" chevron (since content is expanded)
            if (transcriptToggle) {
                transcriptToggle.innerHTML = '<i class="fas fa-chevron-up"></i>';
            }

            // Reflection bullets
            const reflectionList = document.querySelector('.reflection-bullets');
            if (reflectionList) {
                reflectionList.innerHTML = '';
                data.bullets.forEach(bullet => {
                    const li = document.createElement('li');
                    li.textContent = bullet.text;
                    li.classList.add(bullet.type || 'neutral');
                    reflectionList.appendChild(li);
                });
            }

            // Emotion point
            const emotionPoint = document.querySelector('.emotion-point');
            if (emotionPoint) {
                const energy = (data.emotion.energy || 0);
                const valence = (data.emotion.valence || 0);
                emotionPoint.style.left = `${(energy + 1) * 50}%`;
                emotionPoint.style.top = `${(1 - valence) * 50}%`;
            }

            // Emotion summary
            const emotionSummary = document.querySelector('.emotion-summary');
            if (emotionSummary) {
                emotionSummary.textContent = data.emotion.summary || 'Your reflection captured.';
            }

            // Next prompt
            const nextPrompt = document.querySelector('.next-prompt');
            if (nextPrompt) {
                nextPrompt.textContent = data.nextPrompt || 'Keep reflecting!';
            }

            // Audio player setup
            const durationElement = document.querySelector('.duration');
            if (durationElement && audioElement) {
                audioElement.addEventListener('loadedmetadata', () => {
                    const minutes = Math.floor(audioElement.duration / 60);
                    const seconds = Math.floor(audioElement.duration % 60);
                    durationElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                });
            }

            const progressBar = document.querySelector('.progress');
            if (progressBar && audioElement) {
                audioElement.addEventListener('timeupdate', () => {
                    if (audioElement.duration > 0) {
                        const progress = (audioElement.currentTime / audioElement.duration) * 100;
                        progressBar.style.width = `${progress}%`;
                    }
                });
            }

            // Save journal entry to local storage
            saveJournalEntry({
                date: new Date().toISOString(),
                topic: topic,
                transcript: data.transcript,
                bullets: data.bullets,
                emotion: data.emotion,
                nextPrompt: data.nextPrompt,
                audioBlobUrl: audioUrl,
            });

            // Update calendar
            initCalendar();

            showView('insights');
        } catch (error) {
            console.error('Error displaying insights:', error);
            alert('There was an error processing the response. Please try again.\n\nError: ' + error.message);
            showView('landing');
        }
    }

    // Audio player toggle
    function togglePlay() {
        if (!audioElement) return;
        if (audioElement.paused) {
            audioElement.play();
            if (playButton) playButton.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            audioElement.pause();
            if (playButton) playButton.innerHTML = '<i class="fas fa-play"></i>';
        }
    }

    // Transcript toggle
    function toggleTranscript() {
        const transcriptContent = document.getElementById('transcript-content');
        if (!transcriptContent) return;

        transcriptContent.classList.toggle('collapsed');
        if (transcriptToggle) {
            if (transcriptContent.classList.contains('collapsed')) {
                transcriptToggle.innerHTML = '<i class="fas fa-chevron-down"></i>';
            } else {
                transcriptToggle.innerHTML = '<i class="fas fa-chevron-up"></i>';
            }
        }
    }

    // Calendar rendering
    function initCalendar() {
        const calendarView = document.querySelector('.calendar-view');
        if (!calendarView) return;
        calendarView.innerHTML = '';

        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();

        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const lastDayOfMonth = new Date(year, month + 1, 0).getDate();

        const journalDays = getJournalDays();

        // Add day headers: Su, Mo, Tu, We, Th, Fr, Sa
        const dayNames = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
        dayNames.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.textContent = day;
            dayHeader.classList.add('calendar-header');
            calendarView.appendChild(dayHeader);
        });

        // Add empty cells for days before the 1st
        for (let i = 0; i < firstDayOfMonth; i++) {
            const emptyDay = document.createElement('div');
            calendarView.appendChild(emptyDay);
        }

        // Add calendar days
        for (let i = 1; i <= lastDayOfMonth; i++) {
            const day = document.createElement('div');
            day.textContent = i;
            day.classList.add('calendar-day');

            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;

            if (journalDays.includes(dateStr)) {
                day.classList.add('journal-day');
            }

            calendarView.appendChild(day);
        }
    }

    // Local storage functions
    function saveJournalEntry(entry) {
        let entries = JSON.parse(localStorage.getItem('journalEntries') || '[]');
        entries.push(entry);
        localStorage.setItem('journalEntries', JSON.stringify(entries));
    }

    function getJournalDays() {
        const entries = JSON.parse(localStorage.getItem('journalEntries') || '[]');
        return entries.map(entry => {
            const date = new Date(entry.date);
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        });
    }

    // Settings: Export all data
    function exportAllData() {
        try {
            const entries = JSON.parse(localStorage.getItem('journalEntries') || '[]');

            if (entries.length === 0) {
                alert('No journal entries to export.');
                return;
            }

            // Create export data object
            const exportData = {
                exportDate: new Date().toISOString(),
                totalEntries: entries.length,
                appVersion: '1.0.0',
                entries: entries.map(entry => ({
                    date: entry.date,
                    topic: entry.topic,
                    transcript: entry.transcript,
                    bullets: entry.bullets,
                    emotion: entry.emotion,
                    nextPrompt: entry.nextPrompt
                    // Note: audioBlobUrl is excluded as it's a temporary browser URL
                }))
            };

            // Convert to JSON string with pretty formatting
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });

            // Create download link
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `unposted-journal-${new Date().toISOString().split('T')[0]}.json`;

            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Clean up URL
            URL.revokeObjectURL(url);

            alert(`✅ Successfully exported ${entries.length} journal ${entries.length === 1 ? 'entry' : 'entries'}!`);
        } catch (error) {
            console.error('Error exporting data:', error);
            alert('❌ Failed to export data. Please try again.');
        }
    }

    // Settings: Delete all data
    function deleteAllData() {
        const entries = JSON.parse(localStorage.getItem('journalEntries') || '[]');

        if (entries.length === 0) {
            alert('No data to delete.');
            return;
        }

        // Confirm deletion
        const confirmDelete = confirm(
            `⚠️ Warning: This will permanently delete all ${entries.length} journal ${entries.length === 1 ? 'entry' : 'entries'}.\n\n` +
            'This action cannot be undone. Are you sure you want to continue?'
        );

        if (confirmDelete) {
            // Double confirmation for safety
            const doubleConfirm = confirm(
                '🚨 Final confirmation: Delete ALL journal data permanently?'
            );

            if (doubleConfirm) {
                try {
                    // Clear all journal data from localStorage
                    localStorage.removeItem('journalEntries');

                    // Refresh calendar to show empty state
                    initCalendar();

                    alert('✅ All journal data has been deleted successfully.');

                    // Return to landing page
                    showView('landing');
                } catch (error) {
                    console.error('Error deleting data:', error);
                    alert('❌ Failed to delete data. Please try again.');
                }
            }
        }
    }

});
