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
                            <button class="btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; border-radius: 4px;" onclick="alert('Query details: \\n\\nPrompt: ${sanitizeHtmlString(logEntry.user_query)}\\n\\nResponse: ${sanitizeHtmlString(logEntry.ai_response)}')">
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

    // Load metrics initially on boot
    reloadDashboardMetrics();
});

