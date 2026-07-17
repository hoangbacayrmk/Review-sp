import os
import json
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

def generate_ad_script(image_urls: list, angle: str = "Tập trung vào tính năng nổi bật"):
    """
    Sử dụng Gemini 3.5 Flash Vision để phân tích mảng ảnh và sinh kịch bản kèm chuyển cảnh.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: Không tìm thấy GEMINI_API_KEY, dùng dữ liệu giả lập.")
        return get_mock_data()
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    # 1. Load mảng ảnh
    images = []
    for url in image_urls:
        try:
            if url.startswith("http"):
                response = requests.get(url)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(url)
            images.append(img)
        except Exception as e:
            print(f"Error loading image {url}: {e}")

    # 2. Prompt thiết kế riêng cho Video Ads nhiều cảnh
    prompt = f"""
    Bạn là một chuyên gia chạy Facebook/TikTok Ads thực chiến đẳng cấp thế giới.
    Hãy phân tích {len(images)} hình ảnh sản phẩm tôi gửi, tự động nhận diện đâu là ảnh tổng quan, đâu là ảnh chi tiết, đâu là ảnh ứng dụng.
    
    YÊU CẦU QUAN TRỌNG NHẤT: Kịch bản phải được thiết kế theo góc độ (Marketing Angle): "{angle}".
    Hãy điều chỉnh văn phong, từ ngữ và chiến lược chốt sale đúng theo góc độ này.

    Dựa vào đó, hãy viết một kịch bản Video Ads dài từ 30 đến 45 giây. TỔNG SỐ TỪ (WORD COUNT) PHẢI ĐẠT TỪ 120 ĐẾN 150 TỪ.
    
    YÊU CẦU NHẬP VAI: 
    Bạn là một siêu KOL / Tiktoker review sản phẩm với hàng triệu người theo dõi. Lời thoại phải cực kỳ tự nhiên, mang đậm tính kể chuyện (storytelling), sử dụng những từ cảm thán (Ví dụ: "Trời ơi", "Anh em nhìn này", "Thực sự đỉnh", "Nét căng"). Tránh kiểu hô hào quảng cáo nhàm chán, thay vào đó là phong cách review "người thật việc thật", bóc tách tường tận chất liệu, trải nghiệm sử dụng thực tế và khơi gợi cảm xúc mạnh liệt.
    
    YÊU CẦU ĐẦU RA (JSON FORMAT CHÍNH XÁC NHƯ SAU):
    {{
        "text_blocks": [
            {{
                "text": "TỪ KHOÁ GÂY SỐC",
                "voice_text": "Câu văn thứ nhất (Khoảng 40-50 từ): Nhập đề theo phong cách KOL, kể một câu chuyện ngắn hoặc một sự thật gây sốc để giữ chân người xem ngay lập tức.",
                "imageIndex": 0, 
                "transition": "zoom" 
            }},
            {{
                "text": "TÍNH NĂNG ĐỈNH",
                "voice_text": "Câu văn thứ hai (Khoảng 50-70 từ): Đi sâu vào review chi tiết trải nghiệm thực tế. Khen ngợi chất liệu, tính năng vượt trội, và cảm giác tuyệt vời khi sử dụng sản phẩm. Dùng ngôn từ mạnh, giàu hình ảnh.",
                "imageIndex": 1,
                "transition": "cut"
            }},
            {{
                "text": "MUA NGAY -30%",
                "voice_text": "Câu văn thứ ba (Khoảng 30 từ): Dồn dập khan hiếm và đọc chính xác câu: 'Thông tin sản phẩm để dưới phần bình luận anh chị em bấm vào nhận ưu đãi ngay nhé'.",
                "imageIndex": 2,
                "transition": "slide"
            }}
        ]
    }}
    Lưu ý:
    - 'imageIndex' là chỉ số ảnh (từ 0 đến {len(images)-1}) phù hợp nhất cho phân cảnh đó.
    - 'transition' chỉ được phép chọn 1 trong 3 loại: "zoom", "cut", "slide".
    - Không trả về markdown, chỉ JSON thô.
    """

    # 3. Gửi cho Gemini (Truyền cả prompt và mảng ảnh)
    try:
        print(f"Đang phân tích {len(images)} hình ảnh bằng Gemini 3.5 Flash...")
        contents = [prompt] + images
        response = model.generate_content(contents)
        
        # Bóc tách JSON từ chuỗi trả về
        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
            
        script_data = json.loads(text_resp.strip())
        print("✅ Gemini đã sinh kịch bản thành công!")
        return script_data
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return get_mock_data()

def get_mock_data():
    return {
         "text_blocks": [
            {"text": "SẢN PHẨM MỚI", "startFrame": 0, "endFrame": 45, "imageIndex": 0, "transition": "zoom"},
            {"text": "CHẤT LƯỢNG CAO TỪ GEMINI", "startFrame": 45, "endFrame": 90, "imageIndex": 1, "transition": "cut"},
            {"text": "MUA NGAY HÔM NAY", "startFrame": 90, "endFrame": 150, "imageIndex": 2, "transition": "slide"}
        ]
    }
