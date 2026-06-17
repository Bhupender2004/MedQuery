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

    // Chart.js instance tracking variables
    let auditVolumeChart = null;
    let severityBreakdownChart = null;
    let flaggedCompoundsChart = null;

    // Custom Delete Confirmation Modal Logic
    const deleteModal = document.getElementById('delete-confirm-modal');
    const deleteModalQuery = document.getElementById('delete-log-query');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const closeDeleteModalBtn = document.getElementById('close-delete-modal-btn');
    
    let logIdToDelete = null;

    const closeDeleteModal = () => {
        logIdToDelete = null;
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
            if (!logIdToDelete) return;
            
            try {
                btnConfirmDelete.disabled = true;
                btnConfirmDelete.textContent = 'Deleting...';
                
                const response = await fetch(`/api/chat/log/${logIdToDelete}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                
                if (response.ok) {
                    closeDeleteModal();
                    await reloadDashboardMetrics();
                } else {
                    alert(`Error: ${result.error || 'Failed to delete log entry'}`);
                }
            } catch (err) {
                console.error('Failed to delete query log:', err);
                alert('Network error. Failed to delete query log.');
            } finally {
                btnConfirmDelete.disabled = false;
                btnConfirmDelete.textContent = 'Delete';
            }
        });
    }

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
                            <button class="btn-inspect-log btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; border-radius: 4px;">
                                Inspect
                            </button>
                            <button class="btn-delete-log">
                                Delete
                            </button>
                        </td>
                    `;
                    
                    rowElement.querySelector('.btn-inspect-log').addEventListener('click', () => {
                        inspectLogEntry(logEntry.id);
                    });
                    
                    rowElement.querySelector('.btn-delete-log').addEventListener('click', () => {
                        deleteLogEntry(logEntry.id);
                    });
                    
                    queryLogsTableBody.appendChild(rowElement);
                });
            }

            // Render Chart.js visual graphs
            renderCharts(metrics);

        } catch (err) {
            console.error('Failed to reload metrics dashboard views: ', err);
        }
    };

    // Helper to construct and render Chart.js graphs
    const renderCharts = (metrics) => {
        const styles = getComputedStyle(document.documentElement);
        const textPrimary = styles.getPropertyValue('--text-primary').trim() || 'hsl(210, 30%, 95%)';
        const textSecondary = styles.getPropertyValue('--text-secondary').trim() || 'hsl(210, 15%, 75%)';
        const borderVal = styles.getPropertyValue('--border-color').trim() || 'hsl(220, 15%, 22%)';
        const bgSecondary = styles.getPropertyValue('--bg-secondary').trim() || 'hsl(220, 20%, 14%)';
        const accentTeal = styles.getPropertyValue('--accent-teal').trim() || 'hsl(175, 75%, 45%)';
        const accentTealGlow = styles.getPropertyValue('--accent-teal-glow').trim() || 'hsla(175, 75%, 45%, 0.08)';

        // 1. Weekly Audit Volume Line Chart
        const canvasVolume = document.getElementById('chart-audit-volume');
        if (canvasVolume) {
            const ctxVolume = canvasVolume.getContext('2d');
            if (auditVolumeChart) auditVolumeChart.destroy();
            
            const volumeData = metrics.weekly_audit_volume || { labels: [], values: [] };
            auditVolumeChart = new Chart(ctxVolume, {
                type: 'line',
                data: {
                    labels: volumeData.labels,
                    datasets: [{
                        label: 'Queries Checked',
                        data: volumeData.values,
                        borderColor: accentTeal,
                        backgroundColor: accentTealGlow,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: accentTeal,
                        pointBorderColor: textPrimary,
                        pointHoverRadius: 6,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: bgSecondary,
                            titleColor: textPrimary,
                            bodyColor: textSecondary,
                            borderColor: borderVal,
                            borderWidth: 1,
                            titleFont: { family: 'Inter', weight: '600' },
                            bodyFont: { family: 'Inter' }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: borderVal },
                            ticks: { color: textSecondary, font: { family: 'Inter', size: 10 } }
                        },
                        y: {
                            grid: { color: borderVal },
                            ticks: { color: textSecondary, font: { family: 'Inter', size: 10 }, stepSize: 1, beginAtZero: true }
                        }
                    }
                }
            });
        }

        // 2. Interaction Severity Breakdown Donut Chart
        const canvasSeverity = document.getElementById('chart-severity-breakdown');
        if (canvasSeverity) {
            const ctxSeverity = canvasSeverity.getContext('2d');
            if (severityBreakdownChart) severityBreakdownChart.destroy();
            
            const dist = metrics.severity_distribution || { minor: 0, moderate: 0, major: 0 };
            
            severityBreakdownChart = new Chart(ctxSeverity, {
                type: 'doughnut',
                data: {
                    labels: ['Low Severity', 'Moderate Severity', 'High Severity'],
                    datasets: [{
                        data: [dist.minor, dist.moderate, dist.major],
                        backgroundColor: [
                            'hsl(200, 80%, 50%)',   // minor
                            'hsl(35, 90%, 55%)',    // moderate
                            'hsl(0, 85%, 60%)'      // major
                        ],
                        borderColor: bgSecondary,
                        borderWidth: 2,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: textSecondary,
                                font: { family: 'Inter', size: 10 },
                                padding: 12,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: bgSecondary,
                            bodyColor: textPrimary,
                            borderColor: borderVal,
                            borderWidth: 1,
                            bodyFont: { family: 'Inter' }
                        }
                    },
                    cutout: '70%'
                }
            });
        }

        // 3. Most Flagged Compounds Horizontal Bar Chart
        const canvasFlagged = document.getElementById('chart-flagged-compounds');
        if (canvasFlagged) {
            const ctxFlagged = canvasFlagged.getContext('2d');
            if (flaggedCompoundsChart) flaggedCompoundsChart.destroy();
            
            const flaggedData = metrics.most_flagged_drugs || { labels: [], values: [] };
            
            flaggedCompoundsChart = new Chart(ctxFlagged, {
                type: 'bar',
                data: {
                    labels: flaggedData.labels,
                    datasets: [{
                        data: flaggedData.values,
                        backgroundColor: accentTealGlow,
                        borderColor: accentTeal,
                        borderWidth: 1.5,
                        borderRadius: 4,
                        barThickness: 16
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: bgSecondary,
                            bodyColor: textPrimary,
                            borderColor: borderVal,
                            borderWidth: 1,
                            bodyFont: { family: 'Inter' }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: borderVal },
                            ticks: { color: textSecondary, font: { family: 'Inter', size: 10 }, stepSize: 1, beginAtZero: true }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: textSecondary, font: { family: 'Inter', size: 10 } }
                        }
                    }
                }
            });
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

    window.deleteLogEntry = (logId) => {
        const log = (window.loadedLogs || []).find(l => l.id === logId);
        if (!log) return;
        
        logIdToDelete = logId;
        if (deleteModal) {
            if (deleteModalQuery) {
                deleteModalQuery.textContent = `"${log.user_query}"`;
            }
            deleteModal.style.display = 'flex';
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

    // Redraw charts when theme changes
    window.addEventListener('themechanged', () => {
        reloadDashboardMetrics();
    });
});
