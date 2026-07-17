import os
from io import BytesIO
from PIL import Image
from rembg import remove, new_session

def process_image(input_path, output_path):
    """
    Xóa nền ảnh bằng AI (rembg) và lưu thành PNG trong suốt.
    Sử dụng model isnet-general-use chuyên dụng cho độ chính xác tuyệt đối.
    Sau đó crop khít theo đúng biên sản phẩm (bỏ khoảng trống thừa quanh ảnh gốc),
    để khi Remotion zoom/crop vào từng góc ảnh (cận cảnh trên/dưới/trái/phải) luôn
    có nội dung sản phẩm thật, không bị lẹm vào vùng trong suốt trống rỗng.
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

        img = Image.open(BytesIO(output_data)).convert("RGBA")
        # Chỉ tính bbox theo pixel có alpha đủ rõ (>30), bỏ qua viền mờ/bóng phản
        # chiếu bán trong suốt mà rembg đôi khi chưa xóa sạch hết - nếu không bbox
        # sẽ bị kéo rộng ra bao gồm cả vùng nhiễu đó, khiến crop đa góc bị lem.
        alpha = img.split()[-1]
        solid_mask = alpha.point(lambda p: 255 if p > 30 else 0)
        bbox = solid_mask.getbbox()
        if bbox:
            left, top, right, bottom = bbox
            pad_x = int((right - left) * 0.04)
            pad_y = int((bottom - top) * 0.04)
            left = max(0, left - pad_x)
            top = max(0, top - pad_y)
            right = min(img.width, right + pad_x)
            bottom = min(img.height, bottom + pad_y)
            img = img.crop((left, top, right, bottom))

        img.save(output_path)
        return True
    except Exception as e:
        print(f"Lỗi khi xóa nền: {e}")
        return False
