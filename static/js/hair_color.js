// DOM Elements
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('startCamera');
const stopBtn = document.getElementById('stopCamera');
const captureBtn = document.getElementById('capturePhoto');

let stream = null;
let selectedColor = null;

// --- Color Swatch Selection ---
document.querySelectorAll('.color-swatch').forEach(swatch => {
    swatch.addEventListener('click', () => {
        const color = swatch.getAttribute('data-color');
        selectedColor = color === '#FFFFFF' ? null : color;
    });
});

// --- Camera Functions ---
startBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();
    } catch (err) {
        alert('Could not access camera: ' + err.message);
    }
});

stopBtn.addEventListener('click', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
});

// --- Core Hair Color Changing Logic ---
captureBtn.addEventListener('click', () => {
    if (!video.videoWidth) {
        alert('Please start the camera first.');
        return;
    }
    if (!selectedColor) {
        alert('Please select a color from the palette.');
        return;
    }

    // 1. Capture the current frame from the video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // 2. Get the pixel data
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    // 3. Convert the selected color from Hex to RGB values
    const r_target = parseInt(selectedColor.slice(1,3), 16);
    const g_target = parseInt(selectedColor.slice(3,5), 16);
    const b_target = parseInt(selectedColor.slice(5,7), 16);

    // 4. Process each pixel
    for (let i = 0; i < data.length; i += 4) {
        let r = data[i];
        let g = data[i+1];
        let b = data[i+2];
        
        // Simple heuristic to detect hair pixels (based on brown/black/dark tones)
        // This is the "non-ML" magic part. It works best on typical hair colors.
        const isHair = (r < 150 && g < 150 && b < 150) || 
                       (r > 50 && r < 200 && g > 30 && g < 150 && b > 20 && b < 120);
        
        if (isHair) {
            // Blend the original pixel's brightness with the new color
            const brightness = (r + g + b) / 3;
            const blendFactor = 0.7; // 70% new color, 30% original brightness
            data[i] = r_target * blendFactor + brightness * (1 - blendFactor);
            data[i+1] = g_target * blendFactor + brightness * (1 - blendFactor);
            data[i+2] = b_target * blendFactor + brightness * (1 - blendFactor);
        }
    }
    
    // 5. Put the modified pixel data back onto the canvas
    ctx.putImageData(imageData, 0, 0);
    
    // 6. Show the result and hide the video feed
    video.style.display = 'none';
    canvas.style.display = 'block';
});