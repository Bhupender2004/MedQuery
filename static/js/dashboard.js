/**
 * MedQuery Analytical Dashboard Controller
 * Periodically calls `/api/dashboard/stats` to update count boards and details tables.
 */

document.addEventListener('DOMContentLoaded', () => {
    const docCountField = document.getElementById('count-documents');
    const queryCountField = document.getElementById('count-queries');
    const warningCountField = document.getElementById('count-warnings');
    const rulesCountField = document.getElementById('count-rules');
    const queryLogsTableBody = document.getElementById('dashboard-logs-tbody');

    if (!docCountField) return;

    // Helper: Escapes queries strings to prevent injection in table renders
    const sanitizeHtmlString = (textStr) => {
        if (!textStr) return '';
        return textStr
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    };

    // Main fetch handler compiling indicators
    const reloadDashboardMetrics = async () => {
        try {
            const apiResult = await fetch('/api/dashboard/stats');
            const metrics = await apiResult.json();

            // Populate dashboard boards fields
            docCountField.textContent = metrics.total_documents;
            queryCountField.textContent = metrics.total_queries;
            warningCountField.textContent = metrics.total_warnings;
            
            if (rulesCountField) {
                rulesCountField.textContent = metrics.rules_count || 0;
            }

            // Populate table log content rows
            if (queryLogsTableBody) {
                queryLogsTableBody.innerHTML = '';
                
                const recentLogsList = metrics.recent_queries || [];
                window.loadedLogs = recentLogsList; // Cache logs to avoid inline JS quote escaping issues
                
                if (recentLogsList.length === 0) {
                    queryLogsTableBody.innerHTML = `
                        <tr>
                            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
                                No queries logged in the system. Go to the Chat page to submit queries.
                            </td>
                        </tr>
                    `;
                    return;
                }

                recentLogsList.forEach((logEntry) => {
                    const rowElement = document.createElement('tr');
                    
                    const timestampStr = new Date(logEntry.created_at).toLocaleString();
                    
                    const alertBadge = logEntry.has_interaction_warnings
                        ? `<span class="badge warning" style="background-color: var(--warning-major-glow); color: var(--warning-major); border: 1px solid var(--warning-major); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight:600;">${logEntry.severity_level.toUpperCase()}</span>`
                        : `<span class="badge safe" style="background-color: rgba(175, 75, 45, 0.05); color: var(--accent-teal); border: 1px solid var(--accent-teal); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight:600;">SAFE</span>`;

                    rowElement.innerHTML = `
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; color: var(--text-secondary);">${timestampStr}</td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px;">${sanitizeHtmlString(logEntry.user_query)}</td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border-color);">${alertBadge}</td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border-color); text-align:right; white-space: nowrap;">
                            <button class="btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; border-radius: 4px;" onclick="inspectLogEntry(${logEntry.id})">
                                Inspect
                            </button>
                            <button class="btn-delete-log" onclick="deleteLogEntry(${logEntry.id})">
                                Delete
                            </button>
                        </td>
                    `;
                    queryLogsTableBody.appendChild(rowElement);
                });
            }

        } catch (err) {
            console.error('Failed to reload metrics dashboard views: ', err);
        }
    };

    window.inspectLogEntry = (logId) => {
        const log = (window.loadedLogs || []).find(l => l.id === logId);
        if (!log) return;

        document.getElementById('modal-timestamp').textContent = new Date(log.created_at).toLocaleString();
        
        const severityBadge = document.getElementById('modal-severity');
        severityBadge.textContent = log.severity_level.toUpperCase();
        severityBadge.className = 'badge';
        if (log.has_interaction_warnings) {
            severityBadge.style.backgroundColor = 'var(--warning-major-glow)';
            severityBadge.style.color = 'var(--warning-major)';
            severityBadge.style.border = '1px solid var(--warning-major)';
            severityBadge.style.padding = '0.2rem 0.5rem';
            severityBadge.style.borderRadius = '4px';
            severityBadge.style.fontSize = '0.8rem';
            severityBadge.style.fontWeight = '600';
        } else {
            severityBadge.style.backgroundColor = 'rgba(175, 75, 45, 0.05)';
            severityBadge.style.color = 'var(--accent-teal)';
            severityBadge.style.border = '1px solid var(--accent-teal)';
            severityBadge.style.padding = '0.2rem 0.5rem';
            severityBadge.style.borderRadius = '4px';
            severityBadge.style.fontSize = '0.8rem';
            severityBadge.style.fontWeight = '600';
        }

        document.getElementById('modal-query').textContent = log.user_query;
        
        // Parse markdown using marked.js
        const responseDiv = document.getElementById('modal-response');
        if (typeof marked !== 'undefined') {
            responseDiv.innerHTML = marked.parse(log.ai_response);
        } else {
            responseDiv.textContent = log.ai_response;
        }

        // Citations rendering
        const citationsSection = document.getElementById('modal-citations-section');
        const citationsList = document.getElementById('modal-citations');
        citationsList.innerHTML = '';
        
        if (log.citations) {
            try {
                const citations = JSON.parse(log.citations);
                if (citations && citations.length > 0) {
                    citations.forEach(c => {
                        const li = document.createElement('li');
                        li.textContent = `${c.source} (Page ${c.page || 1})`;
                        citationsList.appendChild(li);
                    });
                    citationsSection.style.display = 'block';
                } else {
                    citationsSection.style.display = 'none';
                }
            } catch (e) {
                citationsSection.style.display = 'none';
            }
        } else {
            citationsSection.style.display = 'none';
        }

        document.getElementById('inspect-modal').style.display = 'flex';
    };

    window.deleteLogEntry = async (logId) => {
        if (confirm('Are you sure you want to delete this specific query log entry?')) {
            try {
                const response = await fetch(`/api/chat/log/${logId}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (response.ok) {
                    await reloadDashboardMetrics();
                } else {
                    alert(`Error: ${result.error || 'Failed to delete log entry'}`);
                }
            } catch (err) {
                console.error('Failed to delete query log:', err);
                alert('Network error. Failed to delete query log.');
            }
        }
    };

    // Close Modal event listeners
    const closeModalBtn = document.getElementById('close-modal-btn');
    const inspectModal = document.getElementById('inspect-modal');
    if (closeModalBtn && inspectModal) {
        const closeModal = () => {
            inspectModal.style.display = 'none';
        };
        closeModalBtn.addEventListener('click', closeModal);
        inspectModal.addEventListener('click', (e) => {
            if (e.target === inspectModal) {
                closeModal();
            }
        });
    }

    // Load metrics initially on boot
    reloadDashboardMetrics();
});
