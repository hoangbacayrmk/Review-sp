import os
from rembg import remove, new_session

def process_image(input_path, output_path):
    """
    Xóa nền ảnh bằng AI (rembg) và lưu thành PNG trong suốt.
    Sử dụng model isnet-general-use chuyên dụng cho độ chính xác tuyệt đối.
    """
    print(f"Đang xóa nền cho ảnh: {os.path.basename(input_path)}...")
    try:
        # Khởi tạo session với model ISNet (chính xác hơn U2Net mặc định)
        session = new_session("isnet-general-use")
        
        with open(input_path, 'rb') as i:
            input_data = i.read()
            
        # Xóa nền với thuật toán làm mịn viền vi pixel (Alpha Matting)
        # Giúp không bị lẹm vào sản phẩm, không bị răng cưa
        output_data = remove(
            input_data, 
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        
        with open(output_path, 'wb') as o:
            o.write(output_data)
        return True
    except Exception as e:
        print(f"Lỗi khi xóa nền: {e}")
        return False
