/**
 * Upload interaction JavaScript for drag-drop and file handling.
 */

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const selectFileBtn = document.getElementById('select-file-btn');
const progressIndicator = document.getElementById('progress-indicator');
const errorMessage = document.getElementById('error-message');

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png'];

// Detect touch device
const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

// Hide drag-drop UI on mobile
if (isTouchDevice && window.innerWidth < 768) {
    uploadArea.style.cursor = 'pointer';
}

// File selection button click
selectFileBtn.addEventListener('click', () => {
    fileInput.click();
});

// Upload area click (mobile)
uploadArea.addEventListener('click', (e) => {
    if (e.target !== selectFileBtn) {
        fileInput.click();
    }
});

// File input change handler
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        await uploadFile(file);
    }
});

// Drag and drop event handlers (desktop only)
if (!isTouchDevice) {
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', async (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        if (file) {
            await uploadFile(file);
        }
    });
}

/**
 * Validate file before upload.
 */
function validateFile(file) {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        return { valid: false, error: 'File size exceeds 5MB limit' };
    }

    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
        return { valid: false, error: 'Only JPG and PNG formats are supported' };
    }

    return { valid: true };
}

/**
 * Upload file to server and handle response.
 */
async function uploadFile(file) {
    // Hide previous errors
    errorMessage.style.display = 'none';

    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
        showError(validation.error);
        return;
    }

    // Show progress indicator
    progressIndicator.style.display = 'block';
    uploadArea.style.display = 'none';

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/v1/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Success - redirect to review page
            const receiptId = data.receipt_id;

            // Store extracted data in sessionStorage for review page
            sessionStorage.setItem('extracted_data', JSON.stringify(data.extracted_data));

            window.location.href = `/review/${receiptId}`;
        } else {
            // Error response
            showError(data.message || 'Upload failed');
            resetUploadUI();
        }
    } catch (error) {
        console.error('Upload error:', error);
        showError('Network error. Please try again.');
        resetUploadUI();
    }
}

/**
 * Show error message.
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

/**
 * Reset upload UI to initial state.
 */
function resetUploadUI() {
    progressIndicator.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInput.value = '';
}
