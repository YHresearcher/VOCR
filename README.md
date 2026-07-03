# VietOCR Portal & Training System 🧠📝

**VietOCR Portal** là một cổng thông tin và công cụ trực tuyến hiện đại sử dụng trí tuệ nhân tạo (AI) để nhận dạng ký tự quang học (OCR) cho chữ viết Tiếng Việt. Dự án bao gồm hai thành phần cốt lõi: Ứng dụng Web Frontend tương tác trực quan và Hệ thống Huấn luyện (Training System) tích hợp đám mây serverless **Modal GPU Cloud**.

---

## 🚀 Tính Năng Nổi Bật

- **Nhận dạng Tiếng Việt chuyên sâu**: Nhận dạng cực tốt các chữ in, chữ viết tay, ký tự đặc biệt có dấu tiếng Việt với độ chính xác cao.
- **Trải nghiệm kéo thả mượt mà (Drag-and-Drop)**: Tải ảnh tài liệu (PNG, JPG, JPEG) với dung lượng hỗ trợ lên tới **10MB**.
- **Thời gian thực (Real-time Processing)**: Nhờ tích hợp hạ tầng điện toán đám mây **Modal Serverless GPU**, quá trình nhận diện diễn ra trong vài giây.
- **Hiển thị kết quả đa chiều**: Xem kết quả dưới 3 dạng trực quan:
  - **Văn bản**: Đoạn văn bản đầy đủ được định dạng liền mạch.
  - **Từng dòng**: Danh sách tách biệt chi tiết theo từng dòng được nhận dạng để đối chiếu.
  - **JSON**: Dữ liệu cấu trúc gốc từ API phục vụ mục đích tích hợp hệ thống khác.
- **Xuất dữ liệu nhanh**: Sao chép nhanh vào bộ nhớ tạm hoặc tải xuống tệp `.txt` và `.json`.
- **Hệ thống huấn luyện mạnh mẽ trên GPU Cloud**: Tích hợp kịch bản huấn luyện, xuất mô hình tự động chạy trên GPU của Modal.

---

## 🛠️ Công Nghệ Lõi và Kiến Trúc Hệ Thống

### 1. Frontend (Ứng dụng Client)
- **HTML5 & Vanilla CSS**: Thiết kế hiện đại, cao cấp với phong cách kính mờ (glassmorphism), bảng màu gradient sinh động, và hiệu ứng động vi mô (micro-animations).
- **Vanilla JavaScript** (tệp `app.js`): Xử lý tương tác giao diện người dùng, xử lý tệp kéo thả và kết nối API.

### 2. Backend & Training System (Modal.com GPU Cloud)
Hệ thống sử dụng hạ tầng Serverless của Modal để chạy huấn luyện và cung cấp dịch vụ OCR thông qua tệp [modal_app.py](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/modal_app.py):
- **Chuẩn bị dữ liệu (`prepare_dataset`)**: Tự động tải bộ dữ liệu VinText từ Google Drive, cắt ảnh (cropping) đa luồng (16 threads) tăng tốc gấp 10 lần, đóng gói và tải lên Volume lưu trữ `viet-ocr-vol`.
- **Huấn luyện mô hình (`run_train`)**: Chạy huấn luyện mô hình **PP-OCRv5-server** tiếng Việt trên GPU Nvidia T4 trong môi trường container tùy chỉnh tương thích CUDA 11.8.
- **Xuất mô hình (`run_export`)**: Chuyển đổi trọng số huấn luyện tốt nhất (`best_accuracy.pdparams`) sang mô hình suy luận (Inference Model) có hiệu năng cao.
- **Dịch vụ OCR (`OCRService`)**: Dịch vụ API Webhook (FastAPI) lưu trữ mô hình trực tiếp trên bộ nhớ GPU của container, phục vụ yêu cầu nhận diện ảnh base64 thời gian thực từ giao diện Frontend.

---

## 💻 Hướng Dẫn Vận Hành Hệ Thống Huấn Luyện (Modal)

Bạn cần cài đặt thư viện `modal` và cấu hình token xác thực trước khi chạy các lệnh sau:

### Bước 1: Chuẩn bị dữ liệu và tải trọng số pretrained
Tự động tải trọng số pretrained của PP-OCRv5 và chuẩn bị bộ dữ liệu VinText lên Volume:
```bash
python -m modal run modal_app.py::prepare_dataset
```

### Bước 2: Chạy chẩn đoán môi trường (Diagnostics)
Kiểm tra tính tương thích và sự trùng khớp của bộ ký tự nhãn trong tập dữ liệu với từ điển:
```bash
python -m modal run modal_app.py::test_env
```

### Bước 3: Huấn luyện mô hình (Training)
- **Chạy kiểm thử nhanh (1 epoch)**:
  ```bash
  python -m modal run modal_app.py::run_train --test-run True
  ```
- **Chạy huấn luyện chính thức (nhiều epochs)**:
  ```bash
  python -m modal run modal_app.py::run_train
  ```

### Bước 4: Xuất mô hình sang định dạng suy luận (Export)
```bash
python -m modal run modal_app.py::run_export
```

### Bước 5: Deploy dịch vụ OCR API Webhook
```bash
python -m modal deploy modal_app.py
```
Lệnh này sẽ tạo ra các địa chỉ API trực tuyến phục vụ cho ứng dụng giao diện web của bạn.

---

## 📂 Danh Sách Tệp Tin Cốt Lõi

- [index.html](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/index.html): Giao diện hiển thị chính của ứng dụng web.
- [app.js](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/app.js): Tập lệnh điều khiển giao diện frontend và gọi API.
- [styles.css](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/styles.css): Định nghĩa bố cục và hiệu ứng thị giác.
- [modal_app.py](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/modal_app.py): Toàn bộ kịch bản chuẩn bị, huấn luyện và API backend chạy trên Modal.
- [.nojekyll](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/.nojekyll): Tắt Jekyll phục vụ triển khai lên GitHub Pages.
- [README.md](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/README.md): Bản hướng dẫn chi tiết này.
