async function uploadSampleFiles() {
    const file1 = document.getElementById("sample_file1").files[0];
    const file2 = document.getElementById("sample_file2").files[0];

    // Reset error messages
    document.getElementById("sample-error").style.display = "none";
    document.getElementById("sample-success").style.display = "none";

    // Validate file names
    let isValid = true;
    let errorMsg = "";

    if (!file1 || !validateFileName(file1.name, ["Import sales order"])) {
        isValid = false;
        errorMsg += "Sample File 1 must contain 'Import sales order' in the filename. ";
    }

    if (!file2 || !validateFileName(file2.name, ["pricelist"])) {
        isValid = false;
        errorMsg += "Sample File 2 must contain 'pricelist' in the filename.";
    }

    if (!isValid) {
        document.getElementById("sample-error").textContent = errorMsg;
        document.getElementById("sample-error").style.display = "block";
        return;
    }

    let formData = new FormData();
    formData.append("sample_file1", file1);
    formData.append("sample_file2", file2);

    try {
        let response = await fetch("/upload-sample-files/", {
            method: "POST",
            body: formData
        });

        let result = await response.json();
        if (response.ok) {
            document.getElementById("sample-success").textContent = result.message || "Sample files uploaded successfully!";
            document.getElementById("sample-success").style.display = "block";
        } else {
            document.getElementById("sample-error").textContent = result.detail || "Error uploading files";
            document.getElementById("sample-error").style.display = "block";
        }
    } catch (error) {
        document.getElementById("sample-error").textContent = "Error uploading sample files: " + error.message;
        document.getElementById("sample-error").style.display = "block";
    }
}

async function uploadBulkFiles() {
    const file1 = document.getElementById("bulk_file1").files[0];
    const file2 = document.getElementById("bulk_file2").files[0];
    const file3 = document.getElementById("bulk_file3").files[0];
    const file4 = document.getElementById("bulk_file4").files[0];

    // Reset error messages
    document.getElementById("bulk-error").style.display = "none";
    document.getElementById("bulk-success").style.display = "none";

    // Validate file names
    let isValid = true;
    let errorMsg = "";

    if (!file1 || !validateFileName(file1.name, ["Import sales order"])) {
        isValid = false;
        errorMsg += "Bulk File 1 must contain 'Import sales order' in the filename. ";
    }

    if (!file2 || !validateFileName(file2.name, ["SS", "Final all"])) {
        isValid = false;
        errorMsg += "Bulk File 2 must contain 'SS' or 'Final all' in the filename. ";
    }

    if (!file3 || !validateFileName(file3.name, ["FW", "Final all"])) {
        isValid = false;
        errorMsg += "Bulk File 3 must contain 'FW' or 'Final all' in the filename. ";
    }

    if (!file4 || !validateFileName(file4.name, ["WEEKLY"])) {
        isValid = false;
        errorMsg += "Bulk File 4 must contain 'WEEKLY' in the filename.";
    }

    if (!isValid) {
        document.getElementById("bulk-error").textContent = errorMsg;
        document.getElementById("bulk-error").style.display = "block";
        return;
    }

    let formData = new FormData();
    formData.append("bulk_file1", file1);
    formData.append("bulk_file2", file2);
    formData.append("bulk_file3", file3);
    formData.append("bulk_file4", file4);

    try {
        let response = await fetch("/upload-bulk-files/", {
            method: "POST",
            body: formData
        });

        let result = await response.json();
        if (response.ok) {
            document.getElementById("bulk-success").textContent = result.message || "Bulk files uploaded successfully!";
            document.getElementById("bulk-success").style.display = "block";
        } else {
            document.getElementById("bulk-error").textContent = result.detail || "Error uploading files";
            document.getElementById("bulk-error").style.display = "block";
        }
    } catch (error) {
        document.getElementById("bulk-error").textContent = "Error uploading bulk files: " + error.message;
        document.getElementById("bulk-error").style.display = "block";
    }
}

async function processSampleFiles() {
    try {
        // Show spinner and disable button
        document.getElementById("sample-spinner").style.display = "inline-block";
        const processBtn = document.getElementById("sample-process-btn");
        processBtn.classList.add("disabled");
        processBtn.disabled = true;

        document.getElementById("sample-error").style.display = "none";
        document.getElementById("sample-success").style.display = "none";

        let response = await fetch("/process-sample-files/", {
            method: "POST"
        });

        let result = await response.json();

        if (response.ok) {
            document.getElementById("sample-success").textContent = result.message || "Sample files processed successfully!";
            document.getElementById("sample-success").style.display = "block";
            // Refresh the file list
            refreshResultFiles();
        } else {
            document.getElementById("sample-error").textContent = result.detail || "Error processing files";
            document.getElementById("sample-error").style.display = "block";
        }
    } catch (error) {
        document.getElementById("sample-error").textContent = "Error processing sample files: " + error.message;
        document.getElementById("sample-error").style.display = "block";
    } finally {
        // Hide spinner and enable button
        document.getElementById("sample-spinner").style.display = "none";
        const processBtn = document.getElementById("sample-process-btn");
        processBtn.classList.remove("disabled");
        processBtn.disabled = false;
    }
}

async function processBulkFiles() {
    try {
        // Show spinner and disable button
        document.getElementById("bulk-spinner").style.display = "inline-block";
        const processBtn = document.getElementById("bulk-process-btn");
        processBtn.classList.add("disabled");
        processBtn.disabled = true;

        document.getElementById("bulk-error").style.display = "none";
        document.getElementById("bulk-success").style.display = "none";

        let response = await fetch("/process-bulk-files/", {
            method: "POST"
        });

        let result = await response.json();

        if (response.ok) {
            document.getElementById("bulk-success").textContent = result.message || "Bulk files processed successfully!";
            document.getElementById("bulk-success").style.display = "block";
            // Refresh the file list
            refreshResultFiles();
        } else {
            document.getElementById("bulk-error").textContent = result.detail || "Error processing files";
            document.getElementById("bulk-error").style.display = "block";
        }
    } catch (error) {
        document.getElementById("bulk-error").textContent = "Error processing bulk files: " + error.message;
        document.getElementById("bulk-error").style.display = "block";
    } finally {
        // Hide spinner and enable button
        document.getElementById("bulk-spinner").style.display = "none";
        const processBtn = document.getElementById("bulk-process-btn");
        processBtn.classList.remove("disabled");
        processBtn.disabled = false;
    }
}

function validateFileName(filename, patterns) {
    filename = filename.toLowerCase();
    for (let pattern of patterns) {
        if (filename.includes(pattern.toLowerCase())) {
            return true;
        }
    }
    return false;
}

async function refreshResultFiles() {
    try {
        let response = await fetch("/get-result-files/");
        let data = await response.json();
        // Update Sample Result Files
        const sampleFileList = document.getElementById("sample-result-files");
        sampleFileList.innerHTML = "";
        data.sample_files.forEach(file => {
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = `/download-result/sample/${file[0]}`;
            a.textContent = file[0];
            li.appendChild(a);
            const dateSpan = document.createElement("small");
            dateSpan.textContent = ` ${file[1]}`;
            li.appendChild(document.createTextNode(" "));
            li.appendChild(dateSpan);

            sampleFileList.appendChild(li);
        });

        // Update Bulk Result Files
        const bulkFileList = document.getElementById("bulk-compare-result-files");
        bulkFileList.innerHTML = "";
        data.bulk_files.forEach(file => {
            if (file[0].includes("Compare")) {
                const li = document.createElement("li");
                const a = document.createElement("a");
                a.href = `/download-result/bulk/${file[0]}`;
                a.textContent = file[0];
                li.appendChild(a);

                // Add date in small tag
                const dateSpan = document.createElement("small");
                dateSpan.textContent = ` ${file[1]}`;
                li.appendChild(document.createTextNode(" "));
                li.appendChild(dateSpan);

                bulkFileList.appendChild(li);
            }
        });

        const bulkFileList1 = document.getElementById("bulk-updated-result-files");
        bulkFileList1.innerHTML = "";
        data.bulk_files.forEach(file => {
            if (file[0].includes("Update")) {
                const li = document.createElement("li");
                const a = document.createElement("a");
                a.href = `/download-result/bulk/${file[0]}`;
                a.textContent = file[0];
                li.appendChild(a);

                // Add date in small tag
                const dateSpan = document.createElement("small");
                dateSpan.textContent = ` ${file[1]}`;
                li.appendChild(document.createTextNode(" "));
                li.appendChild(dateSpan);

                bulkFileList1.appendChild(li);
            }
        });
    } catch (error) {
        console.error("Error refreshing file list:", error);
    }
}