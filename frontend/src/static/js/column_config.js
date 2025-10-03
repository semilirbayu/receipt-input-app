/**
 * Column configuration JavaScript for real-time validation and form submission.
 */

const form = document.getElementById('column-config-form');
const dateColumnInput = document.getElementById('date-column');
const descriptionColumnInput = document.getElementById('description-column');
const priceColumnInput = document.getElementById('price-column');
const saveBtn = document.getElementById('save-config-btn');
const cancelBtn = document.getElementById('cancel-btn');
const successMessage = document.getElementById('success-message');
const errorMessage = document.getElementById('error-message');

// Track validation state for each field
const validationState = {
    date: false,
    description: false,
    price: false
};

/**
 * Auto-capitalize input to uppercase
 */
function setupAutoCapitalize(input) {
    input.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase();
    });
}

setupAutoCapitalize(dateColumnInput);
setupAutoCapitalize(descriptionColumnInput);
setupAutoCapitalize(priceColumnInput);

/**
 * Validate a single column input via API
 */
async function validateColumn(field, value) {
    const validationIndicator = document.getElementById(`${field}-validation`);
    const errorDiv = document.getElementById(`${field}-error`);
    const input = document.getElementById(`${field}-column`);

    // Clear previous state
    errorDiv.textContent = '';
    errorDiv.style.display = 'none';
    input.classList.remove('field-valid', 'field-invalid');
    validationIndicator.textContent = '';

    // Empty value is invalid (required field)
    if (!value || value.trim() === '') {
        validationState[field] = false;
        updateSaveButton();
        return;
    }

    // Show loading indicator
    validationIndicator.textContent = '⋯';
    validationIndicator.style.color = '#64748b';

    try {
        const response = await fetch('/api/v1/column-config/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ column: value })
        });

        const data = await response.json();

        if (response.ok && data.valid) {
            // Valid column
            validationState[field] = true;
            input.classList.add('field-valid');
            validationIndicator.textContent = '✓';
            validationIndicator.style.color = '#10b981';
        } else {
            // Invalid column
            validationState[field] = false;
            input.classList.add('field-invalid');
            validationIndicator.textContent = '✗';
            validationIndicator.style.color = '#ef4444';

            // Show error message
            errorDiv.textContent = data.message || 'Invalid column format';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Validation error:', error);
        // Network error - don't block user
        validationState[field] = false;
        validationIndicator.textContent = '⚠';
        validationIndicator.style.color = '#f59e0b';
        errorDiv.textContent = 'Unable to validate. Please check your input.';
        errorDiv.style.display = 'block';
    }

    updateSaveButton();
}

/**
 * Update save button state based on validation
 */
function updateSaveButton() {
    const allValid = validationState.date &&
                     validationState.description &&
                     validationState.price;

    saveBtn.disabled = !allValid;
}

/**
 * Attach validation to blur events (when user leaves field)
 */
dateColumnInput.addEventListener('blur', async (e) => {
    await validateColumn('date', e.target.value);
});

descriptionColumnInput.addEventListener('blur', async (e) => {
    await validateColumn('description', e.target.value);
});

priceColumnInput.addEventListener('blur', async (e) => {
    await validateColumn('price', e.target.value);
});

/**
 * Initial validation if fields are pre-filled
 */
window.addEventListener('load', async () => {
    if (dateColumnInput.value) {
        await validateColumn('date', dateColumnInput.value);
    }
    if (descriptionColumnInput.value) {
        await validateColumn('description', descriptionColumnInput.value);
    }
    if (priceColumnInput.value) {
        await validateColumn('price', priceColumnInput.value);
    }
});

/**
 * Handle form submission
 */
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Hide previous messages
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';

    // Re-validate all fields before submission
    await validateColumn('date', dateColumnInput.value);
    await validateColumn('description', descriptionColumnInput.value);
    await validateColumn('price', priceColumnInput.value);

    // Check if all fields are valid
    if (!validationState.date || !validationState.description || !validationState.price) {
        showError('Please ensure all fields are valid before saving');
        return;
    }

    // Disable save button during request
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    const payload = {
        date_column: dateColumnInput.value.toUpperCase(),
        description_column: descriptionColumnInput.value.toUpperCase(),
        price_column: priceColumnInput.value.toUpperCase()
    };

    try {
        const response = await fetch('/api/v1/column-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            // Success
            showSuccess('Column mappings saved successfully! Redirecting to upload page...');

            // Redirect to upload page after 2 seconds
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else if (response.status === 400) {
            // Validation errors from backend
            if (data.errors && Array.isArray(data.errors)) {
                // Display field-specific errors
                data.errors.forEach(error => {
                    const field = error.field || error.loc?.[1]; // Handle both formats
                    if (field) {
                        const errorDiv = document.getElementById(`${field.replace('_column', '')}-error`);
                        if (errorDiv) {
                            errorDiv.textContent = error.message || error.msg;
                            errorDiv.style.display = 'block';
                        }
                    }
                });
                showError('Please correct the validation errors');
            } else {
                showError(data.message || 'Invalid configuration');
            }
        } else if (response.status === 401) {
            // Authentication required
            showError('Please log in to configure column mappings');
            setTimeout(() => {
                window.location.href = '/api/v1/auth/login';
            }, 2000);
        } else {
            // Other errors
            showError(data.message || 'Failed to save configuration');
        }
    } catch (error) {
        console.error('Save error:', error);
        showError('Network error. Please try again.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Configuration';
        updateSaveButton(); // Re-check validation state
    }
});

/**
 * Handle cancel button
 */
cancelBtn.addEventListener('click', () => {
    window.location.href = '/setup';
});

/**
 * Show success message
 */
function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    window.scrollTo(0, 0);
}

/**
 * Show error message
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    window.scrollTo(0, 0);
}
