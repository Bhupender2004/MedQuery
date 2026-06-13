/**
 * MedQuery Chat Client
 * Handles posting prompts to `/api/chat/ask`, switching sessions, and managing ChatGPT-style sidebar history.
 */

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const messagesBox = document.getElementById('chat-messages');
    const sessionsList = document.getElementById('sessions-list');
    const newChatBtn = document.getElementById('new-chat-btn');

    if (!chatForm) return;

    let currentSessionId = '';

    // Helper: Generate a unique session token
    const generateSessionId = () => {
        return 'session-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now();
    };

    // Helper: Append a message bubble to the chat container
    const appendMessage = (sender, content, isHtml = false) => {
        const msgId = `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
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

    // Render Welcome Assistant message when starting fresh
    const renderWelcomeMessage = () => {
        messagesBox.innerHTML = '';
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'message assistant';
        welcomeDiv.innerHTML = `
            <p>Hello! I am your clinical pharmacy assistant. Type in drug names or clinical combinations to verify interactions and check against your uploaded reference documents.</p>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem;">Try asking: <em>"Can I take Aspirin with Warfarin?"</em> or <em>"Is there an issue with Ibuprofen and Lisinopril?"</em></p>
        `;
        messagesBox.appendChild(welcomeDiv);
        messagesBox.scrollTop = 0;
    };

    // Load and render history logs for a specific session ID
    const loadSessionHistory = async (sessionId) => {
        currentSessionId = sessionId;
        localStorage.setItem('medquery_current_session', sessionId);
        window.location.hash = sessionId;

        // Render loading state inside chat window
        messagesBox.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Loading conversation logs...</div>';

        try {
            const response = await fetch(`/api/chat/history?session_id=${sessionId}`);
            const logs = await response.json();
            
            messagesBox.innerHTML = '';
            
            if (!logs || logs.length === 0) {
                renderWelcomeMessage();
                return;
            }

            logs.forEach(log => {
                // Append User Query
                appendMessage('user', log.user_query);

                // Build Assistant Response with warnings
                let renderHtml = '';
                if (log.has_interaction_warnings) {
                    renderHtml += `
                        <div class="warning-banner major" style="margin-bottom:1rem;">
                            <strong>⚠️ CRITICAL INTERACTION DETECTED (${log.severity_level.toUpperCase()}):</strong>
                            <p style="margin-top: 0.25rem; font-size: 0.9rem;">
                               Known safety interaction risk flagged.
                            </p>
                        </div>
                    `;
                }

                const parsedMarkdown = typeof marked !== 'undefined' ? marked.parse(log.ai_response) : log.ai_response;
                renderHtml += `<div class="clinical-note">${parsedMarkdown}</div>`;

                // Add Citations if present
                if (log.citations) {
                    try {
                        const citations = JSON.parse(log.citations);
                        if (citations && citations.length > 0) {
                            renderHtml += `
                                <div class="citations-container" style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); font-size: 0.85rem;">
                                    <span style="color: var(--accent-teal); font-weight:600;">Cited Sources:</span>
                                    <ul style="margin-left: 1rem; margin-top: 0.25rem; color: var(--text-secondary);">
                            `;
                            citations.forEach(c => {
                                renderHtml += `<li>${c.source} (Page ${c.page || 1})</li>`;
                            });
                            renderHtml += `</ul></div>`;
                        }
                    } catch (e) {
                        // ignore JSON parse errors
                    }
                }

                appendMessage('assistant', renderHtml, true);
            });
        } catch (err) {
            messagesBox.innerHTML = `<div style="text-align: center; color: var(--warning-major); padding: 2rem;">Failed to load chat history: ${err.message}</div>`;
        }
    };

    // Fetch list of distinct sessions and render them in the sidebar
    const loadSessionsSidebar = async () => {
        if (!sessionsList) return;

        try {
            const response = await fetch('/api/chat/sessions');
            const sessions = await response.json();
            
            sessionsList.innerHTML = '';
            
            if (!sessions || sessions.length === 0) {
                sessionsList.innerHTML = '<div style="padding: 1rem; font-size:0.8rem; color: var(--text-muted); text-align:center;">No previous chats</div>';
                return;
            }

            sessions.forEach(session => {
                const sessionItem = document.createElement('div');
                sessionItem.className = `session-item ${session.session_id === currentSessionId ? 'active' : ''}`;
                sessionItem.dataset.id = session.session_id;

                const titleSpan = document.createElement('span');
                titleSpan.className = 'session-title';
                titleSpan.textContent = session.title || 'Untitled Chat';
                sessionItem.appendChild(titleSpan);

                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn-delete-session';
                deleteBtn.innerHTML = '&times;';
                deleteBtn.title = 'Delete conversation';
                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation(); // Prevent trigger click on sessionItem

                    if (confirm('Are you sure you want to delete this chat conversation? This will delete all queries and reference files associated with this chat.')) {
                        try {
                            const deleteResponse = await fetch(`/api/chat/session/${session.session_id}`, {
                                method: 'DELETE'
                            });
                            const deleteResult = await deleteResponse.json();
                            if (deleteResponse.ok) {
                                if (currentSessionId === session.session_id) {
                                    startNewChat();
                                } else {
                                    // Just reload the sidebar
                                    await loadSessionsSidebar();
                                }
                            } else {
                                alert(`Error: ${deleteResult.error || 'Failed to delete session'}`);
                            }
                        } catch (deleteErr) {
                            console.error('Failed to delete session:', deleteErr);
                            alert('Network error. Failed to delete session.');
                        }
                    }
                });
                sessionItem.appendChild(deleteBtn);
                
                sessionItem.addEventListener('click', () => {
                    // Update active styling
                    document.querySelectorAll('.session-item').forEach(item => item.classList.remove('active'));
                    sessionItem.classList.add('active');
                    loadSessionHistory(session.session_id);
                });

                sessionsList.appendChild(sessionItem);
            });
        } catch (err) {
            console.error('Failed to load chat sessions list:', err);
        }
    };


    // Start a completely fresh chat
    const startNewChat = () => {
        currentSessionId = generateSessionId();
        localStorage.setItem('medquery_current_session', currentSessionId);
        window.location.hash = '';
        renderWelcomeMessage();
        
        // Deselect sidebar items
        document.querySelectorAll('.session-item').forEach(item => item.classList.remove('active'));
    };

    // Wire up "+ New Chat" button
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }

    // Submit handler for sending messages
    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const queryText = chatInput.value.trim();
        if (!queryText) return;

        // Ensure we have an active session ID
        if (!currentSessionId) {
            currentSessionId = generateSessionId();
            localStorage.setItem('medquery_current_session', currentSessionId);
        }

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
                    session_id: currentSessionId
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

            // Set the URL hash to current session if it isn't set yet (enables bookmarking/reload support)
            if (window.location.hash !== `#${currentSessionId}`) {
                window.location.hash = currentSessionId;
            }

            // Reload sidebar list to show new session title
            await loadSessionsSidebar();

        } catch (fetchErr) {
            removeMessage(loadingBubbleId);
            appendMessage('assistant', `Failed to contact servers. Network issue: ${fetchErr.message}`);
        }
    });

    // Initialize: load session from URL hash or start fresh
    const initChat = async () => {
        const hash = window.location.hash.substring(1);
        if (hash && hash.startsWith('session-')) {
            currentSessionId = hash;
            localStorage.setItem('medquery_current_session', hash);
            await loadSessionHistory(hash);
        } else {
            startNewChat();
        }
        await loadSessionsSidebar();
    };

    initChat();
});
