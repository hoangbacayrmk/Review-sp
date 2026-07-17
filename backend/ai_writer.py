import os
import json
from google import genai
from google.genai import types
from PIL import Image


# Dùng alias "-latest" thay vì ghim version cụ thể (vd: gemini-2.5-flash) vì Google
# thường xuyên rút quyền truy cập các version cũ với tài khoản/key mới ("no longer
# available to new users"). Alias này được Google tự trỏ sang model flash mới nhất
# còn hỗ trợ, nên không bao giờ bị lỗi 404 vì lỗi thời.
GEMINI_MODEL = "gemini-flash-latest"


def generate_ad_script(image_urls: list, angle: str = "Tập trung vào tính năng nổi bật"):
    """
    Sử dụng Gemini Vision để phân tích mảng ảnh và sinh kịch bản kèm chuyển cảnh.
    """
    raw_keys = os.getenv("GEMINI_API_KEY")
    if not raw_keys:
        print("Warning: Không tìm thấy GEMINI_API_KEY, dùng dữ liệu giả lập.")
        return get_mock_data()

    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

    # 1. Load mảng ảnh trước để tiết kiệm tài nguyên
    images = []
    for url in image_urls:
        try:
            if url.startswith("http"):
                import requests
                from io import BytesIO
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
    - 'imageIndex' là chỉ số ảnh (từ 0 đến {len(images) - 1}) phù hợp nhất cho phân cảnh đó.
    - 'transition' chỉ được phép chọn 1 trong 3 loại: "zoom", "cut", "slide".
    - Không trả về markdown, chỉ JSON thô.
    """

    # 3. Gửi cho Gemini với cơ chế xoay vòng Key (Fallback)
    contents = [prompt] + images

    for idx, key in enumerate(api_keys):
        try:
            print(f"Đang phân tích {len(images)} hình ảnh bằng Gemini (Key {idx + 1}/{len(api_keys)})...")
            client = genai.Client(api_key=key)

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            script_data = json.loads(response.text.strip())
            print(f"✅ Gemini (Key {idx + 1}) đã sinh kịch bản thành công!")
            return script_data

        except Exception as e:
            print(f"⚠️ Lỗi ở Key {idx + 1} ({str(e)[:80]}...). Tự động chuyển Key tiếp theo...")
            continue

    print("❌ THẤT BẠI: Toàn bộ danh sách Key Gemini đều đã hết Quota hoặc bị lỗi. Chuyển sang dữ liệu dự phòng.")
    return get_mock_data()


def get_mock_data():
    return {
        "text_blocks": [
            {
                "text": "SẢN PHẨM MỚI",
                "voice_text": "Trời ơi anh em nhìn này, hôm nay mình vừa săn được một con siêu phẩm cực kỳ đỉnh cao luôn. Nói thật là ban đầu mình cũng không tin đâu, nhưng khi tận mắt thấy và sờ thử thì mới tá hỏa vì chất lượng của nó.",
                "imageIndex": 0,
                "transition": "zoom"
            },
            {
                "text": "CHẤT LƯỢNG CAO",
                "voice_text": "Cầm trên tay mà cảm giác nó đầm, chắc chắn và xịn xò đến từng đường kim mũi chỉ. Chất liệu cao cấp chống nước hoàn toàn, dùng thử mấy hôm mà thấy ưng cái bụng vô cùng. Thực sự là một trải nghiệm vượt xa mức giá, dùng xong là nghiện luôn đấy anh em ạ.",
                "imageIndex": 1,
                "transition": "cut"
            },
            {
                "text": "MUA NGAY -30%",
                "voice_text": "Hàng này đang siêu hot và rất nhanh cháy hàng. Thông tin chi tiết sản phẩm mình để dưới phần bình luận, anh chị em bấm vào nhận ưu đãi ngay nhé kẻo lỡ!",
                "imageIndex": 2,
                "transition": "slide"
            }
        ]
    }
