/**
 * MedQuery Chat Client
 * Handles posting prompts to `/api/chat/ask` and showing citations/warning alerts.
 */

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const messagesBox = document.getElementById('chat-messages');

    if (!chatForm) return;

    // Helper: Append a message bubble to the chat container
    const appendMessage = (sender, content, isHtml = false) => {
        const msgId = `msg-${Date.now()}`;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.id = msgId;

        if (isHtml) {
            messageDiv.innerHTML = content;
        } else {
            const textParagraph = document.createElement('p');
            textParagraph.textContent = content;
            messageDiv.appendChild(textParagraph);
        }

        messagesBox.appendChild(messageDiv);
        messagesBox.scrollTop = messagesBox.scrollHeight;
        return msgId;
    };

    // Helper: Remove temporary loading status elements
    const removeMessage = (id) => {
        const elem = document.getElementById(id);
        if (elem) elem.remove();
    };

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const queryText = chatInput.value.trim();
        if (!queryText) return;

        // Render user question bubble
        appendMessage('user', queryText);
        chatInput.value = '';

        // Render loading state indicator
        const loadingBubbleId = appendMessage('assistant', 'Analyzing medical references and compound databases...');

        try {
            const apiResponse = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: queryText,
                    session_id: 'demo-session-token'
                })
            });

            const data = await apiResponse.json();
            removeMessage(loadingBubbleId);

            if (data.error) {
                appendMessage('assistant', `Service warning: ${data.message || data.error}`);
                return;
            }

            // Build structural output displaying markdown clinical notes
            let renderHtml = '';
            
            // Format warning alert box if interactions are present
            if (data.has_warnings) {
                renderHtml += `
                    <div class="warning-banner major" style="margin-bottom:1rem;">
                        <strong>⚠️ CRITICAL INTERACTION DETECTED (${data.severity.toUpperCase()}):</strong>
                        <p style="margin-top: 0.25rem; font-size: 0.9rem;">
                           Database Rule Match: ${data.description || 'Known safety interaction risk flagged.'}
                        </p>
                    </div>
                `;
            }

            // Render the main clinical pharmacist response parsed from Markdown to beautiful HTML
            const parsedMarkdown = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response;
            renderHtml += `<div class="clinical-note">${parsedMarkdown}</div>`;

            // Append retrieved citation documents lists
            if (data.citations && data.citations.length > 0) {
                renderHtml += `
                    <div class="citations-container" style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); font-size: 0.85rem;">
                        <span style="color: var(--accent-teal); font-weight:600;">Cited Sources:</span>
                        <ul style="margin-left: 1rem; margin-top: 0.25rem; color: var(--text-secondary);">
                `;
                data.citations.forEach(sourceItem => {
                    const docName = sourceItem.metadata.source;
                    const docPage = sourceItem.metadata.page || 1;
                    renderHtml += `<li>${docName} (Page ${docPage})</li>`;
                });
                renderHtml += `</ul></div>`;
            }

            appendMessage('assistant', renderHtml, true);

        } catch (fetchErr) {
            removeMessage(loadingBubbleId);
            appendMessage('assistant', `Failed to contact servers. Network issue: ${fetchErr.message}`);
        }
    });
});
