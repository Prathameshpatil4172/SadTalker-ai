// SadTalker Flask UI - JavaScript

// File upload handling
const sourceImageInput = document.getElementById('sourceImageInput');
const sourceImageArea = document.getElementById('sourceImageArea');
const sourceImagePreview = document.getElementById('sourceImagePreview');
const sourcePlaceholder = document.getElementById('sourcePlaceholder');
const sourceActions = document.getElementById('sourceActions');

const audioInput = document.getElementById('audioInput');
const audioArea = document.getElementById('audioArea');
const audioPreview = document.getElementById('audioPreview');
const audioPlaceholder = document.getElementById('audioPlaceholder');
const audioName = document.getElementById('audioName');

const videoInput = document.getElementById('videoInput');
const videoArea = document.getElementById('videoArea');
const videoPreview = document.getElementById('videoPreview');
const videoPlaceholder = document.getElementById('videoPlaceholder');
const refVideo = document.getElementById('refVideo');
const closeVideo = document.getElementById('closeVideo');

// Slider value updates
const poseStyle = document.getElementById('poseStyle');
const poseValue = document.getElementById('poseValue');
const expWeight = document.getElementById('expWeight');
const expressionValue = document.getElementById('expressionValue');
const batchSize = document.getElementById('batchSize');
const batchValue = document.getElementById('batchValue');

// Update slider displays
poseStyle.addEventListener('input', () => {
    poseValue.textContent = poseStyle.value;
});

expWeight.addEventListener('input', () => {
    expressionValue.textContent = parseFloat(expWeight.value).toFixed(1);
});

batchSize.addEventListener('input', () => {
    batchValue.textContent = batchSize.value;
});

// Store uploaded file info
let uploadedFiles = {
    image: null,
    audio: null,
    video: null
};

// ==================== SOURCE IMAGE UPLOAD ====================

sourceImageArea.addEventListener('click', () => sourceImageInput.click());

sourceImageArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    sourceImageArea.classList.add('dragover');
});

sourceImageArea.addEventListener('dragleave', () => {
    sourceImageArea.classList.remove('dragover');
});

sourceImageArea.addEventListener('drop', (e) => {
    e.preventDefault();
    sourceImageArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
        handleImageUpload(files[0]);
    }
});

sourceImageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleImageUpload(e.target.files[0]);
    }
});

function handleImageUpload(file) {
    // Show preview immediately
    const reader = new FileReader();
    reader.onload = (e) => {
        sourceImagePreview.src = e.target.result;
        sourceImagePreview.classList.remove('hidden');
        sourcePlaceholder.classList.add('hidden');
        sourceActions.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
    
    // Upload to server
    uploadFile(file, 'image');
}

function clearImage() {
    sourceImagePreview.src = '';
    sourceImagePreview.classList.add('hidden');
    sourcePlaceholder.classList.remove('hidden');
    sourceActions.classList.add('hidden');
    sourceImageInput.value = '';
    uploadedFiles.image = null;
}

// ==================== AUDIO UPLOAD ====================

audioArea.addEventListener('click', () => audioInput.click());

audioArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    audioArea.classList.add('dragover');
});

audioArea.addEventListener('dragleave', () => {
    audioArea.classList.remove('dragover');
});

audioArea.addEventListener('drop', (e) => {
    e.preventDefault();
    audioArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('audio/')) {
        handleAudioUpload(files[0]);
    }
});

audioInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleAudioUpload(e.target.files[0]);
    }
});

function handleAudioUpload(file) {
    audioName.textContent = file.name;
    audioPreview.classList.remove('hidden');
    audioPlaceholder.classList.add('hidden');
    uploadFile(file, 'audio');
}

function clearAudio() {
    audioName.textContent = '';
    audioPreview.classList.add('hidden');
    audioPlaceholder.classList.remove('hidden');
    audioInput.value = '';
    uploadedFiles.audio = null;
}

// ==================== VIDEO UPLOAD ====================

videoPlaceholder.addEventListener('click', () => videoInput.click());

videoArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    videoArea.classList.add('dragover');
});

videoArea.addEventListener('dragleave', () => {
    videoArea.classList.remove('dragover');
});

videoArea.addEventListener('drop', (e) => {
    e.preventDefault();
    videoArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('video/')) {
        handleVideoUpload(files[0]);
    }
});

videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleVideoUpload(e.target.files[0]);
    }
});

function handleVideoUpload(file) {
    const url = URL.createObjectURL(file);
    refVideo.src = url;
    videoPreview.classList.remove('hidden');
    videoPlaceholder.classList.add('hidden');
    closeVideo.classList.remove('hidden');
    
    // Auto-check the use ref video checkbox
    document.getElementById('useRefVideo').checked = true;
    
    uploadFile(file, 'video');
}

function clearVideo() {
    refVideo.src = '';
    videoPreview.classList.add('hidden');
    videoPlaceholder.classList.remove('hidden');
    closeVideo.classList.add('hidden');
    videoInput.value = '';
    uploadedFiles.video = null;
    document.getElementById('useRefVideo').checked = false;
}

// ==================== FILE UPLOAD TO SERVER ====================

async function uploadFile(file, type) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`/upload/${type}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`${type} uploaded successfully:`, data.filename);
            uploadedFiles[type] = data.filename;
        } else {
            console.error(`Error uploading ${type}:`, data.error);
            alert(`Failed to upload ${type}: ${data.error}`);
        }
    } catch (error) {
        console.error(`Error uploading ${type}:`, error);
        alert(`Network error uploading ${type}`);
    }
}

// ==================== GENERATE BUTTON ====================

const generateBtn = document.getElementById('generateBtn');
const progressPanel = document.getElementById('progressPanel');
const progressFill = document.getElementById('progressFill');
const progressMessage = document.getElementById('progressMessage');
const btnText = generateBtn.querySelector('.btn-text');
const btnLoader = generateBtn.querySelector('.btn-loader');

generateBtn.addEventListener('click', async () => {
    // Validate required fields
    if (!uploadedFiles.image) {
        alert('Please upload a source image');
        return;
    }
    
    const useIdleMode = document.getElementById('useIdleMode').checked;
    const useRefVideo = document.getElementById('useRefVideo').checked;
    
    if (!uploadedFiles.audio && !useIdleMode && !useRefVideo) {
        alert('Please provide audio, enable idle mode, or use reference video');
        return;
    }

    // Collect all parameters
    const params = {
        source_image: uploadedFiles.image,
        driven_audio: uploadedFiles.audio,
        preprocess: document.querySelector('input[name="preprocessType"]:checked').value,
        still_mode: document.getElementById('isStillMode').checked,
        enhancer: document.getElementById('enhancer').checked,
        batch_size: parseInt(document.getElementById('batchSize').value),
        size: parseInt(document.querySelector('input[name="sizeOfImage"]:checked').value),
        pose_style: parseInt(document.getElementById('poseStyle').value),
        exp_scale: parseFloat(document.getElementById('expWeight').value),
        use_ref_video: useRefVideo,
        ref_video: uploadedFiles.video,
        ref_info: document.querySelector('input[name="refInfo"]:checked').value,
        use_idle_mode: useIdleMode,
        length_of_audio: parseInt(document.getElementById('lengthOfAudio').value),
        use_blink: document.getElementById('blinkEvery').checked
    };

    // Update UI to processing state
    generateBtn.disabled = true;
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    progressPanel.classList.remove('hidden');

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to result page
            window.location.href = `/result/${data.job_id}`;
        } else {
            throw new Error(data.error || 'Generation failed');
        }
    } catch (error) {
        console.error('Generation error:', error);
        alert(`Error: ${error.message}`);
        
        // Reset UI
        generateBtn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        progressPanel.classList.add('hidden');
    }
});

// ==================== IDLE MODE TOGGLE ====================

const useIdleModeCheckbox = document.getElementById('useIdleMode');
const idleLengthGroup = document.getElementById('idleLengthGroup');

useIdleModeCheckbox.addEventListener('change', () => {
    if (useIdleModeCheckbox.checked) {
        idleLengthGroup.style.opacity = '1';
    }
});

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter' && !generateBtn.disabled) {
        generateBtn.click();
    }
});

// ==================== DRAG & DROP PREVENT DEFAULT ====================

document.addEventListener('dragover', (e) => {
    if (e.target.closest('.image-upload-area, .audio-upload-area, .video-upload-box')) {
        return;
    }
    e.preventDefault();
});

document.addEventListener('drop', (e) => {
    if (e.target.closest('.image-upload-area, .audio-upload-area, .video-upload-box')) {
        return;
    }
    e.preventDefault();
});

// ==================== REF VIDEO CHECKBOX SYNC ====================

document.getElementById('useRefVideo').addEventListener('change', (e) => {
    if (e.target.checked && !uploadedFiles.video) {
        // Prompt user to upload video
        alert('Please upload a reference video first');
        e.target.checked = false;
    }
});
