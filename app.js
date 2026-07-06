// App Configuration and State
const API_BASE_URL = 'https://yhresearcher--vietocr-service-fastapi-app-fastapi-app.modal.run';
let currentFile = null;
let ocrResult = null;

// PDF Rendering State
let pdfDoc = null;
let pdfPageNum = 1;
let pdfPageRendering = false;
let pdfPendingPageNum = null;

// DOM Elements
const elements = {
    dropzone: document.getElementById('upload-dropzone'),
    fileInput: document.getElementById('file-input'),
    dropzoneDefault: document.getElementById('dropzone-default'),
    dropzonePreview: document.getElementById('dropzone-preview'),
    imageElement: document.getElementById('image-element'),
    btnRemoveImage: document.getElementById('btn-remove-image'),
    btnProcess: document.getElementById('btn-process'),

    // PDF elements
    pdfOptionsContainer: document.getElementById('pdf-options-container'),
    btnPrevPage: document.getElementById('btn-prev-page'),
    btnNextPage: document.getElementById('btn-next-page'),
    pdfPageInput: document.getElementById('pdf-page-input'),
    pdfTotalPages: document.getElementById('pdf-total-pages'),
    pdfPreviewCanvas: document.getElementById('pdf-preview-canvas'),
    pdfScanMode: document.getElementById('pdf-scan-mode'),

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

    // PDF page navigation buttons
    elements.btnPrevPage.addEventListener('click', onPrevPage);
    elements.btnNextPage.addEventListener('click', onNextPage);
    elements.pdfPageInput.addEventListener('change', onPageInputChange);
    elements.pdfScanMode.addEventListener('change', handleScanModeChange);

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
    const isPDF = file.type === 'application/pdf' || file.name.endsWith('.pdf');
    const isImage = file.type.startsWith('image/');

    if (!isPDF && !isImage) {
        showToast('Vui lòng chọn file hình ảnh (PNG, JPG, JPEG) hoặc tài liệu PDF.', 'error');
        return;
    }

    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        showToast('Kích thước tệp vượt quá giới hạn 50MB.', 'error');
        return;
    }

    currentFile = file;

    if (isPDF) {
        // Reset image previews
        elements.imageElement.src = '#';
        elements.imageElement.classList.add('hidden');
        elements.pdfPreviewCanvas.classList.remove('hidden');
        elements.dropzoneDefault.classList.add('hidden');
        elements.dropzonePreview.classList.remove('hidden');

        // Reset PDF scan mode and help texts
        elements.pdfScanMode.value = 'current';
        elements.pdfScanMode.disabled = false;
        elements.pdfPageInput.disabled = false;
        document.getElementById('pdf-page-help-text').textContent = "Di chuyển qua lại hoặc nhập số trang để chọn trang muốn nhận dạng chữ.";

        // Display spinner during PDF parsing
        elements.btnProcess.setAttribute('disabled', 'true');
        showToast('Đang tải và phân tích tài liệu PDF...', 'success');

        const fileReader = new FileReader();
        fileReader.onload = function () {
            const typedarray = new Uint8Array(this.result);
            // Configure PDF.js worker
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

            pdfjsLib.getDocument({ data: typedarray }).promise.then(pdf => {
                pdfDoc = pdf;
                elements.pdfTotalPages.textContent = pdf.numPages;
                elements.pdfPageInput.max = pdf.numPages;
                pdfPageNum = 1;
                elements.pdfPageInput.value = 1;

                elements.pdfOptionsContainer.classList.remove('hidden');
                elements.btnProcess.removeAttribute('disabled');

                renderPage(pdfPageNum);
                showToast(`Đã tải tài liệu PDF: ${file.name} (${pdf.numPages} trang)`, 'success');
            }).catch(error => {
                showToast('Lỗi khi phân tích file PDF.', 'error');
                console.error(error);
                resetUpload();
            });
        };
        fileReader.readAsArrayBuffer(file);
    } else {
        // Handle normal Image
        pdfDoc = null;
        elements.pdfOptionsContainer.classList.add('hidden');
        elements.pdfPreviewCanvas.classList.add('hidden');
        elements.imageElement.classList.remove('hidden');

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
}

// Reset dropzone state
function resetUpload() {
    currentFile = null;
    elements.fileInput.value = '';
    elements.imageElement.src = '#';

    // Reset PDF States
    pdfDoc = null;
    pdfPageNum = 1;
    pdfPageRendering = false;
    pdfPendingPageNum = null;
    elements.pdfScanMode.value = 'current';
    elements.pdfScanMode.disabled = false;
    elements.pdfPageInput.disabled = false;
    elements.pdfOptionsContainer.classList.add('hidden');
    elements.pdfPreviewCanvas.classList.add('hidden');
    elements.imageElement.classList.remove('hidden');

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

    try {
        formData.append('file', currentFile, currentFile.name);

        if (pdfDoc) {
            const scanMode = elements.pdfScanMode.value;
            if (scanMode === 'current') {
                formData.append('pages', pdfPageNum.toString());
                showToast(`Đang gửi trang ${pdfPageNum} đi nhận dạng...`, 'success');
            } else {
                showToast('Đang tải và nhận dạng toàn bộ tài liệu PDF...', 'success');
            }
        } else {
            showToast('Đang gửi hình ảnh đi nhận dạng...', 'success');
        }

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
        showToast('Lỗi trong quá trình nhận dạng chữ.', 'error');
        elements.resultEmpty.classList.remove('hidden');
        console.error('OCR Process Error:', error);
    } finally {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// PDF.js Page Rendering Helpers
function renderPage(num) {
    if (!pdfDoc) return;
    pdfPageRendering = true;

    pdfDoc.getPage(num).then(page => {
        const canvas = elements.pdfPreviewCanvas;
        const context = canvas.getContext('2d');

        // Render a reasonable sized preview thumbnail (scale = 0.8)
        const viewport = page.getViewport({ scale: 0.8 });
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        // Draw white background
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, canvas.width, canvas.height);

        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        const renderTask = page.render(renderContext);

        renderTask.promise.then(() => {
            pdfPageRendering = false;

            // Enable/disable page buttons
            elements.btnPrevPage.disabled = (num <= 1);
            elements.btnNextPage.disabled = (num >= pdfDoc.numPages);

            if (pdfPendingPageNum !== null) {
                renderPage(pdfPendingPageNum);
                pdfPendingPageNum = null;
            }
        });
    });
}

function queueRenderPage(num) {
    if (pdfPageRendering) {
        pdfPendingPageNum = num;
    } else {
        renderPage(num);
    }
}

function onPrevPage() {
    if (!pdfDoc || pdfPageNum <= 1) return;
    pdfPageNum--;
    elements.pdfPageInput.value = pdfPageNum;
    queueRenderPage(pdfPageNum);
}

function onNextPage() {
    if (!pdfDoc || pdfPageNum >= pdfDoc.numPages) return;
    pdfPageNum++;
    elements.pdfPageInput.value = pdfPageNum;
    queueRenderPage(pdfPageNum);
}

function onPageInputChange(e) {
    if (!pdfDoc) return;
    let val = parseInt(e.target.value);
    if (isNaN(val)) return;
    if (val < 1) val = 1;
    if (val > pdfDoc.numPages) val = pdfDoc.numPages;
    pdfPageNum = val;
    e.target.value = val;
    queueRenderPage(pdfPageNum);
}

// Display results in UI
function displayOcrResult(data, durationSec) {
    // 1. Text Area Tab
    elements.textOutput.value = data.full_text || data.text || '';

    // 2. Lines View Tab
    elements.linesList.innerHTML = '';
    const lines = data.lines || [];
    if (lines.length > 0) {
        lines.forEach((line, index) => {
            // Support both old format (string) and new format ({text, confidence})
            const lineText = typeof line === 'string' ? line : line.text;
            const confidence = typeof line === 'object' ? line.confidence : null;

            const item = document.createElement('div');
            item.className = 'line-item';

            const num = document.createElement('span');
            num.className = 'line-number';
            num.innerText = index + 1;

            const textEl = document.createElement('span');
            textEl.className = 'line-text';
            textEl.innerText = lineText;

            // Show confidence badge if available
            if (confidence !== null) {
                const confBadge = document.createElement('span');
                const confPercent = Math.round(confidence * 100);
                let confClass = 'conf-high';
                if (confPercent < 70) confClass = 'conf-low';
                else if (confPercent < 85) confClass = 'conf-medium';
                confBadge.className = `line-confidence ${confClass}`;
                confBadge.innerText = `${confPercent}%`;
                confBadge.title = `Độ chính xác: ${confPercent}%`;
                item.appendChild(confBadge);
            }

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

// PDF Scan Mode Change Listener
function handleScanModeChange(e) {
    const isAll = e.target.value === 'all';

    // Disable/enable page navigation based on mode
    elements.btnPrevPage.disabled = isAll || (pdfPageNum <= 1);
    elements.btnNextPage.disabled = isAll || (pdfPageNum >= (pdfDoc ? pdfDoc.numPages : 1));
    elements.pdfPageInput.disabled = isAll;

    const helpText = document.getElementById('pdf-page-help-text');
    if (isAll) {
        helpText.textContent = "Toàn bộ các trang trong tài liệu PDF sẽ được nhận dạng chữ.";
    } else {
        helpText.textContent = "Di chuyển qua lại hoặc nhập số trang để chọn trang muốn nhận dạng chữ.";
    }
}
