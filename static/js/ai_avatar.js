// DOM Elements
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('startCamera');
const stopBtn = document.getElementById('stopCamera');
const captureBtn = document.getElementById('captureBtn');
const downloadBtn = document.getElementById('downloadBtn');
const shareInstagramBtn = document.getElementById('shareInstagramBtn');
const resultContainer = document.getElementById('resultContainer');
const actionButtons = document.getElementById('actionButtons');
const statusDiv = document.getElementById('statusMessage');

let stream = null;
let currentAvatarData = null;

// --- Camera Functions ---
startBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();
        canvas.style.display = 'none';
        video.style.display = 'block';
        statusDiv.innerHTML = '';
    } catch (err) {
        statusDiv.innerHTML = `<div class="status-message error">❌ Camera error: ${err.message}</div>`;
    }
});

stopBtn.addEventListener('click', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
});

// --- Capture and Generate Avatar ---
captureBtn.addEventListener('click', async () => {
    if (!video.videoWidth) {
        statusDiv.innerHTML = '<div class="status-message error">❌ Please start the camera first.</div>';
        return;
    }

    statusDiv.innerHTML = '<div class="status-message">🎨 AI is creating your avatar... please wait.</div>';
    
    // Capture frame from video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob and send to backend
    canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');
        
        try {
            const response = await fetch('/api/generate-avatar', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                currentAvatarData = data.image;
                const avatarImg = document.createElement('img');
                avatarImg.src = 'data:image/jpeg;base64,' + data.image;
                avatarImg.classList.add('avatar-result');
                resultContainer.innerHTML = '';
                resultContainer.appendChild(avatarImg);
                actionButtons.style.display = 'flex';
                statusDiv.innerHTML = '<div class="status-message success">✅ Avatar created successfully!</div>';
            } else {
                statusDiv.innerHTML = `<div class="status-message error">❌ Error: ${data.error}</div>`;
            }
        } catch (err) {
            statusDiv.innerHTML = `<div class="status-message error">❌ Network error: ${err.message}</div>`;
        }
    }, 'image/jpeg');
});

// --- Download Avatar ---
downloadBtn.addEventListener('click', () => {
    if (currentAvatarData) {
        const link = document.createElement('a');
        link.download = 'ai_avatar.jpg';
        link.href = 'data:image/jpeg;base64,' + currentAvatarData;
        link.click();
    }
});

// --- Share to Instagram ---
shareInstagramBtn.addEventListener('click', async () => {
    if (!currentAvatarData) {
        statusDiv.innerHTML = '<div class="status-message error">❌ No avatar to share.</div>';
        return;
    }
    
    statusDiv.innerHTML = '<div class="status-message">📤 Sharing to Instagram...</div>';
    
    try {
        const response = await fetch('/api/share-instagram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: currentAvatarData })
        });
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = '<div class="status-message success">✅ Shared to Instagram successfully!</div>';
        } else {
            statusDiv.innerHTML = `<div class="status-message error">❌ Instagram error: ${data.error}</div>`;
        }
    } catch (err) {
        statusDiv.innerHTML = `<div class="status-message error">❌ Network error: ${err.message}</div>`;
    }
});