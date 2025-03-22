def generate_html_template(sample_result_files, bulk_result_files):
    """Generate the HTML template for the home page with modern UI/UX"""

    # Generate HTML lists with file names and dates
    sample_result_html = "".join(
        f'<div class="result-item">'
        f'<div class="result-item-content">'
        f'<div class="file-icon"><i class="fas fa-file-excel"></i></div>'
        f'<div class="file-info">'
        f'<div class="file-name">{file}</div>'
        f'<div class="file-date">{date}</div>'
        f'</div>'
        f'</div>'
        f'<a href="/download-result/sample/{file}" class="download-button">'
        f'<i class="fas fa-download"></i>'
        f'</a>'
        f'</div>\n'
        for file, date in sample_result_files
    )

    bulk_compare_html = "".join(
        f'<div class="result-item">'
        f'<div class="result-item-content">'
        f'<div class="file-icon"><i class="fas fa-file-excel"></i></div>'
        f'<div class="file-info">'
        f'<div class="file-name">{file}</div>'
        f'<div class="file-date">{date}</div>'
        f'</div>'
        f'</div>'
        f'<a href="/download-result/bulk/{file}" class="download-button">'
        f'<i class="fas fa-download"></i>'
        f'</a>'
        f'</div>\n'
        for file, date in bulk_result_files if "Compare" in file
    )

    bulk_updated_html = "".join(
        f'<div class="result-item">'
        f'<div class="result-item-content">'
        f'<div class="file-icon"><i class="fas fa-file-excel"></i></div>'
        f'<div class="file-info">'
        f'<div class="file-name">{file}</div>'
        f'<div class="file-date">{date}</div>'
        f'</div>'
        f'</div>'
        f'<a href="/download-result/bulk/{file}" class="download-button">'
        f'<i class="fas fa-download"></i>'
        f'</a>'
        f'</div>\n'
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

    <!-- Header -->
    <header class="app-header">
        <div class="container">
            <h1>Price Check File Upload System</h1>
        </div>
    </header>

    <main class="container">
        <div class="app-card">
            <!-- Tab Navigation -->
            <div class="tabs">
                <button class="tab-btn active" data-tab="upload">Upload Files</button>
                <button class="tab-btn" data-tab="results">Result Files</button>
            </div>

            <!-- Upload Tab Content -->
            <div class="tab-content active" id="upload-tab">
                <div class="upload-container">
                    <!-- Sample Files Section -->
                    <div class="upload-section">
                        <div class="section-header">
                            <h2><i class="fas fa-vial"></i> Sample Files</h2>
                            <span class="badge">2 Files Required</span>
                        </div>

                        <div class="dropzone" id="sample-dropzone">
                            <div class="dropzone-content">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>Drag and drop files here</p>
                                <p>or</p>
                                <label for="sample-file-input" class="btn">Select Files</label>
                                <input type="file" id="sample-file-input" multiple style="display: none;">
                            </div>
                        </div>

                        <div class="file-requirements">
                            <p><strong>Required Files:</strong></p>
                            <ul>
                                <li>File 1: Must contain "<span class="highlight">Import sales order</span>" in filename</li>
                                <li>File 2: Must contain "<span class="highlight">pricelist</span>" in filename</li>
                            </ul>
                        </div>

                        <div class="selected-files" id="sample-selected-files">
                            <!-- Files will be added here via JavaScript -->
                        </div>

                        <div class="action-buttons">
                            <button type="button" id="sample-upload-btn" class="btn primary-btn" onclick="uploadSampleFiles()">
                                <i class="fas fa-upload"></i> Upload
                            </button>
                            <button type="button" id="sample-process-btn" class="btn secondary-btn" onclick="processSampleFiles()" disabled>
                                <i class="fas fa-cogs"></i> Process
                                <span class="spinner" id="sample-spinner"></span>
                            </button>
                        </div>
                    </div>

                    <!-- Bulk Files Section -->
                    <div class="upload-section">
                        <div class="section-header">
                            <h2><i class="fas fa-database"></i> Bulk Files</h2>
                            <span class="badge">4 Files Required</span>
                        </div>

                        <div class="dropzone" id="bulk-dropzone">
                            <div class="dropzone-content">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>Drag and drop files here</p>
                                <p>or</p>
                                <label for="bulk-file-input" class="btn">Select Files</label>
                                <input type="file" id="bulk-file-input" multiple style="display: none;">
                            </div>
                        </div>

                        <div class="file-requirements">
                            <p><strong>Required Files:</strong></p>
                            <ul>
                                <li>File 1: Must contain "<span class="highlight">Import sales order</span>" in filename</li>
                                <li>File 2: Must contain "<span class="highlight">SS</span>" and "<span class="highlight">Final all</span>" in filename</li>
                                <li>File 3: Must contain "<span class="highlight">FW</span>" and "<span class="highlight">Final all</span>" in filename</li>
                                <li>File 4: Must contain "<span class="highlight">WEEKLY</span>" in filename</li>
                            </ul>
                        </div>

                        <div class="selected-files" id="bulk-selected-files">
                            <!-- Files will be added here via JavaScript -->
                        </div>

                        <div class="action-buttons">
                            <button type="button" id="bulk-upload-btn" class="btn primary-btn" onclick="uploadBulkFiles()">
                                <i class="fas fa-upload"></i> Upload
                            </button>
                            <button type="button" id="bulk-process-btn" class="btn secondary-btn" onclick="processBulkFiles()" disabled>
                                <i class="fas fa-cogs"></i> Process
                                <span class="spinner" id="bulk-spinner"></span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Results Tab Content -->
            <div class="tab-content" id="results-tab">
                <div class="results-container">
                    <div class="results-header">
                        <h2>Result Files</h2>
                        <button type="button" class="btn refresh-btn" onclick="refreshResultFiles()">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>

                    <div class="results-grid">
                        <div class="results-section">
                            <h3><i class="fas fa-vial"></i> Sample Results</h3>
                            <div class="results-list" id="sample-result-files">
                                ${sample_result_html}
                            </div>
                        </div>

                        <div class="results-section">
                            <h3><i class="fas fa-exchange-alt"></i> Bulk Compare Results</h3>
                            <div class="results-list" id="bulk-compare-result-files">
                                ${bulk_compare_html}
                            </div>
                        </div>

                        <div class="results-section">
                            <h3><i class="fas fa-edit"></i> Bulk Updated Results</h3>
                            <div class="results-list" id="bulk-updated-result-files">
                                ${bulk_updated_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script src="/static/js/scripts.js"></script>
</body>
</html>
    """
