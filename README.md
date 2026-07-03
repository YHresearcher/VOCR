# VietOCR Portal 🧠📝

**VietOCR Portal** là một cổng thông tin và công cụ trực tuyến hiện đại sử dụng trí tuệ nhân tạo (AI) để nhận dạng ký tự quang học (OCR) cho chữ viết Tiếng Việt. Dự án hướng tới trải nghiệm người dùng tối ưu, xử lý nhanh chóng và chính xác các tài liệu, hình ảnh, chữ viết tay tiếng Việt trực tiếp trên nền tảng web.

---

## 🚀 Tính Năng Nổi Bật

- **Nhận dạng Tiếng Việt chuyên sâu**: Nhận dạng cực tốt các chữ in, chữ viết tay, ký tự đặc biệt có dấu tiếng Việt với độ chính xác cao.
- **Trải nghiệm kéo thả mượt mà (Drag-and-Drop)**: Tải ảnh tài liệu (PNG, JPG, JPEG) với dung lượng hỗ trợ lên tới **10MB**.
- **Thời gian thực (Real-time Processing)**: Nhờ tích hợp hạ tầng điện toán đám mây **Modal Serverless GPU**, quá trình nhận diện diễn ra trong vài giây.
- **Hiển thị đa chiều**: Xem kết quả dưới 3 dạng trực quan:
  - **Văn bản**: Đoạn văn bản đầy đủ được định dạng liền mạch.
  - **Từng dòng**: Danh sách tách biệt chi tiết theo từng dòng được nhận dạng để đối chiếu.
  - **JSON**: Dữ liệu cấu trúc gốc từ API phục vụ mục đích tích hợp hệ thống khác.
- **Tiện ích xuất dữ liệu nhanh**: 
  - Sao chép nhanh văn bản vào bộ nhớ tạm (Clipboard).
  - Tải xuống kết quả dưới dạng tệp văn bản thô `.txt`.
  - Tải xuống dữ liệu cấu trúc dưới dạng tệp `.json`.
- **Giám sát Trạng thái API**: Hiển thị trạng thái kết nối trực tiếp đến Modal API Server ở góc trên cùng giao diện để người dùng luôn nắm bắt được độ khả dụng của hệ thống.

---

## 🛠️ Công Nghệ Lõi và Kiến Trúc Hệ Thống

Dự án được phân tách rõ ràng thành hai phần chính:

### 1. Frontend (Ứng dụng Client)
- **HTML5 & Vanilla CSS**: Được viết tay tỉ mỉ với thiết kế hiện đại, cao cấp, sử dụng bảng màu gradient sinh động, phong cách kính mờ (glassmorphism), và các hiệu ứng động vi mô (micro-animations) tinh tế.
- **Vanilla JavaScript**: Xử lý toàn bộ các tác vụ tương tác DOM, quản lý thẻ tab, xử lý kéo thả tệp tin, xuất tải file và gửi yêu cầu không đồng bộ (Fetch API) tới máy chủ.

### 2. Backend (Modal GPU Serverless API)
- Sử dụng mô hình **EasyOCR** kết hợp thuật toán tối ưu để phát hiện (Detection) và bao khung vùng chữ.
- Sử dụng mô hình **VietOCR** chuyên biệt để nhận dạng (Recognition) văn bản tiếng Việt có dấu và chữ viết tay phức tạp.
- Triển khai serverless chạy trực tiếp trên GPU cloud Modal giúp tối ưu chi phí và tăng tốc hiệu năng.

---

## 💻 Hướng Dẫn Sử Dụng Cục Bộ (Local Setup)

Để chạy thử nghiệm giao diện VietOCR Portal trên máy tính cá nhân của bạn:

1. **Chuẩn bị**: Cần có trình duyệt web hiện đại (Chrome, Edge, Firefox, Safari...).
2. **Khởi chạy**:
   - Bạn có thể mở trực tiếp tệp [index.html](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/index.html) bằng trình duyệt của mình.
   - Hoặc khởi chạy một web server đơn giản (ví dụ dùng Python):
     ```bash
     python -m http.server 8000
     ```
     Sau đó truy cập địa chỉ: `http://localhost:8000/index.html` trên trình duyệt.
3. **Thực hiện nhận diện**: Tải một hình ảnh có chứa văn bản Tiếng Việt lên góc bên trái, click nút **Nhận dạng chữ (OCR)** và đợi kết quả hiển thị ở khu vực bên phải.

---

## 📂 Danh Sách Tệp Tin Cốt Lõi

Kho lưu trữ đã được tinh giản tối đa để chỉ chứa các tài tệp tin thực sự phục vụ vận hành:
- [index.html](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/index.html): Giao diện hiển thị chính của ứng dụng.
- [app.js](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/app.js): Tập lệnh điều khiển tương tác logic và gửi API.
- [styles.css](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/styles.css): Định nghĩa toàn bộ màu sắc, bố cục, hiệu ứng thị giác.
- [.nojekyll](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/.nojekyll): Cấu hình tắt cơ chế biên dịch Jekyll khi triển khai trên GitHub Pages.
- [README.md](file:///c:/Users/pntha/OneDrive/Documents/Antigravity/TheVOCR/VietOCR/README.md): Bản hướng dẫn giới thiệu này.

---

## 📄 Giấy Phép (License)

Dự án này được phát triển độc lập cho các mục đích nghiên cứu, học tập và phục vụ cộng đồng Việt Nam. Bản quyền mã nguồn giao diện thuộc về **VietOCR Portal**.
