import os
import modal

app = modal.App("viet-ocr-server")

# Xây dựng môi trường container trên Modal.com (Cài đặt PaddleOCR, CUDA...)
ocr_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install(
        "paddlepaddle-gpu==2.6.0", # Cài đặt Paddle tương thích với T4/CUDA 12
        "paddleocr>=2.8.0",
        "imaug"
    )
)

# Khởi tạo Volume để lưu trữ dữ liệu huấn luyện và trọng số (Checkpoints)
vol = modal.Volume.from_name("viet-ocr-vol", create_if_missing=True)

# 1. Hàm huấn luyện: Thời gian timeout 24 giờ, chạy trên 1 GPU T4
@app.function(
    image=ocr_image,
    gpu="T4",
    timeout=86400, # 24 tiếng để training ko bị đứt quãng
    volumes={"/vol": vol}
)
def run_train():
    import subprocess
    print("Bắt đầu khởi chạy Job huấn luyện tiếng Việt (PP-OCRv5-server)...")
    
    # Mã nguồn sẽ gọi trực tiếp kịch bản train của PaddleOCR với file cấu hình đã tùy chỉnh
    cmd = [
        "python", "tools/train.py",
        "-c", "configs/rec/PP-OCRv5/multi_language/rec_vi_server.yml",
        # Có thể ghi đè biến môi trường để lưu kết quả trực tiếp lên Modal Volume
        "-o", "Global.save_model_dir=/vol/output/vi_PP-OCRv5_server_rec"
    ]
    
    # Chạy mô phỏng 1 epoch cho mục đích kiểm thử nếu chưa có dữ liệu
    # cmd.extend(["Global.epoch_num=1", "Train.loader.num_workers=0"])
    
    try:
        subprocess.run(cmd, check=True)
        print("Huấn luyện hoàn tất và đã lưu trọng số.")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi trong quá trình huấn luyện: {e}")

# 2. Hàm Webhook (API): Scale về 0 khi không nhận tải, siêu tiết kiệm chi phí
@app.function(
    image=ocr_image,
    gpu="T4",
    min_containers=0, # Rất quan trọng cho gói miễn phí (Scale-to-zero)
    volumes={"/vol": vol}
)
@modal.fastapi_endpoint(method="POST")
def ocr_webhook(item: dict):
    from paddleocr import PaddleOCR
    import base64
    import numpy as np
    import cv2
    
    # Khởi tạo OCR với mô hình tiếng Việt. 
    # Lưu ý: Khi fine-tune xong, cần thay đổi "rec_model_dir" thành đường dẫn tới checkpoint trong /vol
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="vi",
        use_gpu=True
    )
    
    if "image_b64" not in item:
        return {"error": "Missing 'image_b64' field"}
        
    try:
        # Giải mã ảnh base64
        img_data = base64.b64decode(item["image_b64"])
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "Failed to decode image from base64"}
            
        # Chạy dự đoán
        result = ocr.ocr(img, cls=True)
        
        # Bóc tách text và tọa độ
        extracted_text = []
        if result and result[0]:
            for line in result[0]:
                extracted_text.append(line[1][0])
                
        return {
            "status": "success",
            "text": "\n".join(extracted_text),
            "raw_result": result
        }
    except Exception as e:
        return {"error": str(e)}
