// Configuration
const API_URL = 'http://localhost:5000/api';

// Query mode state
let isSQLMode = false;
let sqlEditor = null;

// Check backend health on load
window.addEventListener('load', checkHealth);

async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            updateStatus('connected', 'Connected');
        } else {
            updateStatus('error', 'Backend Error');
        }
    } catch (error) {
        updateStatus('error', 'Backend Offline');
        console.error('Health check failed:', error);
    }
}

function updateStatus(status, text) {
    const statusElement = document.getElementById('status');
    const statusText = document.getElementById('statusText');
    statusElement.className = `status ${status}`;
    statusText.textContent = text;
}

// Ask Question
async function askQuestion() {
    const question = document.getElementById('questionInput').value.trim();
    
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    // Show loading
    setLoading(true);
    hideError();
    
    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.sql, data.results, data.count, data.note, data.agent_output);
        } else {
            // Show error with suggestion if available
            const errorMsg = data.error + (data.suggestion ? `\n\nSuggestion: ${data.suggestion}` : '');
            showError(errorMsg);
        }
    } catch (error) {
        showError(`Request failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// Display Results
function displayResults(sql, results, count, note, agentOutput) {
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    
    // Display SQL with note if available
    let sqlDisplay = sql;
    if (note) {
        sqlDisplay = `-- NOTE: ${note}\n${sql}`;
    }
    document.getElementById('sqlQuery').textContent = sqlDisplay;
    
    // Display results table
    const tableContainer = document.getElementById('resultsTable');
    
    if (results.length === 0) {
        tableContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">No results found</p>';
        document.getElementById('resultsCount').textContent = '';
        return;
    }
    
    // Build table
    const table = document.createElement('table');
    
    // Header
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    Object.keys(results[0]).forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    
    // Body
    const tbody = table.createTBody();
    results.forEach(row => {
        const tr = tbody.insertRow();
        Object.values(row).forEach(value => {
            const td = tr.insertCell();
            // Handle long text in 'answer' field
            if (typeof value === 'string' && value.length > 200) {
                td.textContent = value;
                td.style.whiteSpace = 'pre-wrap';
                td.style.maxWidth = '800px';
            } else {
                td.textContent = value !== null ? value : 'NULL';
            }
        });
    });
    
    tableContainer.innerHTML = '';
    tableContainer.appendChild(table);
    
    // Update count with note
    let countText = `Showing ${count} row${count !== 1 ? 's' : ''}`;
    if (note) {
        countText += ` • ${note}`;
    }
    document.getElementById('resultsCount').textContent = countText;
}

// List Tables
async function listTables() {
    try {
        const response = await fetch(`${API_URL}/tables`);
        const data = await response.json();
        
        if (data.success) {
            const tablesList = document.getElementById('tablesList');
            tablesList.innerHTML = '';
            
            data.tables.forEach(table => {
                const div = document.createElement('div');
                div.className = 'table-item';
                div.textContent = table;
                div.onclick = () => {
                    document.getElementById('questionInput').value = `Show me the first 10 rows from ${table}`;
                    closeModal();
                };
                tablesList.appendChild(div);
            });
            
            document.getElementById('tablesModal').style.display = 'flex';
        }
    } catch (error) {
        alert('Failed to load tables: ' + error.message);
    }
}

// Show Examples
function showExamples() {
    document.getElementById('examplesModal').style.display = 'flex';
}

function useExample(element) {
    document.getElementById('questionInput').value = element.textContent.trim();
    closeExamplesModal();
}

// Copy SQL
function copySQL() {
    const sql = document.getElementById('sqlQuery').textContent;
    navigator.clipboard.writeText(sql).then(() => {
        alert('SQL copied to clipboard!');
    });
}

// Export to CSV
function exportToCSV() {
    const table = document.querySelector('#resultsTable table');
    if (!table) return;
    
    let csv = [];
    
    // Headers
    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent);
    csv.push(headers.join(','));
    
    // Rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('td')).map(td => {
            let value = td.textContent;
            // Escape commas and quotes
            if (value.includes(',') || value.includes('"')) {
                value = `"${value.replace(/"/g, '""')}"`;
            }
            return value;
        });
        csv.push(cells.join(','));
    });
    
    // Download
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_results_${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Clear Results
function clearResults() {
    document.getElementById('questionInput').value = '';
    document.getElementById('resultsSection').style.display = 'none';
    hideError();
}

// Error handling
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
}

function hideError() {
    document.getElementById('errorSection').style.display = 'none';
}

// Loading state
function setLoading(isLoading) {
    const submitBtn = document.querySelector('.btn-submit');
    const submitText = document.getElementById('submitText');
    const loader = document.getElementById('loader');
    
    submitBtn.disabled = isLoading;
    submitText.style.display = isLoading ? 'none' : 'inline';
    loader.style.display = isLoading ? 'inline-block' : 'none';
}

// Modal controls
function closeModal() {
    document.getElementById('tablesModal').style.display = 'none';
}

function closeExamplesModal() {
    document.getElementById('examplesModal').style.display = 'none';
}

// Close modals on outside click
window.onclick = function(event) {
    const tablesModal = document.getElementById('tablesModal');
    const examplesModal = document.getElementById('examplesModal');
    
    if (event.target === tablesModal) {
        closeModal();
    }
    if (event.target === examplesModal) {
        closeExamplesModal();
    }
}

// Toggle between Natural Language and SQL mode
function toggleQueryMode() {
    isSQLMode = !isSQLMode;
    
    const naturalInput = document.getElementById('naturalLanguageInput');
    const sqlInput = document.getElementById('sqlInput');
    const modeToggle = document.getElementById('modeToggle');
    const modeIndicator = document.getElementById('modeIndicator');
    const modeText = document.getElementById('modeText');
    
    if (isSQLMode) {
        naturalInput.style.display = 'none';
        sqlInput.style.display = 'block';
        modeToggle.textContent = '💬 Switch to Natural Language';
        modeText.textContent = 'Custom SQL Mode';
        modeIndicator.className = 'mode-indicator sql-mode';
        
        // Initialize CodeMirror if not already done
        setTimeout(() => {
            if (!sqlEditor) {
                initializeSQLEditor();
            }
            if (sqlEditor) {
                sqlEditor.refresh(); // Refresh to ensure proper sizing
                sqlEditor.focus();
            } else {
                document.getElementById('sqlQueryInput').focus();
            }
        }, 100);
    } else {
        naturalInput.style.display = 'block';
        sqlInput.style.display = 'none';
        modeToggle.textContent = '🔧 Switch to SQL';
        modeText.textContent = 'Natural Language Mode';
        modeIndicator.className = 'mode-indicator';
        // Focus on natural language input
        setTimeout(() => document.getElementById('questionInput').focus(), 100);
    }
    
    // Clear results when switching modes
    clearResults();
}

// Autocomplete removed - was causing performance issues

// Initialize CodeMirror SQL Editor
function initializeSQLEditor() {
    const textarea = document.getElementById('sqlQueryInput');
    if (!textarea || sqlEditor) return;
    
    // Initialize CodeMirror
    sqlEditor = CodeMirror.fromTextArea(textarea, {
        mode: 'text/x-mysql',
        theme: 'default',
        lineNumbers: true,
        lineWrapping: true,
        indentWithTabs: true,
        smartIndent: true,
        autofocus: true,
        extraKeys: {
            "Ctrl-Enter": function(cm) {
                executeCustomSQL();
            },
            "Tab": function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection("add");
                } else {
                    cm.replaceSelection("  ", "end");
                }
            }
        }
    });
    
    // Autocomplete disabled - was causing performance issues
    // Users can still use Ctrl+Space manually if needed
    
    // Autocomplete disabled to prevent UI hanging
    // CodeMirror still provides syntax highlighting
    
    console.log('SQL Editor initialized with autocomplete');
}

// Execute Custom SQL Query
async function executeCustomSQL() {
    // Get SQL from CodeMirror if available, otherwise from textarea
    const sql = sqlEditor ? sqlEditor.getValue().trim() : document.getElementById('sqlQueryInput').value.trim();
    
    if (!sql) {
        alert('Please enter a SQL query');
        return;
    }
    
    // Show loading
    setSQLLoading(true);
    hideError();
    
    try {
        const response = await fetch(`${API_URL}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ sql })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.sql, data.results, data.count);
        } else {
            // Show validation error
            showError(`Query Validation Error: ${data.error}\n\nOnly SELECT queries are allowed. Operations like INSERT, UPDATE, DELETE, DROP, etc. are blocked for security.`);
        }
    } catch (error) {
        showError(`Request failed: ${error.message}`);
    } finally {
        setSQLLoading(false);
    }
}

// Set loading state for SQL execution
function setSQLLoading(isLoading) {
    const submitBtn = document.querySelector('#sqlInput .btn-submit');
    const submitText = document.getElementById('sqlSubmitText');
    const loader = document.getElementById('sqlLoader');
    
    if (submitBtn) {
        submitBtn.disabled = isLoading;
        submitText.style.display = isLoading ? 'none' : 'inline';
        loader.style.display = isLoading ? 'inline-block' : 'none';
    }
}

// Show SQL Help
function showSQLHelp() {
    const helpText = `Custom SQL Query Help

✅ ALLOWED:
- SELECT queries only
- JOINs, WHERE, GROUP BY, ORDER BY, etc.
- Aggregations (SUM, COUNT, AVG, etc.)
- Subqueries

❌ BLOCKED (for security):
- INSERT, UPDATE, DELETE
- DROP, ALTER, CREATE
- GRANT, REVOKE
- EXEC, EXECUTE
- Multiple statements

⌨️ SHORTCUTS:
- Ctrl+Enter: Execute query
- Tab: Indent code

Example:
SELECT product_code, 
       SUM(amount_magnitude) AS total
FROM encoredb.loan_od_disbursements
GROUP BY product_code
ORDER BY total DESC
LIMIT 10`;

    alert(helpText);
}

// Handle Enter key in textarea (Shift+Enter for new line, Enter to submit)
document.getElementById('questionInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});

// Handle Enter key in SQL textarea (for non-CodeMirror mode)
const sqlTextarea = document.getElementById('sqlQueryInput');
if (sqlTextarea) {
    sqlTextarea.addEventListener('keydown', function(e) {
        // Only handle if CodeMirror is not active
        if (!sqlEditor && e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            executeCustomSQL();
        }
    });
}

