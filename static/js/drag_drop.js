// Drag and drop functionality for file upload
class DragDropUploader {
    constructor(dropZoneId, fileInputId, options = {}) {
        this.dropZone = document.getElementById(dropZoneId);
        this.fileInput = document.getElementById(fileInputId);
        this.options = {
            acceptedTypes: options.acceptedTypes || ['text/csv'],
            maxSize: options.maxSize || 50 * 1024 * 1024, // 50MB default
            onFileSelected: options.onFileSelected || (() => { }),
            onError: options.onError || ((error) => console.error(error))
        };

        this.init();
    }

    init() {
        if (!this.dropZone || !this.fileInput) {
            console.error('Drop zone or file input not found');
            return;
        }

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.highlight(), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.unhighlight(), false);
        });

        // Handle dropped files
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);

        // Handle click to select file
        this.dropZone.addEventListener('click', () => this.fileInput.click());

        // Handle file input change
        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight() {
        this.dropZone.classList.add('drag-over');
    }

    unhighlight() {
        this.dropZone.classList.remove('drag-over');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    handleFiles(files) {
        if (files.length === 0) return;

        const file = files[0];

        // Validate file type - be more permissive with CSV files
        const isCSV = file.name.toLowerCase().endsWith('.csv') ||
            file.type === 'text/csv' ||
            file.type === 'application/vnd.ms-excel';

        if (!isCSV) {
            this.options.onError(`Invalid file type. Please upload a CSV file.`);
            return;
        }

        // Validate file size
        if (file.size > this.options.maxSize) {
            this.options.onError(`File too large. Maximum size: ${this.formatBytes(this.options.maxSize)}`);
            return;
        }

        this.options.onFileSelected(file);
    }

    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
}

// File preview functionality
function createFilePreview(file, previewContainerId) {
    const container = document.getElementById(previewContainerId);
    if (!container) return;

    const reader = new FileReader();

    reader.onload = function (e) {
        const content = e.target.result;
        const lines = content.split('\n').slice(0, 6); // First 6 lines

        let html = `
            <div class="file-preview-card">
                <div class="file-info mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1"><i class="fas fa-file-csv text-success"></i> ${file.name}</h6>
                            <small class="text-muted">${formatBytes(file.size)}</small>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="clearFilePreview()">
                            <i class="fas fa-times"></i> Remove
                        </button>
                    </div>
                </div>
                <div class="preview-table">
                    <h6 class="mb-2">Preview (first 5 rows)</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead class="table-dark">
                                <tr>
                                    ${lines[0].split(',').map(col => `<th>${col.trim()}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${lines.slice(1, 6).map(line =>
            `<tr>${line.split(',').map(cell => `<td>${cell.trim()}</td>`).join('')}</tr>`
        ).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
        container.style.display = 'block';
    };

    reader.readAsText(file);
}

function clearFilePreview() {
    const container = document.getElementById('file-preview');
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }

    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
        fileInput.value = '';
    }
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Animated progress bar
function animateProgress(elementId, targetPercentage, duration = 1000) {
    const element = document.getElementById(elementId);
    if (!element) return;

    let start = null;
    const startPercentage = parseInt(element.style.width) || 0;

    function step(timestamp) {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        const currentPercentage = startPercentage + (targetPercentage - startPercentage) * progress;

        element.style.width = currentPercentage + '%';
        element.textContent = Math.round(currentPercentage) + '%';

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}
