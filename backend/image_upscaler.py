import os
import cv2
import numpy as np
import urllib.request

MODEL_URL = "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x4.pb"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "FSRCNN_x4.pb")

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Đang tải AI Upscale model (FSRCNN) lần đầu (chỉ ~170KB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

def imread_utf8(path):
    with open(path, "rb") as stream:
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        return cv2.imdecode(numpyarray, cv2.IMREAD_COLOR)

def imwrite_utf8(path, img):
    ext = os.path.splitext(path)[1] or ".jpg"
    is_success, im_buf_arr = cv2.imencode(ext, img)
    if is_success:
        im_buf_arr.tofile(path)
    return is_success

def upscale_image(input_path, output_path):
    download_model()

    img = imread_utf8(input_path)
    if img is None:
        print(f"❌ Không thể đọc ảnh: {input_path}")
        return False

    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(MODEL_PATH)
    sr.setModel("fsrcnn", 4)

    print(f"✨ Đang chạy AI Upscale (FSRCNN 4x) để tăng độ nét cho: {os.path.basename(input_path)}...")
    result = sr.upsample(img)

    if not imwrite_utf8(output_path, result):
        print(f"❌ Ghi file thất bại: {output_path}")
        return False
    return True
