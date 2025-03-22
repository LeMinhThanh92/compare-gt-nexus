// File validation patterns
const filePatterns = {
    sample: [
        {pattern: ["Import sales order"], id: "import", label: "Import File"},
        {pattern: ["pricelist"], id: "pricelist", label: "Pricelist File"}
    ],
    bulk: [
        {pattern: ["Import sales order"], id: "import", label: "Import File"},
        {pattern: ["SS", "Final all"], id: "ss", label: "LineSheet SS File"},
        {pattern: ["FW", "Final all"], id: "fw", label: "LineSheet FW File"},
        {pattern: ["WEEKLY"], id: "weekly", label: "Weekly File"}
    ]
};

// Global variables to store selected files
let sampleFiles = {};
let bulkFiles = {};

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeTabs();
    initializeDropzones();
    initializeFileInputs();
    checkUploadedFiles();
});

// Initialize tab functionality
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// Initialize dropzone functionality
function initializeDropzones() {
    setupDropzone('sample-dropzone', 'sample-file-input');
    setupDropzone('bulk-dropzone', 'bulk-file-input');
}

// Setup dropzone event listeners
function setupDropzone(dropzoneId, inputId) {
    const dropzone = document.getElementById(dropzoneId);
    const fileInput = document.getElementById(inputId);

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight dropzone when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.add('dragover');
        }, false);
    });

    // Remove highlight when dragging leaves dropzone
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.remove('dragover');
        }, false);
    });

    // Handle dropped files
    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        fileInput.files = files;
        handleFileSelect(fileInput);
    }, false);

    // Handle click on dropzone
    dropzone.addEventListener('click', () => {
        fileInput.click();
    }, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Initialize file input handlers
function initializeFileInputs() {
    document.getElementById('sample-file-input').addEventListener('change', handleFileSelect);
    document.getElementById('bulk-file-input').addEventListener('change', handleFileSelect);
}

// Handle file selection
function handleFileSelect(event) {
    const input = event.target || event;
    const files = Array.from(input.files);
    const type = input.id.includes('sample') ? 'sample' : 'bulk';

    // Categorize files based on filename patterns
    files.forEach(file => {
        const fileCategory = detectFileCategory(file.name, type);
        if (fileCategory) {
            if (type === 'sample') {
                sampleFiles[fileCategory.id] = file;
            } else {
                bulkFiles[fileCategory.id] = file;
            }
        }
    });

    // Display the categorized files
    displaySelectedFiles(type === 'sample' ? sampleFiles : bulkFiles, type);
    validateFiles(type);
}

// Detect file category based on filename
function detectFileCategory(fileName, type) {
    fileName = fileName.toLowerCase();
    const patterns = filePatterns[type];

    // More specific patterns should be checked first
    // FW vs SS detection needs special handling for LineSheet files
    if (type === 'bulk') {
        if (fileName.includes('fw')) {
            return patterns.find(p => p.id === 'fw');
        } else if (fileName.includes('ss')) {
            return patterns.find(p => p.id === 'ss');
        }
    }

    // Regular pattern matching for other files
    for (let i = 0; i < patterns.length; i++) {
        if (patterns[i].pattern.some(pattern => fileName.includes(pattern.toLowerCase()))) {
            return patterns[i];
        }
    }

    return null;
}

// Display selected files in the UI
function displaySelectedFiles(files, type) {
    const container = document.getElementById(`${type}-selected-files`);
    container.innerHTML = '';

    if (Object.keys(files).length === 0) {
        return;
    }

    // Get the patterns for the file type
    const patterns = filePatterns[type];

    // Display files in the order defined in filePatterns
    patterns.forEach(pattern => {
        const file = files[pattern.id];
        if (file) {
            const isValid = true; // File is valid because it matched a pattern
            const status = isValid ? 'valid' : 'invalid';
            const statusText = isValid ? 'Valid' : 'Invalid';

            // Create a badge to show the file type for clearer identification
            const fileTypeBadge = `<span class="file-type-badge">${pattern.label}</span>`;

            const fileItem = document.createElement('div');
            fileItem.className = `file-item file-${status}`;
            fileItem.innerHTML = `
                <div class="file-icon">
                    <i class="fas fa-file-excel"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    ${fileTypeBadge}
                </div>
                <div class="file-status ${status}">${statusText}</div>
                <button type="button" class="file-remove" data-type="${type}" data-id="${pattern.id}">
                    <i class="fas fa-times"></i>
                </button>
            `;

            container.appendChild(fileItem);
        }
    });

    // Add event listeners to remove buttons
    document.querySelectorAll('.file-remove').forEach(button => {
        button.addEventListener('click', removeFile);
    });
}

// Remove a file from the selection
function removeFile(event) {
    const button = event.currentTarget;
    const type = button.getAttribute('data-type');
    const id = button.getAttribute('data-id');

    if (type === 'sample') {
        delete sampleFiles[id];
        displaySelectedFiles(sampleFiles, 'sample');
    } else {
        delete bulkFiles[id];
        displaySelectedFiles(bulkFiles, 'bulk');
    }

    validateFiles(type);
}

// Validate files against required patterns
function validateFiles(type) {
    const fileObj = type === 'sample' ? sampleFiles : bulkFiles;
    const requiredPatterns = filePatterns[type];
    const uploadBtn = document.getElementById(`${type}-upload-btn`);

    // Check if we have files
    if (Object.keys(fileObj).length === 0) {
        uploadBtn.disabled = true;
        return false;
    }

    // Check if we have all required file types
    const hasAllRequiredTypes = requiredPatterns.every(pattern => {
        return fileObj[pattern.id] !== undefined;
    });

    // Update UI based on validation
    uploadBtn.disabled = !hasAllRequiredTypes;

    return hasAllRequiredTypes;
}

// This function is no longer needed as validation is handled differently
// Keeping it for reference but it's not used
function validateSingleFile(fileName, type) {
    fileName = fileName.toLowerCase();
    const patterns = filePatterns[type];

    return patterns.some(req =>
        req.pattern.some(pattern => fileName.includes(pattern.toLowerCase()))
    );
}

// Check if files have been uploaded and update UI accordingly
function checkUploadedFiles() {
    // This would typically check with the server if files have been uploaded
    // and enable the process buttons if they have
    fetch('/check-uploaded-files/')
        .then(response => response.json())
        .then(data => {
            if (data.sample_files_uploaded) {
                document.getElementById('sample-process-btn').disabled = false;
            }
            if (data.bulk_files_uploaded) {
                document.getElementById('bulk-process-btn').disabled = false;
            }
        })
        .catch(error => {
            console.error('Error checking uploaded files:', error);
        });
}

// Upload sample files
async function uploadSampleFiles() {
    if (Object.keys(sampleFiles).length === 0) {
        showToast('error', 'Error', 'No files selected');
        return;
    }

    if (!validateFiles('sample')) {
        showToast('error', 'Validation Error', 'All required files must be provided');
        return;
    }

    try {
        const formData = new FormData();
        // Use the file patterns to ensure consistent naming
        filePatterns.sample.forEach((pattern, index) => {
            if (sampleFiles[pattern.id]) {
                formData.append(`sample_file${index + 1}`, sampleFiles[pattern.id]);
            }
        });

        // Show upload progress
        showUploadProgress('sample');

        const response = await fetch('/upload-sample-files/', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showToast('success', 'Success', result.message || 'Sample files uploaded successfully');
            document.getElementById('sample-process-btn').disabled = false;
        } else {
            showToast('error', 'Error', result.detail || 'Failed to upload files');
        }
    } catch (error) {
        showToast('error', 'Error', `Upload failed: ${error.message}`);
    } finally {
        hideUploadProgress('sample');
    }
}

// Upload bulk files
async function uploadBulkFiles() {
    if (Object.keys(bulkFiles).length === 0) {
        showToast('error', 'Error', 'No files selected');
        return;
    }

    if (!validateFiles('bulk')) {
        showToast('error', 'Validation Error', 'All required files must be provided');
        return;
    }

    try {
        const formData = new FormData();
        // Use the file patterns to ensure consistent naming
        filePatterns.bulk.forEach((pattern, index) => {
            if (bulkFiles[pattern.id]) {
                formData.append(`bulk_file${index + 1}`, bulkFiles[pattern.id]);
            }
        });

        // Show upload progress
        showUploadProgress('bulk');

        const response = await fetch('/upload-bulk-files/', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showToast('success', 'Success', result.message || 'Bulk files uploaded successfully');
            document.getElementById('bulk-process-btn').disabled = false;
        } else {
            showToast('error', 'Error', result.detail || 'Failed to upload files');
        }
    } catch (error) {
        showToast('error', 'Error', `Upload failed: ${error.message}`);
    } finally {
        hideUploadProgress('bulk');
    }
}

// Process sample files
async function processSampleFiles() {
    try {
        // Show spinner
        document.getElementById('sample-spinner').style.display = 'inline-block';
        document.getElementById('sample-process-btn').disabled = true;

        const response = await fetch('/process-sample-files/', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            showToast('success', 'Success', result.message || 'Sample files processed successfully');
            refreshResultFiles();
            // Switch to results tab
            switchToResultsTab();
        } else {
            showToast('error', 'Error', result.detail || 'Failed to process files');
        }
    } catch (error) {
        showToast('error', 'Error', `Processing failed: ${error.message}`);
    } finally {
        document.getElementById('sample-spinner').style.display = 'none';
        document.getElementById('sample-process-btn').disabled = false;
    }
}

// Process bulk files
async function processBulkFiles() {
    try {
        // Show spinner
        document.getElementById('bulk-spinner').style.display = 'inline-block';
        document.getElementById('bulk-process-btn').disabled = true;

        const response = await fetch('/process-bulk-files/', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            showToast('success', 'Success', result.message || 'Bulk files processed successfully');
            refreshResultFiles();
            // Switch to results tab
            switchToResultsTab();
        } else {
            showToast('error', 'Error', result.detail || 'Failed to process files');
        }
    } catch (error) {
        showToast('error', 'Error', `Processing failed: ${error.message}`);
    } finally {
        document.getElementById('bulk-spinner').style.display = 'none';
        document.getElementById('bulk-process-btn').disabled = false;
    }
}

// Switch to results tab
function switchToResultsTab() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Remove active class from all buttons and contents
    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));

    // Add active class to results tab
    document.querySelector('[data-tab="results"]').classList.add('active');
    document.getElementById('results-tab').classList.add('active');
}

// Show upload progress animation
function showUploadProgress(type) {
    // This is a simplified implementation - in a real app, you would
    // use the fetch API's upload progress event
    const dropzone = document.getElementById(`${type}-dropzone`);
    dropzone.style.opacity = '0.7';
    dropzone.style.pointerEvents = 'none';

    // Add a progress bar or other visual indicator
    const icon = dropzone.querySelector('i');
    icon.className = 'fas fa-spinner fa-spin';
}

// Hide upload progress animation
function hideUploadProgress(type) {
    const dropzone = document.getElementById(`${type}-dropzone`);
    dropzone.style.opacity = '1';
    dropzone.style.pointerEvents = 'auto';

    // Restore the original icon
    const icon = dropzone.querySelector('i');
    icon.className = 'fas fa-cloud-upload-alt';
}

// Refresh result files
async function refreshResultFiles() {
    try {
        const response = await fetch('/get-result-files/');
        const data = await response.json();

        // Update sample result files
        updateResultsList('sample-result-files', data.sample_files, 'sample');

        // Update bulk compare result files
        updateResultsList('bulk-compare-result-files',
            data.bulk_files.filter(file => file[0].includes('Compare')), 'bulk');

        // Update bulk updated result files
        updateResultsList('bulk-updated-result-files',
            data.bulk_files.filter(file => file[0].includes('Updated')), 'bulk');

        showToast('success', 'Success', 'File list refreshed');
    } catch (error) {
        showToast('error', 'Error', `Failed to refresh file list: ${error.message}`);
    }
}

// Update a result files list
function updateResultsList(containerId, files, fileType) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (files.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'empty-message';
        emptyMessage.textContent = 'No files available';
        container.appendChild(emptyMessage);
        return;
    }

    files.forEach(file => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        resultItem.innerHTML = `
            <div class="result-item-content">
                <div class="file-icon">
                    <i class="fas fa-file-excel"></i>
                </div>
                <div class="file-info">
                    <div class="file-name">${file[0]}</div>
                    <div class="file-date">${file[1]}</div>
                </div>
            </div>
            <a href="/download-result/${fileType}/${file[0]}" class="download-button">
                <i class="fas fa-download"></i>
            </a>
        `;

        container.appendChild(resultItem);
    });
}

// Show toast notification
function showToast(type, title, message) {
    const toastContainer = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? 'check-circle' :
        type === 'error' ? 'exclamation-circle' : 'exclamation-triangle';

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${icon}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;

    // Add click event for close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    toastContainer.appendChild(toast);

    // Automatically remove toast after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}