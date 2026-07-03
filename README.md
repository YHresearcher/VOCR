# VietOCR Portal & Training System 🧠📝

**VietOCR Portal** là một cổng thông tin và công cụ trực tuyến hiện đại sử dụng trí tuệ nhân tạo (AI) để nhận dạng ký tự quang học (OCR) cho chữ viết Tiếng Việt. Dự án bao gồm hai thành phần cốt lõi: Ứng dụng Web Frontend tương tác trực quan và Hệ thống Huấn luyện (Training System) tích hợp đám mây serverless **Modal GPU Cloud**.

---

## 🚀 Tính Năng Nổi Bật

- **Nhận dạng Tiếng Việt chuyên sâu**: Nhận dạng cực tốt các chữ in, chữ viết tay, ký tự đặc biệt có dấu tiếng Việt với độ chính xác cao.
- **Trải nghiệm kéo thả mượt mà (Drag-and-Drop)**: Tải ảnh tài liệu (PNG, JPG, JPEG) và file PDF với dung lượng hỗ trợ lên tới **50MB**.
- **Thời gian thực (Real-time Processing)**: Nhờ tích hợp hạ tầng điện toán đám mây **Modal Serverless GPU**, quá trình nhận diện diễn ra trong vài giây.
- **Hiển thị kết quả đa chiều**: Xem kết quả dưới 3 dạng trực quan:
  - **Văn bản**: Đoạn văn bản đầy đủ được định dạng liền mạch.
  - **Từng dòng**: Danh sách tách biệt chi tiết theo từng dòng được nhận dạng để đối chiếu.
  - **JSON**: Dữ liệu cấu trúc gốc từ API phục vụ mục đích tích hợp hệ thống khác.
- **Xử lý PDF**: Tích hợp PDF.js để xem trước và trích xuất text từ file PDF nhiều trang.
- **Xuất dữ liệu nhanh**: Sao chép nhanh vào bộ nhớ tạm hoặc tải xuống tệp `.txt` và `.json`.
- **Hệ thống huấn luyện mạnh mẽ trên GPU Cloud**: Tích hợp kịch bản huấn luyện, xuất mô hình tự động chạy trên GPU T4 của Modal.

---

## 🛠️ Công Nghệ Lõi và Kiến Trúc Hệ Thống

### 1. Frontend (Ứng dụng Client)
- **HTML5 & Vanilla CSS**: Thiết kế hiện đại, cao cấp với phong cách kính mờ (glassmorphism), bảng màu gradient sinh động, và hiệu ứng động vi mô (micro-animations).
- **Vanilla JavaScript** (`app.js`): Xử lý tương tác giao diện người dùng, kéo thả tệp, xem trước PDF, và kết nối API.

### 2. Backend & Training System (Modal.com GPU Cloud)
Hệ thống sử dụng hạ tầng Serverless của Modal để chạy huấn luyện và cung cấp dịch vụ OCR:
- **Chuẩn bị dữ liệu (`prepare_dataset`)**: Tự động tải bộ dữ liệu VinText từ Google Drive, cắt ảnh (cropping) đa luồng (16 threads), đóng gói và tải lên Volume lưu trữ `viet-ocr-vol`.
- **Huấn luyện mô hình (`run_train`)**: Chạy huấn luyện mô hình **PP-OCRv5-server** tiếng Việt trên GPU Nvidia T4.
- **Xuất mô hình (`run_export`)**: Chuyển đổi trọng số huấn luyện tốt nhất sang mô hình suy luận (Inference Model) hiệu năng cao.
- **Dịch vụ OCR (`OCRService`)**: API Webhook FastAPI lưu trữ mô hình trên bộ nhớ GPU, phục vụ nhận diện ảnh base64 thời gian thực.

---

## 💻 Hướng Dẫn Vận Hành Hệ Thống Huấn Luyện (Modal)

Cài đặt thư viện `modal` và cấu hình token xác thực trước khi chạy:

### Bước 1: Chuẩn bị dữ liệu và tải trọng số pretrained
```bash
python -m modal run modal_app.py::prepare_dataset
```

### Bước 2: Chạy chẩn đoán môi trường
```bash
python -m modal run modal_app.py::test_env
```

### Bước 3: Huấn luyện mô hình
```bash
# Kiểm thử nhanh (1 epoch)
python -m modal run modal_app.py::run_train --test-run True

# Huấn luyện chính thức
python -m modal run modal_app.py::run_train
```

### Bước 4: Xuất mô hình
```bash
python -m modal run modal_app.py::run_export
```

### Bước 5: Deploy dịch vụ OCR API
```bash
python -m modal deploy modal_app.py
```

---

## 📂 Cấu Trúc Tệp Tin

```
├── index.html          # Giao diện web chính
├── app.js              # Logic frontend & gọi API
├── styles.css          # Stylesheet (glassmorphism)
├── modal_app.py        # Backend: training & OCR API trên Modal
├── requirements.txt    # Python dependencies
├── train.sh            # Script huấn luyện PaddleOCR
├── LICENSE             # Giấy phép Apache 2.0
├── .nojekyll           # GitHub Pages config
└── README.md           # Tài liệu dự án
```

---

## 🌐 Truy Cập

- **Frontend**: https://yhresearcher.github.io/VOCR/
- **API Endpoint**: https://yhresearcher--vietocr-service-fastapi-app.modal.run/

---

## 📄 Giấy Phận

Dự án được phát hành theo Giấy phép Apache 2.0. Xem tệp [LICENSE](LICENSE) để biết thêm chi tiết.