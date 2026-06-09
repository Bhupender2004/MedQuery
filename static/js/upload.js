/**
 * MedQuery Upload Desk Controller
 * Handles posting binary forms to `/api/upload` and checking parsing queue status.
 */

document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileSelector = document.getElementById('file-selector');
    const feedbackBanner = document.getElementById('upload-feedback');

    if (!uploadForm) return;

    // Helper: Show feedback alerts to the user
    const displayFeedback = (msgText, stateType) => {
        if (!feedbackBanner) return;
        feedbackBanner.className = `dashboard-card feedback-alert ${stateType}`;
        feedbackBanner.textContent = msgText;
        feedbackBanner.style.display = 'block';
        
        // Adjust alert colors in-place according to HSL palette
        if (stateType === 'error') {
            feedbackBanner.style.borderColor = 'var(--warning-major)';
            feedbackBanner.style.color = 'var(--warning-major)';
        } else if (stateType === 'success') {
            feedbackBanner.style.borderColor = 'var(--accent-teal)';
            feedbackBanner.style.color = 'var(--accent-teal)';
        } else {
            feedbackBanner.style.borderColor = 'var(--border-color)';
            feedbackBanner.style.color = 'var(--text-secondary)';
        }
    };

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const fileToUpload = fileSelector.files[0];
        if (!fileToUpload) {
            displayFeedback('Please attach a medical reference file (PDF, TXT, or CSV) first.', 'error');
            return;
        }

        const multipartPayload = new FormData();
        multipartPayload.append('file', fileToUpload);

        displayFeedback('Uploading document stream and triggering vector parsing pipeline...', 'info');

        try {
            const apiResult = await fetch('/api/upload', {
                method: 'POST',
                body: multipartPayload
            });

            const data = await apiResult.json();

            if (data.error) {
                displayFeedback(`Upload execution denied: ${data.error}`, 'error');
                return;
            }

            // Success feedback and check status
            displayFeedback(
                `Success! File "${data.filename}" has been queued. Ingest status: [${data.status.toUpperCase()}]. Document ID: ${data.document_id}`,
                'success'
            );
            
            // Clear selector values on success
            fileSelector.value = '';

        } catch (netErr) {
            displayFeedback(`File transmission interrupted: ${netErr.message}`, 'error');
        }
    });
});
