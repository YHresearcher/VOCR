// App Configuration and State
const API_BASE_URL = 'https://yhresearcher--vietocr-service-fastapi-app.modal.run';
let currentFile = null;
let ocrResult = null;

// DOM Elements
const elements = {
    dropzone: document.getElementById('upload-dropzone'),
    fileInput: document.getElementById('file-input'),
    dropzoneDefault: document.getElementById('dropzone-default'),
    dropzonePreview: document.getElementById('dropzone-preview'),
    imageElement: document.getElementById('image-element'),
    btnRemoveImage: document.getElementById('btn-remove-image'),
    btnProcess: document.getElementById('btn-process'),
    
    // Tab Elements
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Output Elements
    loadingOverlay: document.getElementById('loading-overlay'),
    resultEmpty: document.getElementById('result-empty'),
    resultFooter: document.getElementById('result-footer'),
    textOutput: document.getElementById('text-output'),
    linesList: document.getElementById('lines-list'),
    jsonOutput: document.getElementById('json-output'),
    
    // Actions
    btnCopyText: document.getElementById('btn-copy-text'),
    btnDownloadTxt: document.getElementById('btn-download-txt'),
    btnDownloadJson: document.getElementById('btn-download-json'),
    
    // Stats
    statLinesCount: document.getElementById('stat-lines-count'),
    statTime: document.getElementById('stat-time'),
    
    // API Badge
    apiStatusBadge: document.getElementById('api-status-badge'),
    toastContainer: document.getElementById('toast-container')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    checkApiStatus();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    // File Inputs
    elements.dropzone.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Drag and Drop
    ['dragenter', 'dragover'].forEach(eventName => {
        elements.dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            elements.dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        elements.dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            elements.dropzone.classList.remove('dragover');
        }, false);
    });

    elements.dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            validateAndSetFile(files[0]);
        }
    });

    // Remove Image Button
    elements.btnRemoveImage.addEventListener('click', (e) => {
        e.stopPropagation(); // Avoid triggering file input click
        resetUpload();
    });

    // Process OCR Button
    elements.btnProcess.addEventListener('click', processOcr);

    // Tab Buttons switching
    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Copy to clipboard
    elements.btnCopyText.addEventListener('click', copyTextToClipboard);

    // Downloads
    elements.btnDownloadTxt.addEventListener('click', downloadTxtFile);
    elements.btnDownloadJson.addEventListener('click', downloadJsonFile);
}

// Check if API is Online
async function checkApiStatus() {
    const badge = elements.apiStatusBadge;
    const indicator = badge.querySelector('.status-indicator');
    const label = badge.querySelector('.status-label');

    try {
        const response = await fetch(`${API_BASE_URL}/`, { method: 'GET' });
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'running') {
                indicator.className = 'status-indicator online';
                label.innerText = 'API Sẵn sàng (Modal)';
                showToast('Kết nối API thành công!', 'success');
                return;
            }
        }
        throw new Error('API returns invalid health data.');
    } catch (error) {
        indicator.className = 'status-indicator offline';
        label.innerText = 'API Ngoại tuyến';
        showToast('Không thể kết nối đến API VietOCR trên Modal.', 'error');
        console.error('API Status Error:', error);
    }
}

// File Select Handlers
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length) {
        validateAndSetFile(files[0]);
    }
}

// Validate file sizes and types
function validateAndSetFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Vui lòng chọn file hình ảnh hợp lệ (PNG, JPG, JPEG).', 'error');
        return;
    }
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showToast('Kích thước ảnh vượt quá giới hạn 10MB.', 'error');
        return;
    }

    currentFile = file;

    // Display preview
    const reader = new FileReader();
    reader.onload = (e) => {
        elements.imageElement.src = e.target.result;
        elements.dropzoneDefault.classList.add('hidden');
        elements.dropzonePreview.classList.remove('hidden');
        elements.btnProcess.removeAttribute('disabled');
        showToast(`Đã tải ảnh: ${file.name}`, 'success');
    };
    reader.readAsDataURL(file);
}

// Reset dropzone state
function resetUpload() {
    currentFile = null;
    elements.fileInput.value = '';
    elements.imageElement.src = '#';
    elements.dropzoneDefault.classList.remove('hidden');
    elements.dropzonePreview.classList.add('hidden');
    elements.btnProcess.setAttribute('disabled', 'true');
    
    // Clear OCR results state
    ocrResult = null;
    elements.resultEmpty.classList.remove('hidden');
    elements.resultFooter.classList.add('hidden');
    elements.textOutput.value = '';
    elements.linesList.innerHTML = '';
    elements.jsonOutput.innerText = '// Dữ liệu JSON raw từ API';
    switchTab('plain-text');
}

// Switch active tab UI
function switchTab(tabId) {
    elements.tabButtons.forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    elements.tabContents.forEach(content => {
        if (content.id === `tab-${tabId}`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// Call the VietOCR POST Endpoint
async function processOcr() {
    if (!currentFile) return;

    elements.loadingOverlay.classList.remove('hidden');
    elements.resultEmpty.classList.add('hidden');
    elements.resultFooter.classList.add('hidden');

    const startTime = performance.now();
    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch(`${API_BASE_URL}/ocr`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`API response error: status ${response.status}`);
        }

        const data = await response.json();
        const duration = ((performance.now() - startTime) / 1000).toFixed(2);
        
        ocrResult = data;
        displayOcrResult(data, duration);
        showToast('Nhận dạng chữ thành công!', 'success');
    } catch (error) {
        showToast('Lỗi trong quá trình nhận dạng ảnh.', 'error');
        elements.resultEmpty.classList.remove('hidden');
        console.error('OCR Process Error:', error);
    } finally {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// Display results in UI
function displayOcrResult(data, durationSec) {
    // 1. Text Area Tab
    elements.textOutput.value = data.full_text || data.text || '';
    
    // 2. Lines View Tab
    elements.linesList.innerHTML = '';
    const lines = data.lines || [];
    if (lines.length > 0) {
        lines.forEach((lineText, index) => {
            const item = document.createElement('div');
            item.className = 'line-item';
            
            const num = document.createElement('span');
            num.className = 'line-number';
            num.innerText = index + 1;
            
            const textEl = document.createElement('span');
            textEl.className = 'line-text';
            textEl.innerText = lineText;
            
            item.appendChild(num);
            item.appendChild(textEl);
            elements.linesList.appendChild(item);
        });
    } else {
        elements.linesList.innerHTML = '<p class="empty-subtitle" style="margin: 2rem auto;">Không phát hiện thấy dòng chữ nào.</p>';
    }

    // 3. JSON Output Tab
    elements.jsonOutput.innerText = JSON.stringify(data, null, 2);

    // 4. Stats and Footer
    elements.statLinesCount.innerText = data.box_count || lines.length || 0;
    elements.statTime.innerText = `${durationSec}s`;
    elements.resultFooter.classList.remove('hidden');
}

// Copy plain text to clipboard
function copyTextToClipboard() {
    const text = elements.textOutput.value;
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        showToast('Đã sao chép vào bộ nhớ tạm!', 'success');
    }).catch(err => {
        showToast('Không thể sao chép văn bản.', 'error');
        console.error('Copy Error:', err);
    });
}

// Download Plain Text File
function downloadTxtFile() {
    if (!ocrResult) return;
    const text = elements.textOutput.value;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vietocr_result_${Date.now()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
}

// Download JSON File
function downloadJsonFile() {
    if (!ocrResult) return;
    const blob = new Blob([JSON.stringify(ocrResult, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vietocr_result_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
}

// Toast Notifications Helper
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = document.createElement('i');
    if (type === 'success') {
        icon.className = 'fa-solid fa-circle-check toast-icon success';
    } else {
        icon.className = 'fa-solid fa-circle-xmark toast-icon error';
    }
    
    const text = document.createElement('span');
    text.className = 'toast-message';
    text.innerText = message;
    
    toast.appendChild(icon);
    toast.appendChild(text);
    elements.toastContainer.appendChild(toast);
    
    // Automatically remove toast after 3.5 seconds
    setTimeout(() => {
        toast.style.animation = 'slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
