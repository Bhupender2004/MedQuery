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

    // Custom Delete Confirmation Modal Logic
    const deleteModal = document.getElementById('delete-confirm-modal');
    const deleteModalTitle = document.getElementById('delete-session-title');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const closeDeleteModalBtn = document.getElementById('close-delete-modal-btn');
    
    let sessionToDelete = null;

    const closeDeleteModal = () => {
        sessionToDelete = null;
        if (deleteModal) deleteModal.style.display = 'none';
    };

    if (btnCancelDelete) {
        btnCancelDelete.addEventListener('click', closeDeleteModal);
    }
    if (closeDeleteModalBtn) {
        closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
    }
    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                closeDeleteModal();
            }
        });
    }

    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', async () => {
            if (!sessionToDelete) return;
            
            const sessionId = sessionToDelete.id;
            try {
                btnConfirmDelete.disabled = true;
                btnConfirmDelete.textContent = 'Deleting...';
                
                const deleteResponse = await fetch(`/api/chat/session/${sessionId}`, {
                    method: 'DELETE'
                });
                const deleteResult = await deleteResponse.json();
                
                if (deleteResponse.ok) {
                    closeDeleteModal();
                    if (currentSessionId === sessionId) {
                        startNewChat();
                    } else {
                        await loadSessionsSidebar();
                    }
                } else {
                    alert(`Error: ${deleteResult.error || 'Failed to delete session'}`);
                }
            } catch (deleteErr) {
                console.error('Failed to delete session:', deleteErr);
                alert('Network error. Failed to delete session.');
            } finally {
                btnConfirmDelete.disabled = false;
                btnConfirmDelete.textContent = 'Delete';
            }
        });
    }

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
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent trigger click on sessionItem
                    
                    const sessionTitle = session.title || 'Untitled Chat';
                    sessionToDelete = { id: session.session_id, title: sessionTitle };
                    
                    if (deleteModal) {
                        deleteModalTitle.textContent = sessionTitle;
                        deleteModal.style.display = 'flex';
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


    // Attachment handling elements
    const chatAttachBtn = document.getElementById('chat-attach-btn');
    const chatFileInput = document.getElementById('chat-file-input');
    const attachedFilesPreview = document.getElementById('attached-files-preview');

    let pendingFiles = [];

    // Render attachment chips preview above input bar
    const renderPreviewChips = () => {
        if (!attachedFilesPreview) return;
        attachedFilesPreview.innerHTML = '';
        if (pendingFiles.length === 0) {
            attachedFilesPreview.style.display = 'none';
            return;
        }
        attachedFilesPreview.style.display = 'flex';

        pendingFiles.forEach((file, index) => {
            const chip = document.createElement('div');
            chip.className = 'file-chip';

            const isImage = file.type.startsWith('image/');
            if (isImage) {
                const imgThumb = document.createElement('img');
                imgThumb.className = 'file-chip-thumb';
                imgThumb.src = URL.createObjectURL(file);
                imgThumb.alt = file.name;
                chip.appendChild(imgThumb);
            } else {
                const iconSpan = document.createElement('span');
                iconSpan.className = 'file-chip-icon';
                iconSpan.textContent = file.name.endsWith('.pdf') ? '📄' : '📝';
                chip.appendChild(iconSpan);
            }

            const nameSpan = document.createElement('span');
            nameSpan.className = 'file-chip-name';
            nameSpan.textContent = file.name;
            chip.appendChild(nameSpan);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'file-chip-remove';
            removeBtn.innerHTML = '&times;';
            removeBtn.title = 'Remove file';
            removeBtn.addEventListener('click', () => {
                pendingFiles.splice(index, 1);
                renderPreviewChips();
            });
            chip.appendChild(removeBtn);

            attachedFilesPreview.appendChild(chip);
        });
    };

    if (chatAttachBtn && chatFileInput) {
        chatAttachBtn.addEventListener('click', () => {
            chatFileInput.click();
        });

        chatFileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                Array.from(e.target.files).forEach(f => {
                    // Prevent duplicate files with same name and size
                    if (!pendingFiles.some(pf => pf.name === f.name && pf.size === f.size)) {
                        pendingFiles.push(f);
                    }
                });
                renderPreviewChips();
                chatFileInput.value = '';
            }
        });
    }

    // Start a completely fresh chat
    const startNewChat = () => {
        currentSessionId = generateSessionId();
        localStorage.setItem('medquery_current_session', currentSessionId);
        window.location.hash = '';
        pendingFiles = [];
        renderPreviewChips();
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
        if (!queryText && pendingFiles.length === 0) return;

        // Ensure we have an active session ID
        if (!currentSessionId) {
            currentSessionId = generateSessionId();
            localStorage.setItem('medquery_current_session', currentSessionId);
        }

        const filesToSend = [...pendingFiles];
        pendingFiles = [];
        renderPreviewChips();

        // Build user message content with text and attachment tags
        let userMessageHtml = '';
        const displayText = queryText || 'Please analyze and summarize the attached file(s).';
        userMessageHtml += `<p>${displayText}</p>`;
        
        if (filesToSend.length > 0) {
            userMessageHtml += `<div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.5rem;">`;
            filesToSend.forEach(f => {
                const icon = f.type.startsWith('image/') ? '🖼️' : (f.name.endsWith('.pdf') ? '📄' : '📝');
                userMessageHtml += `<span class="message-attachment-tag">${icon} ${f.name}</span>`;
            });
            userMessageHtml += `</div>`;
        }

        appendMessage('user', userMessageHtml, true);
        chatInput.value = '';

        // Render loading state indicator
        const loadingMsg = filesToSend.length > 0 
            ? 'Uploading & analyzing attached file(s) and clinical databases...'
            : 'Analyzing medical references and compound databases...';
        const loadingBubbleId = appendMessage('assistant', loadingMsg);

        try {
            let apiResponse;
            if (filesToSend.length > 0) {
                const formData = new FormData();
                formData.append('query', queryText);
                formData.append('session_id', currentSessionId);
                filesToSend.forEach(f => formData.append('files', f));

                apiResponse = await fetch('/api/chat/ask', {
                    method: 'POST',
                    body: formData
                });
            } else {
                apiResponse = await fetch('/api/chat/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: queryText,
                        session_id: currentSessionId
                    })
                });
            }

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
