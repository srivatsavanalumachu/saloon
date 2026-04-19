document.addEventListener('DOMContentLoaded', function() {
    const captureBtn = document.getElementById('capture-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const resultContainer = document.getElementById('result-container');

    captureBtn.addEventListener('click', function() {
        // Capture current frame from video feed
        const videoFeed = document.getElementById('video-feed');
        const canvas = document.createElement('canvas');
        const img = new Image();
        
        img.crossOrigin = 'Anonymous';
        img.onload = function() {
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob(function(blob) {
                const formData = new FormData();
                formData.append('image', blob, 'captured.jpg');
                
                showLoading();
                fetch('/detect_shape', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showError(data.error);
                    } else {
                        showResult(data);
                    }
                })
                .catch(error => {
                    showError('Error analyzing image');
                    console.error('Error:', error);
                });
            }, 'image/jpeg');
        };
        img.src = videoFeed.src;
    });

    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const formData = new FormData();
            formData.append('image', e.target.files[0]);
            
            showLoading();
            fetch('/detect_shape', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                } else {
                    showResult(data);
                }
            })
            .catch(error => {
                showError('Error analyzing image');
                console.error('Error:', error);
            });
        }
    });

    function showLoading() {
        resultContainer.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Analyzing your face shape...</p>
            </div>
        `;
    }

    function showError(message) {
        resultContainer.innerHTML = `
            <div class="error">
                <p>❌ ${message}</p>
                <p>Please try again with a clear face image.</p>
            </div>
        `;
    }

    function showResult(data) {
        resultContainer.innerHTML = `
            <div class="result-card">
                <h3>Face Shape Detected:</h3>
                <div class="shape-badge">${data.face_shape.toUpperCase()}</div>
                <div class="confidence">Confidence: ${(data.confidence * 100).toFixed(1)}%</div>
                
                <h3>Recommended Hairstyle:</h3>
                <div class="hairstyle-name">${data.recommendation.name}</div>
                <p class="hairstyle-desc">${data.recommendation.description}</p>
                
                <a href="/get_recommendation/${data.face_shape}" class="details-btn">View Details</a>
            </div>
        `;
    }
});