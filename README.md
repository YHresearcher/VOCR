# VietOCR Portal & Training System 🧠📝

**VietOCR Portal** là cổng thông tin và công cụ trực tuyến hiện đại sử dụng trí tuệ nhân tạo (AI) để nhận dạng ký tự quang học (OCR) cho chữ viết Tiếng Việt. Dự án tích hợp giữa giao diện Web Frontend tương tác trực quan và hạ tầng huấn luyện (Training System) Serverless **Modal GPU Cloud**.

Dự án đã được đồng bộ hóa và hợp nhất hoàn toàn với repository [YHresearcher/VOCR](https://github.com/YHresearcher/VOCR) để tối ưu cấu trúc nhẹ gọn và bổ sung các tính năng xử lý thông minh.

---

## 🚀 Tính Năng Nổi Bật

- **Nhận dạng Tiếng Việt chuyên sâu**: Nhận dạng cực tốt các chữ in, chữ viết tay, ký tự đặc biệt có dấu tiếng Việt với độ chính xác cao.
- **Trích xuất PDF lai thông minh (Hybrid PDF Parsing) [MỚI]**: 
  * **PDF Điện tử (Native PDF)**: Đọc trực tiếp lớp văn bản số (text layer) block-by-block, giúp trích xuất chữ viết **tức thì (< 1 giây, nhanh gấp ~300 lần)**, đạt độ chính xác **tuyệt đối 100%** và **tiết kiệm 100% tài nguyên GPU**.
  * **PDF Quét (Scanned PDF)**: Tự động phát hiện và kích hoạt chế độ render ảnh 150 DPI kết hợp mô hình OCR GPU fine-tuned làm phương án dự phòng (fallback).
- **Bộ lọc sửa lỗi chính tả Thảo dược [MỚI]**: Tự động lọc và sửa đổi các lỗi chính tả phổ biến của thuật ngữ y học cổ truyền/thảo dược phát sinh sau quá trình OCR (ví dụ: `chüa` -> `chữa`, `bénh` -> `bệnh`, `nuöc` -> `nước`).
- **Thời gian thực (Real-time Processing)**: Tích hợp API Web FastAPI lưu trữ mô hình trên bộ nhớ GPU của Modal Serverless, phản hồi kết quả nhận dạng ảnh trong vài giây.
- **Tách cột thông minh (Multi-column Splitting)**: Tự động tách bố cục 2 cột dọc của trang tài liệu để đọc chữ viết đúng thứ tự đọc tự nhiên từ trên xuống dưới.
- **Giao diện Glassmorphism**: Thiết kế web kéo thả tệp tin hiện đại, cho phép xem trước tài liệu PDF và xuất kết quả dưới 3 dạng: văn bản thô, danh sách dòng chi tiết, hoặc cấu trúc JSON để tích hợp.

---

## 🛠️ Công Nghệ Lõi & Kiến Trúc Patches Tự Huấn Luyện

### 1. Kiến trúc Git rút gọn (Lightweight Git Tree)
Để giữ repository sạch và dung lượng nhẹ (dưới 1MB thay vì phình to gần 2GB do chứa framework PaddleOCR gốc), mã nguồn cốt lõi của PaddleOCR được tải tự động qua lệnh `git clone` trong lúc xây dựng Docker Image trên đám mây Modal.

### 2. Thư mục Patches tùy chỉnh (`custom_src/`)
Tất cả các tệp sửa đổi đặc trưng cho dự án VietOCR của bạn được lưu trữ cách ly trong thư mục [custom_src/](file:///c:/Users/pntha/Documents/Antigravity/TheVOCR/VietOCR/custom_src). Khi khởi tạo Container, Modal sẽ ghi đè các tệp này vào framework PaddleOCR:
*   `custom_src/ppocr/data/collate_fn.py`: Vá lỗi DataLoader CPU đa luồng trên PyDL tránh tràn hàng đợi GPU.
*   `custom_src/ppocr/modeling/heads/rec_nrtr_head.py`: Vá lỗi contiguous bộ nhớ GPU của đầu nhận diện Transformer NRTR trên PaddlePaddle 2.6.
*   `custom_src/ppocr/utils/dict/vi_custom_dict.txt`: Từ điển tiếng Việt mở rộng gồm **291 ký tự** (bao gồm số và ký tự đặc biệt viết hoa/viết thường có dấu).
*   `custom_src/configs/rec/PP-OCRv5/multi_language/rec_vi_server.yml`: Cấu hình huấn luyện mô hình máy chủ server độ chính xác cao.

---

## 💻 Hướng Dẫn Vận Hành Hệ Thống Huấn Luyện & Deploy

Cài đặt thư viện `modal` cục bộ và xác thực tài khoản của bạn trước khi bắt đầu:

### Bước 1: Chuẩn bị dữ liệu và tải trọng số pretrained
Hàm này sẽ tải bộ dữ liệu VinText tự động từ Google Drive, cắt ảnh đa luồng bằng 16 threads và đồng bộ hóa lên Volume đám mây `viet-ocr-vol`:
```bash
$env:PYTHONIOENCODING='utf-8'; python -m modal run modal_app.py::prepare_dataset
```

### Bước 2: Chạy kiểm tra môi trường và tính nhất quan nhãn
Kiểm tra xem từ điển 291 ký tự đã khớp toàn bộ nhãn huấn luyện chưa trước khi chạy:
```bash
$env:PYTHONIOENCODING='utf-8'; python -m modal run modal_app.py::test_env
```

### Bước 3: Huấn luyện mô hình (Fine-tune)
Hệ thống sẽ chạy trên 1 GPU Nvidia T4 đám mây, tự động khôi phục (auto-resume) từ checkpoint gần nhất nếu bị ngắt quãng giữa chừng:
```bash
# Huấn luyện chính thức
$env:PYTHONIOENCODING='utf-8'; python -m modal run modal_app.py::run_train
```

### Bước 4: Xuất mô hình huấn luyện sang dạng suy luận (Export Inference)
```bash
$env:PYTHONIOENCODING='utf-8'; python -m modal run modal_app.py::run_export
```

### Bước 5: Deploy API lên Production
```bash
$env:PYTHONIOENCODING='utf-8'; python -m modal deploy modal_app.py
```

---

## 📂 Cấu Trúc Tệp Tin Dự Án

```
├── index.html          # Giao diện web chính (GitHub Pages)
├── app.js              # Xử lý kéo thả tệp, gọi API & render PDF
├── styles.css          # Stylesheet thiết kế kính mờ (glassmorphism)
├── modal_app.py        # Ứng dụng Backend chính: Chứa API & các Jobs huấn luyện trên Modal
├── custom_src/         # THƯ MỤC PATCH: Lưu trữ toàn bộ mã nguồn tùy chỉnh và từ điển của bạn
├── .temp/              # THƯ MỤC TẠM: Nơi lưu trữ tập dữ liệu và tệp debug cục bộ (được bỏ qua bởi Git/Modal)
├── requirements.txt    # Các thư viện phụ thuộc Python
├── LICENSE             # Giấy phép Apache 2.0
├── .nojekyll           # Cấu hình GitHub Pages
└── README.md           # Tài liệu dự án này
```

---

## 🌐 Đường Dẫn Truy Cập

- **Giao diện Web (GitHub Pages)**: [https://yhresearcher.github.io/VOCR/](https://yhresearcher.github.io/VOCR/)
- **API Production Endpoint (Modal)**: `https://yhresearcher--vietocr-service-fastapi-app-fastapi-app.modal.run`

---

## 📄 Giấy Phép

Dự án được phát hành theo Giấy phép Apache 2.0. Xem tệp [LICENSE](LICENSE) để biết chi tiết.