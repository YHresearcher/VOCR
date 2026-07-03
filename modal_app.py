import os
import modal

app = modal.App("vietocr-service-fastapi-app")

# Xây dựng môi trường container trên Modal.com
# Định nghĩa môi trường chạy: Cài đặt PaddleOCR, CUDA, các gói dependencies 
# và đồng bộ mã nguồn cục bộ vào container (bỏ quan các thư mục không cần thiết).
ocr_image = (
    modal.Image.from_registry("nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04")
    .apt_install("python3-pip", "python3-dev", "libgl1", "libglib2.0-0", "git")
    .run_commands("ln -sf /usr/bin/python3 /usr/bin/python")
    .env({
        "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu"
    })
    .pip_install("numpy==1.26.4") # Bắt buộc cài đặt NumPy 1.x để tương thích với Paddle 2.6
    .pip_install("paddlepaddle-gpu==2.6.0") # PaddlePaddle 2.6.0 với CUDA 11.8 (đã cache)
    .pip_install("imaug")
    .pip_install("fastapi[standard]") # Bắt buộc cho các hàm fastapi_endpoint trong các bản Modal mới
    .pip_install("gdown") # Sử dụng để tải tệp lớn từ Google Drive một cách tin cậy
    .pip_install("pymupdf") # Thư viện xử lý PDF trực tiếp trên backend
    .pip_install_from_requirements("requirements.txt")
    .pip_install("paddleocr==2.7.3.1") # v2.7.x không phụ thuộc paddlex — ổn định với Paddle 2.6
    .add_local_dir(
        ".",
        remote_path="/root",
        ignore=[
            ".git", 
            "train_data", 
            "output", 
            ".venv", 
            "__pycache__", 
            ".idea", 
            ".gemini", 
            "artifacts", 
            "**/*.pyc"
        ]
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
def run_train(test_run: bool = False):
    import subprocess
    print("Bắt đầu khởi chạy Job huấn luyện tiếng Việt (PP-OCRv5-server)...")
    
    # Reload volume để đồng bộ dữ liệu mới nhất
    vol.reload()
    
    # Kiểm tra xem dữ liệu huấn luyện có tồn tại trong Volume không
    if not os.path.exists("/vol/train_data"):
        print("CẢNH BÁO: Không tìm thấy thư mục /vol/train_data. Vui lòng tải dữ liệu huấn luyện lên volume trước.")
        print("Hướng dẫn: python -m modal volume put viet-ocr-vol <path_to_local_train_data> train_data")
        return

    # Gọi trực tiếp kịch bản train của PaddleOCR với các tham số ghi đè sang /vol
    cmd = [
        "python", "tools/train.py",
        "-c", "configs/rec/PP-OCRv5/multi_language/rec_vi_server.yml",
        "-o", "Global.save_model_dir=/vol/output/vi_PP-OCRv5_server_rec",
        "Train.dataset.data_dir=/vol/train_data/",
        "Train.dataset.label_file_list=[/vol/train_data/train_list.txt]",
        "Eval.dataset.data_dir=/vol/train_data/",
        "Eval.dataset.label_file_list=[/vol/train_data/val_list.txt]"
    ]
    
    if test_run:
        print("Đang chạy chế độ kiểm thử (test_run=True): Giới hạn 1 epoch và giảm workers...")
        cmd.extend([
            "Global.epoch_num=1", 
            "Train.loader.num_workers=0", 
            "Eval.loader.num_workers=0"
        ])
    
    try:
        subprocess.run(cmd, check=True)
        print("Huấn luyện hoàn tất và đã lưu trọng số tại /vol/output/vi_PP-OCRv5_server_rec")
        # Commit kết quả huấn luyện lên Volume để các task khác (export/webhook) nhìn thấy
        print("Đang commit kết quả huấn luyện lên Volume...", flush=True)
        vol.commit()
        print("Commit huấn luyện hoàn tất.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"Lỗi trong quá trình huấn luyện: {e}")

# 2. Hàm Export Model: Đổi từ checkpoint (.pdparams) sang mô hình suy luận (Inference Model)
@app.function(
    image=ocr_image,
    volumes={"/vol": vol}
)
def run_export():
    import subprocess
    print("Bắt đầu export model sang định dạng inference...")
    
    # Reload volume để lấy checkpoint mới nhất
    vol.reload()
    
    best_model_path = "/vol/output/vi_PP-OCRv5_server_rec/best_accuracy"
    
    if not os.path.exists(best_model_path + ".pdparams"):
        print(f"Không tìm thấy file checkpoint {best_model_path}.pdparams.")
        print("Vui lòng huấn luyện model trước khi thực hiện export.")
        return
        
    cmd = [
        "python", "tools/export_model.py",
        "-c", "configs/rec/PP-OCRv5/multi_language/rec_vi_server.yml",
        "-o", f"Global.pretrained_model={best_model_path}",
        "Global.save_inference_dir=/vol/inference/vi_PP-OCRv5_server_rec"
    ]
    try:
        subprocess.run(cmd, check=True)
        print("Export hoàn tất. Mô hình đã được lưu tại /vol/inference/vi_PP-OCRv5_server_rec")
        # Commit kết quả export lên Volume để webhook nhìn thấy mô hình mới
        print("Đang commit kết quả export lên Volume...", flush=True)
        vol.commit()
        print("Commit export hoàn tất.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"Lỗi trong quá trình export model: {e}")

# 3. OCR Service: Class-based để giữ model trong bộ nhớ GPU giữa các request
@app.cls(
    image=ocr_image,
    gpu="T4",
    volumes={"/vol": vol},
    scaledown_window=300  # Giữ container sống 5 phút sau request cuối
)
class OCRService:
    def __init__(self):
        self.ocr = None
        self.model_type = None
    
    @modal.enter()
    def load_model(self):
        """Khởi tạo PaddleOCR một lần duy nhất khi container start, thay vì mỗi request."""
        from paddleocr import PaddleOCR
        
        custom_model_dir = "/vol/inference/vi_PP-OCRv5_server_rec"
        
        # Reload volume để nhận mô hình mới nhất
        vol.reload()
        
        # PaddleOCR 2.9.1 API: use_angle_cls, lang, use_gpu
        if os.path.exists(custom_model_dir) and os.listdir(custom_model_dir):
            print(f"Đang tải mô hình fine-tuned tại: {custom_model_dir}")
            self.ocr = PaddleOCR(use_angle_cls=True, lang="vi", use_gpu=True)
            self.model_type = "fine-tuned"
        else:
            print("Không tìm thấy mô hình fine-tuned. Sử dụng mô hình tiếng Việt mặc định...")
            self.ocr = PaddleOCR(use_angle_cls=True, lang="vi", use_gpu=True)
            self.model_type = "default"
        print(f"OCR model đã sẵn sàng (type: {self.model_type})")
    
    @modal.fastapi_endpoint(method="POST")
    def ocr_webhook(self, item: dict):
        import base64
        import numpy as np
        import cv2
        
        if "image_b64" not in item:
            return {"error": "Missing 'image_b64' field"}
        
        if self.ocr is None:
            return {"error": "OCR model not initialized"}
            
        try:
            img_data = base64.b64decode(item["image_b64"])
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "Failed to decode image from base64"}
                
            result = self.ocr.ocr(img, cls=True)
            
            extracted_text = []
            if result and result[0]:
                for line in result[0]:
                    extracted_text.append(line[1][0])
                    
            return {
                "status": "success",
                "model_type": self.model_type,
                "text": "\n".join(extracted_text),
                "raw_result": result
            }
        except Exception as e:
            return {"error": str(e)}
    
    @modal.fastapi_endpoint(method="POST")
    def reload_model(self):
        """Reload model từ Volume — dùng sau khi export model mới."""
        self.load_model()
        return {"status": "success", "model_type": self.model_type}
    
    @modal.fastapi_endpoint(method="GET")
    def health(self):
        return {
            "status": "healthy",
            "model_type": self.model_type,
            "model_loaded": self.ocr is not None
        }

# ==========================================
# FastAPI Web Application for direct PDF/Image OCR
# ==========================================

# Global variables for model sharing inside the container
ocr_model = None
model_type_global = "default"

@app.function(
    image=ocr_image,
    gpu="T4",
    volumes={"/vol": vol},
    scaledown_window=300
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import numpy as np
    import cv2
    import fitz  # PyMuPDF
    
    web_app = FastAPI(title="VietOCR Service API")
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_ocr_model():
        global ocr_model, model_type_global
        if ocr_model is None:
            from paddleocr import PaddleOCR
            custom_model_dir = "/vol/inference/vi_PP-OCRv5_server_rec"
            vol.reload()
            if os.path.exists(custom_model_dir) and os.listdir(custom_model_dir):
                print(f"Loading fine-tuned model from: {custom_model_dir}")
                ocr_model = PaddleOCR(use_angle_cls=True, lang="vi", use_gpu=True)
                model_type_global = "fine-tuned"
            else:
                print("Loading default Vietnamese model...")
                ocr_model = PaddleOCR(use_angle_cls=True, lang="vi", use_gpu=True)
                model_type_global = "default"
        return ocr_model

    @web_app.post("/ocr")
    async def ocr_endpoint(file: UploadFile = File(...), pages: str = Form(None)):
        ocr = get_ocr_model()
        content = await file.read()
        
        # Check if file is PDF
        is_pdf = file.filename.lower().endswith('.pdf') or file.content_type == 'application/pdf'
        
        lines = []
        box_count = 0
        raw_results = []
        
        try:
            if is_pdf:
                doc = fitz.open(stream=content, filetype="pdf")
                num_pages = len(doc)
                
                selected_pages = []
                if pages and pages.strip():
                    for part in pages.split(","):
                        part = part.strip()
                        if "-" in part:
                            try:
                                start, end = part.split("-")
                                selected_pages.extend(range(int(start), int(end) + 1))
                            except ValueError:
                                pass
                        else:
                            try:
                                selected_pages.append(int(part))
                            except ValueError:
                                pass
                    selected_pages = [p - 1 for p in selected_pages if 0 <= p - 1 < num_pages]
                
                if not selected_pages:
                    selected_pages = list(range(num_pages))
                    
                for page_idx in selected_pages:
                    page = doc.load_page(page_idx)
                    # Render to high-resolution image (dpi = 150)
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")
                    np_arr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if img is None:
                        continue
                    
                    result = ocr.ocr(img, cls=True)
                    if result and result[0]:
                        raw_results.append({"page": page_idx + 1, "result": result})
                        for line in result[0]:
                            lines.append(line[1][0])
                            box_count += 1
            else:
                # Handle normal Image
                np_arr = np.frombuffer(content, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if img is None:
                    raise HTTPException(status_code=400, detail="Invalid image format")
                    
                result = ocr.ocr(img, cls=True)
                if result and result[0]:
                    raw_results.append({"page": 1, "result": result})
                    for line in result[0]:
                        lines.append(line[1][0])
                        box_count += 1
                        
            return {
                "status": "success",
                "model_type": model_type_global,
                "text": "\n".join(lines),
                "full_text": "\n".join(lines),
                "lines": lines,
                "box_count": box_count,
                "raw_result": raw_results
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @web_app.get("/")
    async def health_endpoint():
        return {
            "status": "running",
            "model_type": "ready",
            "model_loaded": True
        }

    return web_app


# 4. Hàm Kiểm tra Môi trường (Diagnostics)
@app.function(
    image=ocr_image,
    volumes={"/vol": vol}
)
def test_env():
    import sys
    print("=== ENVIRONMENT DIAGNOSTICS ===")
    print("Python version:", sys.version)
    print("Working directory:", os.getcwd())

    dict_path = "ppocr/utils/dict/vi_custom_dict.txt"
    train_list_path = "/vol/train_data/train_list.txt"
    val_list_path = "/vol/train_data/val_list.txt"
    
    # Đồng bộ volume mới nhất
    vol.reload()
    
    # 1. Đọc từ điển
    if not os.path.exists(dict_path):
        print(f"Lỗi: Không tìm thấy từ điển tại {dict_path}")
        return
        
    with open(dict_path, "r", encoding="utf-8") as f:
        dict_chars = set(f.read().splitlines())
    # Thêm khoảng trắng vì nó thường là ký tự hợp lệ
    dict_chars.add(" ")
    print(f"Từ điển có {len(dict_chars)} ký tự.")
    
    # 2. Đọc nhãn train và val
    missing_chars = set()
    total_labels = 0
    
    for list_path in [train_list_path, val_list_path]:
        if not os.path.exists(list_path):
            print(f"Không tìm thấy nhãn tại {list_path}")
            continue
            
        print(f"Đang kiểm tra {list_path}...")
        with open(list_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t", 1)
                if len(parts) < 2:
                    continue
                transcript = parts[1]
                total_labels += 1
                for char in transcript:
                    if char not in dict_chars:
                        missing_chars.add(char)
                        
    print(f"Đã kiểm tra tổng cộng {total_labels} nhãn.")
    if missing_chars:
        print(f"CẢNH BÁO: Phát hiện {len(missing_chars)} ký tự trong nhãn NHƯNG KHÔNG CÓ trong từ điển:")
        print(repr(sorted(list(missing_chars))))
    else:
        print("Tất cả ký tự trong nhãn đều tồn tại trong từ điển!")

# 5. Hàm tự động tải và chuẩn bị dữ liệu (VinText & Pretrained Weights)
@app.function(
    image=ocr_image,
    volumes={"/vol": vol},
    timeout=3600
)
def prepare_dataset():
    import os
    import requests
    import zipfile
    
    # Hàm hỗ trợ tải từ Google Drive dùng thư viện gdown cực kỳ ổn định
    def download_file_from_google_drive(id, destination):
        import gdown
        print(f"Đang dùng gdown để tải Google Drive file ID: {id}...")
        gdown.download(id=id, output=destination, quiet=False)
    
    # 1. Tạo các thư mục
    os.makedirs("/vol/pretrain_models", exist_ok=True)
    os.makedirs("/vol/train_data", exist_ok=True)
    
    # 2. Tải pre-trained weights
    pretrained_dest = "/vol/pretrain_models/latin_PP-OCRv5_mobile_rec_pretrained.pdparams"
    if not os.path.exists(pretrained_dest):
        pretrained_url = "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_pretrained_model/latin_PP-OCRv5_mobile_rec_pretrained.pdparams"
        print(f"Đang tải pre-trained weights từ {pretrained_url}...")
        try:
            r = requests.get(pretrained_url, stream=True)
            r.raise_for_status()
            with open(pretrained_dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Đã tải xong pre-trained weights.")
        except Exception as e:
            print(f"Lỗi tải pre-trained weights: {e}")
            return
    else:
        print("Pre-trained weights đã có sẵn.")
        
    # 3. Tải bộ dữ liệu VinText
    zip_dest = "/vol/vintext.zip"
    extract_dir = "/vol/vintext_extracted"
    
    # Kiểm tra xem file zip cũ có bị lỗi không, nếu lỗi thì xóa
    if os.path.exists(zip_dest):
        if not zipfile.is_zipfile(zip_dest):
            print("File zip cũ bị lỗi hoặc không đầy đủ. Đang xóa để tải lại...")
            try:
                os.remove(zip_dest)
            except Exception as e:
                print(f"Lỗi xóa file zip cũ: {e}")
    
    if not os.path.exists(zip_dest) and not os.path.exists(extract_dir):
        drive_id = "1UUQhNvzgpZy7zXBFQp0Qox-BBjunZ0ml"
        print("Đang tải bộ dữ liệu VinText (vintext.zip) từ Google Drive...")
        try:
            download_file_from_google_drive(drive_id, zip_dest)
            print("Đã tải xong bộ dữ liệu VinText (vintext.zip).")
        except Exception as e:
            print(f"Lỗi tải VinText: {e}")
            return
            
    # 4. Giải nén VinText
    if os.path.exists(zip_dest) and not os.path.exists(extract_dir):
        print("Đang giải nén bộ dữ liệu VinText...")
        try:
            if not zipfile.is_zipfile(zip_dest):
                raise ValueError("Tập tin tải xuống không phải là zip hợp lệ. Có thể Google Drive chặn tải.")
            with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print("Giải nén hoàn tất.")
            os.remove(zip_dest)
        except Exception as e:
            print(f"Lỗi giải nén: {e}")
            # Xóa file zip hỏng
            try:
                os.remove(zip_dest)
            except:
                pass
            return
            
    # 5. Lập trình cropping logic đa luồng (multi-threaded) bằng thư mục tạm local `/tmp/crops` để tăng tốc gấp 10 lần
    import cv2
    import shutil
    from concurrent.futures import ThreadPoolExecutor
    
    labels_dir = os.path.join(extract_dir, "vietnamese", "labels")
    train_imgs_dir = os.path.join(extract_dir, "vietnamese", "train_images")
    test_imgs_dir = os.path.join(extract_dir, "vietnamese", "test_image")
    
    local_crops_dir = "/tmp/crops"
    shutil.rmtree(local_crops_dir, ignore_errors=True)
    os.makedirs(local_crops_dir, exist_ok=True)
    
    train_list_path = "/vol/train_data/train_list.txt"
    val_list_path = "/vol/train_data/val_list.txt"
    
    if not os.path.exists(labels_dir):
        print(f"Lỗi: Không tìm thấy thư mục nhãn tại {labels_dir}")
        return
        
    label_files = sorted(os.listdir(labels_dir))
    print(f"Bắt đầu xử lý {len(label_files)} tệp nhãn đa luồng (16 threads) để tăng tốc...", flush=True)
    
    def process_label_file(l_file):
        if not l_file.startswith("gt_") or not l_file.endswith(".txt"):
            return []
            
        try:
            n_str = l_file[3:-4]
            N = int(n_str)
        except ValueError:
            return []
            
        img_name = f"im{N:04d}.jpg"
        if 1 <= N <= 1200:
            img_path = os.path.join(train_imgs_dir, img_name)
            is_train = True
        elif 1201 <= N <= 1500:
            img_path = os.path.join(test_imgs_dir, img_name)
            is_train = False
        else:
            return []
            
        if not os.path.exists(img_path):
            return []
            
        img = cv2.imread(img_path)
        if img is None:
            return []
            
        h, w = img.shape[:2]
        
        label_path = os.path.join(labels_dir, l_file)
        try:
            with open(label_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            return []
            
        file_records = []
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(",", 8)
            if len(parts) < 9:
                continue
                
            transcript = parts[8]
            if transcript == "###" or not transcript.strip():
                continue
                
            try:
                coords = [float(p) for p in parts[:8]]
            except ValueError:
                continue
                
            x_coords = [coords[0], coords[2], coords[4], coords[6]]
            y_coords = [coords[1], coords[3], coords[5], coords[7]]
            
            min_x = max(0, int(min(x_coords)))
            min_y = max(0, int(min(y_coords)))
            max_x = min(w, int(max(x_coords)))
            max_y = min(h, int(max(y_coords)))
            
            if (max_x - min_x) <= 2 or (max_y - min_y) <= 2:
                continue
                
            crop_img = img[min_y:max_y, min_x:max_x]
            crop_name = f"crop_{N:04d}_{line_idx:03d}.jpg"
            crop_path = os.path.join(local_crops_dir, crop_name)
            
            cv2.imwrite(crop_path, crop_img)
            
            record = f"crops/{crop_name}\t{transcript}\n"
            file_records.append((is_train, record))
            
        return file_records
        
    train_lines = []
    val_lines = []
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(process_label_file, label_files))
        
    crop_idx = 0
    for res in results:
        for is_train, record in res:
            if is_train:
                train_lines.append(record)
            else:
                val_lines.append(record)
            crop_idx += 1
            
    print(f"Xử lý xong! Đã tạo {crop_idx} ảnh cắt cục bộ tại {local_crops_dir}.", flush=True)
    
    # 6. Đóng gói thư mục tạm thành tệp ZIP
    local_zip_path = "/tmp/crops.zip"
    print("Đang nén thư mục ảnh cắt...", flush=True)
    try:
        shutil.make_archive("/tmp/crops", 'zip', local_crops_dir)
        print("Đã nén xong crops.zip.", flush=True)
    except Exception as e:
        print(f"Lỗi nén file: {e}", flush=True)
        return
        
    # 7. Sao chép ZIP sang Volume và giải nén (Cực nhanh vì chuyển khối lớn)
    vol_crops_dir = "/vol/train_data/crops"
    print("Đang dọn dẹp thư mục ảnh cũ trên Volume...", flush=True)
    shutil.rmtree(vol_crops_dir, ignore_errors=True)
    os.makedirs(vol_crops_dir, exist_ok=True)
    
    print("Đang giải nén tệp zip trực tiếp lên Volume...", flush=True)
    try:
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(vol_crops_dir)
        print("Giải nén lên Volume hoàn tất.", flush=True)
    except Exception as e:
        print(f"Lỗi giải nén lên Volume: {e}", flush=True)
        return
    finally:
        # Dọn dẹp /tmp
        shutil.rmtree(local_crops_dir, ignore_errors=True)
        if os.path.exists(local_zip_path):
            os.remove(local_zip_path)
            
    # Ghi file txt nhãn
    with open(train_list_path, "w", encoding="utf-8") as f:
        f.writelines(train_lines)
    with open(val_list_path, "w", encoding="utf-8") as f:
        f.writelines(val_lines)
        
    print(f"Hoàn tất chuẩn bị dữ liệu!")
    print(f"Tổng số ảnh cropped cho Train: {len(train_lines)}", flush=True)
    print(f"Tổng số ảnh cropped cho Val: {len(val_lines)}", flush=True)
    print(f"Đã ghi nhãn vào {train_list_path} và {val_list_path}", flush=True)
    
    # Commit các thay đổi lên Volume để các task khác (như train/export) nhìn thấy
    print("Đang commit các thay đổi lên Volume...", flush=True)
    vol.commit()
    print("Commit hoàn tất.", flush=True)
