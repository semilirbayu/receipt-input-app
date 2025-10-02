/**
 * Review correction JavaScript for form handling and save logic.
 */

const form = document.getElementById('correction-form');
const receiptIdInput = document.getElementById('receipt-id');
const transactionDateInput = document.getElementById('transaction-date');
const itemsInput = document.getElementById('items');
const totalAmountInput = document.getElementById('total-amount');
const saveBtn = document.getElementById('save-btn');
const discardBtn = document.getElementById('discard-btn');
const successMessage = document.getElementById('success-message');
const errorMessage = document.getElementById('error-message');

// Load extracted data from sessionStorage
const extractedData = JSON.parse(sessionStorage.getItem('extracted_data') || '{}');

// Pre-fill form fields with extracted data
if (extractedData) {
    if (extractedData.transaction_date) {
        transactionDateInput.value = extractedData.transaction_date;
        updateConfidenceIndicator('date', extractedData.transaction_date_confidence);
    }

    if (extractedData.items) {
        itemsInput.value = extractedData.items;
        updateConfidenceIndicator('items', extractedData.items_confidence);
    }

    if (extractedData.total_amount !== null && extractedData.total_amount !== undefined) {
        totalAmountInput.value = extractedData.total_amount;
        updateConfidenceIndicator('amount', extractedData.total_amount_confidence);
    }
}

/**
 * Update confidence indicator icon based on score.
 */
function updateConfidenceIndicator(field, confidence) {
    const indicator = document.getElementById(`${field}-confidence`);
    if (!indicator) return;

    if (confidence >= 0.8) {
        indicator.textContent = '✓';  // High confidence
        indicator.style.color = '#10b981';
    } else if (confidence >= 0.6) {
        indicator.textContent = '⚠';  // Medium confidence
        indicator.style.color = '#f59e0b';
    } else {
        indicator.textContent = '✗';  // Low confidence
        indicator.style.color = '#ef4444';
    }
}

/**
 * Real-time form validation.
 */
function validateForm() {
    const isValid =
        transactionDateInput.value.trim() !== '' &&
        itemsInput.value.trim() !== '' &&
        totalAmountInput.value !== '' &&
        parseFloat(totalAmountInput.value) >= 0;

    saveBtn.disabled = !isValid;

    return isValid;
}

// Attach validation to input events
transactionDateInput.addEventListener('input', validateForm);
itemsInput.addEventListener('input', validateForm);
totalAmountInput.addEventListener('input', validateForm);

// Initial validation
validateForm();

/**
 * Handle form submission - save to Google Sheets.
 */
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Hide previous messages
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';

    if (!validateForm()) {
        showError('Please fill in all required fields');
        return;
    }

    // Disable save button during request
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    const payload = {
        receipt_id: receiptIdInput.value,
        transaction_date: transactionDateInput.value,
        items: itemsInput.value,
        total_amount: parseFloat(totalAmountInput.value)
    };

    try {
        const response = await fetch('/api/v1/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            // Success
            const message = `Receipt saved successfully! <a href="${data.spreadsheet_url}" target="_blank">View in Google Sheets</a>`;
            showSuccess(message);

            // Clear sessionStorage
            sessionStorage.removeItem('extracted_data');

            // Redirect to home after 3 seconds
            setTimeout(() => {
                window.location.href = '/';
            }, 3000);
        } else if (response.status === 401) {
            // Authentication expired or missing
            if (data.error_code === 'AUTH_EXPIRED') {
                showAuthExpiredModal();
            } else {
                showError(data.message || 'Authentication required');
            }
        } else if (response.status === 403 || response.status === 423 || response.status === 429 || response.status === 500) {
            // Google Sheets API error
            const errorCode = data.error_code || 'UNKNOWN';
            const message = `${data.message} <button class="btn btn-secondary" onclick="copyErrorCode('${errorCode}')">Copy Error Code</button>`;
            showError(message);
        } else {
            // Other errors
            showError(data.message || 'Failed to save receipt');
        }
    } catch (error) {
        console.error('Save error:', error);
        showError('Network error. Please try again.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save to Google Sheets';
        validateForm();  // Re-validate to update button state
    }
});

/**
 * Handle discard button - redirect to upload page.
 */
discardBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to discard this receipt?')) {
        sessionStorage.removeItem('extracted_data');
        window.location.href = '/';
    }
});

/**
 * Show auth expired modal.
 */
function showAuthExpiredModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Session Expired</h3>
            <p>Your Google Sheets authentication has expired. Please reconnect.</p>
            <button class="btn btn-primary" onclick="window.location.href='/api/v1/auth/login'">Reconnect</button>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Copy error code to clipboard.
 */
function copyErrorCode(code) {
    navigator.clipboard.writeText(code).then(() => {
        alert(`Error code ${code} copied to clipboard`);
    });
}

/**
 * Show success message.
 */
function showSuccess(message) {
    successMessage.innerHTML = message;
    successMessage.style.display = 'block';
    window.scrollTo(0, 0);
}

/**
 * Show error message.
 */
function showError(message) {
    errorMessage.innerHTML = message;
    errorMessage.style.display = 'block';
    window.scrollTo(0, 0);
}
