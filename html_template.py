def generate_html_template(sample_result_files, bulk_result_files):
    """Generate the HTML template for the home page"""

    # Generate HTML lists with file names and dates
    sample_result_html = "".join(
        f'<li><span class="download-icon"><i class="fas fa-download"></i></span><a href="/download-result/sample/{file}">{file}</a> <small>{date}</small></li>\n'
        for file, date in sample_result_files
    )

    bulk_compare_html = "".join(
        f'<li><span class="download-icon"><i class="fas fa-download"></i></span><a href="/download-result/bulk/{file}">{file}</a> <small>{date}</small></li>\n'
        for file, date in bulk_result_files if "Compare" in file
    )

    bulk_updated_html = "".join(
        f'<li><span class="download-icon"><i class="fas fa-download"></i></span><a href="/download-result/bulk/{file}">{file}</a> <small>{date}</small></li>\n'
        for file, date in bulk_result_files if "Updated" in file
    )

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Price Check File Upload System</title>
    <link rel="stylesheet" href="static/css/styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.3.0/css/all.min.css">
</head>
<body>
    <!-- Toast Notifications Container -->
    <div class="toast-container" id="toast-container"></div>

    <h1>Price Check File Upload System</h1>

    <div class="container">
        <!-- Left Section - Sample Files (2) -->
        <div class="upload-section">
            <div class="upload-progress" id="sample-progress"></div>
            <h2><i class="fas fa-vial"></i> Sample Files (2 Files)</h2>
            <form id="sample-form" onsubmit="event.preventDefault();">
                <label for="sample_file1">Sample File 1 (Import File):</label>
                <div class="file-requirement">File name must contain: <span style="color: red">"Import sales order"</span></div>

                <div class="file-input-container">
                    <label for="sample_file1" class="file-input-label">
                        <i class="fas fa-file-upload"></i> Choose Import File
                    </label>
                    <input type="file" id="sample_file1" required>
                    <div class="selected-file" id="sample-file1-name" style="display:none">
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">No file selected</span>
                        <span class="remove-file" onclick="removeFile('sample_file1')"><i class="fas fa-times"></i></span>
                    </div>
                </div>

                <label for="sample_file2">Sample File 2 (LO File):</label>
                <div class="file-requirement">File name must contain: <span style="color: red">"pricelist"</span></div>

                <div class="file-input-container">
                    <label for="sample_file2" class="file-input-label">
                        <i class="fas fa-file-upload"></i> Choose LO File
                    </label>
                    <input type="file" id="sample_file2" required>
                    <div class="selected-file" id="sample-file2-name" style="display:none">
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">No file selected</span>
                        <span class="remove-file" onclick="removeFile('sample_file2')"><i class="fas fa-times"></i></span>
                    </div>
                </div>

                <div class="error-message" id="sample-error"></div>
                <div class="success-message" id="sample-success"></div>

                <div class="button-group">
                    <button type="button" class="upload-btn" onclick="uploadSampleFiles()">
                        <i class="fas fa-upload"></i> Upload Sample Files
                    </button>
                    <div class="process-btn-container">
                        <div id="sample-spinner" class="spinner"></div>
                        <button type="button" id="sample-process-btn" class="process-btn" onclick="processSampleFiles()">
                            <i class="fas fa-cogs"></i> Process
                        </button>
                    </div>
                </div>
            </form>
        </div>

        <!-- Right Section - Bulk Files (4) -->
        <div class="upload-section">
            <div class="upload-progress" id="bulk-progress"></div>
            <h2><i class="fas fa-database"></i> Bulk Files (4 Files)</h2>
            <form id="bulk-form" onsubmit="event.preventDefault();">
                <label for="bulk_file1">Bulk File 1 (Import File):</label>
                <div class="file-requirement">File name must contain: <span style="color: red">"Import sales order"</span></div>

                <div class="file-input-container">
                    <label for="bulk_file1" class="file-input-label">
                        <i class="fas fa-file-upload"></i> Choose Import File
                    </label>
                    <input type="file" id="bulk_file1" required>
                    <div class="selected-file" id="bulk-file1-name" style="display:none">
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">No file selected</span>
                        <span class="remove-file" onclick="removeFile('bulk_file1')"><i class="fas fa-times"></i></span>
                    </div>
                </div>

                <label for="bulk_file2">Bulk File 2 (LineSheet SS):</label>
                <div class="file-requirement">File name must contain:<span style="color: red">"SS" or "Final all"</span> </div>

                <div class="file-input-container">
                    <label for="bulk_file2" class="file-input-label">
                        <i class="fas fa-file-upload"></i> Choose LineSheet SS File
                    </label>
                    <input type="file" id="bulk_file2" required>
                    <div class="selected-file" id="bulk-file2-name" style="display:none">
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">No file selected</span>
                        <span class="remove-file" onclick="removeFile('bulk_file2')"><i class="fas fa-times"></i></span>
                    </div>
                </div>

                <label for="bulk_file3">Bulk File 3 (Line Sheet FW):</label>
                <div class="file-requirement">File name must contain:<span style="color: red"> "FW" or "Final all"</span></div>

                <div class="file-input-container">
                    <label for="bulk_file3" class="file-input-label">
                        <i class="fas fa-file-upload"></i> Choose LineSheet FW File
                    </label>
                    <input type="file" id="bulk_file3" required>
                    <div class="selected-file" id="bulk-file3-name" style="display:none">
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">No file selected</span>
                        <span class="remove-file" onclick="removeFile('bulk_file3')"><i class="fas fa-times"></i></span>
                    </div>
                </div>

                <label for="bulk_file4">Bulk File 4 (Weekly):</label>
                <div class="file-requirement">File name must contain:<span style="color: red">"WEEKLY"</span> </div>

                <div class="file-input-container">
                    <label for="bulk_file4" class="file-input-label">
                        <i class="fas fa-file-upload"></i> Choose Weekly File
                    </label>
                    <input type="file" id="bulk_file4" required>
                    <div class="selected-file" id="bulk-file4-name" style="display:none">
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">No file selected</span>
                        <span class="remove-file" onclick="removeFile('bulk_file4')"><i class="fas fa-times"></i></span>
                    </div>
                </div>

                <div class="error-message" id="bulk-error"></div>
                <div class="success-message" id="bulk-success"></div>

                <div class="button-group">
                    <button type="button" class="upload-btn" onclick="uploadBulkFiles()">
                        <i class="fas fa-upload"></i> Upload Bulk Files
                    </button>
                    <div class="process-btn-container">
                        <div id="bulk-spinner" class="spinner"></div>
                        <button type="button" id="bulk-process-btn" class="process-btn" onclick="processBulkFiles()">
                            <i class="fas fa-cogs"></i> Process
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- Results Section -->
    <div class="results-section">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2><i class="fas fa-file-download"></i> Result Files</h2>
            <button type="button" class="refresh-btn" onclick="refreshResultFiles()">
                <i class="fas fa-sync-alt"></i> Refresh Files
            </button>
        </div>

        <div class="results-container">
            <div class="results-column">
                <h3><i class="fas fa-vial"></i> Sample Results</h3>
                <ul class="file-list" id="sample-result-files">
                    {sample_result_html}
                </ul>
            </div>
            <div class="results-column">
                <h3><i class="fas fa-exchange-alt"></i> Bulk Compare Results</h3>
                <ul class="file-list" id="bulk-compare-result-files">
                    {bulk_compare_html}
                </ul>
            </div>
            <div class="results-column">
                <h3><i class="fas fa-edit"></i> Bulk Updated Results</h3>
                <ul class="file-list" id="bulk-updated-result-files">
                    {bulk_updated_html}
                </ul>
            </div>
        </div>
    </div>

    <script src="/static/js/scripts.js"></script>
    <script>
    // File input display handling
    document.querySelectorAll('input[type="file"]').forEach(input => {{
        input.addEventListener('change', function() {{
            const fileNameDiv =
    document.getElementById(this.id.replace('_', '-') + '-name');
    const
    fileNameSpan = fileNameDiv.querySelector('.file-name');

    if (this.files.length > 0) {{
    fileNameSpan.textContent = this.files[0].name;
    fileNameDiv.style.display = 'flex';
    }} else {{
    fileNameDiv.style.display = 'none';
    }}
    }});
    }});

    // Remove file function
    function removeFile(inputId) {{
    const input = document.getElementById(inputId);
    input.value = '';
    const fileNameDiv = document.getElementById(inputId.replace('_', '-') + '-name');
    fileNameDiv.style.display = 'none';
    }}

    // Toast notification function
    function showToast(message, type) {{
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${{type}}`;

    const icon = type == = 'success' ? 'check-circle' : 'exclamation-circle';

        toast.innerHTML = `
            <div class="toast-icon"><i class="fas fa-${{icon}}"></i></div>
            <div class="toast-message">${{message}}</div>
            <div class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></div>
        `;

        toastContainer.appendChild(toast);

        // Remove toast after 3 seconds
        setTimeout(() => {{
    toast.remove();
    }}, 3000);
    }}

    // File validation with better feedback
    function validateFiles(formType) {{
    const form = document.getElementById(formType + '-form');
    const errorDiv = document.getElementById(formType + '-error');
    let isValid = true;
    let errorMessage = '';

    if (formType == = 'sample') {{
    const file1 = document.getElementById('sample_file1');
    const file2 = document.getElementById('sample_file2');

    if (!file1.files.length | | !file2.files.length) {{
    errorMessage = 'Please select all required files.';
    isValid = false;
    }} else {{
    if (!file1.files[0].name.includes('Import sales order')) {{
    errorMessage = 'Sample File 1 must contain "Import sales order" in its name.';
    isValid = false;
    }}
    if (!file2.files[0].name.toLowerCase().includes('pricelist')) {{
    errorMessage = 'Sample File 2 must contain "pricelist" in its name.';
    isValid = false;
    }}
    }} }} else if (formType === 'bulk') {{
    // Similar validation for bulk files
    //...
    }}

        if (!isValid) {{
    errorDiv.textContent = errorMessage;
    errorDiv.style.display = 'block';
    showToast(errorMessage, 'error');
    }} else {{
    errorDiv.style.display = 'none';
    }}

        return isValid;
    }}

    // Simulate upload progress
    function simulateProgress(formType) {{
    const progressBar = document.getElementById(formType + '-progress');
    let width = 0;

    const interval = setInterval(() = > {{
    if (width >= 100) {{
    clearInterval(interval);
    setTimeout(() = > {{
    progressBar.style.width = '0';
    }}, 500);
    }} else {{
    width += 5;
    progressBar.style.width = width + '%';
    }}
    }}, 100);
    }}
    </script>
</body>
</html>
    """
