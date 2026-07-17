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
        return get_mock_data(angle)

    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

    # 1. Load mảng ảnh trước để tiết kiệm tài nguyên
    images = []
    for url in image_urls:
        try:
            if url.startswith("http"):
                import requests
                from io import BytesIO
                response = requests.get(url, timeout=30)
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
    Bạn là một siêu KOL / Tiktoker review sản phẩm với hàng triệu người theo dõi. Lời thoại phải cực kỳ tự nhiên, mang đậm tính kể chuyện (storytelling).
    XƯNG HÔ: Luôn gọi người xem là "anh chị em" xuyên suốt kịch bản (KHÔNG dùng "anh em", "cả nhà", "các bạn", "ae" hay bất kỳ cách gọi nào khác).

    QUAN TRỌNG - CÂU MỞ ĐẦU (HOOK) PHẢI BÁM SÁT ĐÚNG GÓC ĐỘ "{angle}" Ở TRÊN, KHÔNG ĐƯỢC DÙNG CHUNG MỘT KIỂU MỞ ĐẦU CHO MỌI GÓC ĐỘ:
    TUYỆT ĐỐI KHÔNG mở đầu bằng các câu cảm thán chung chung như "Sốc thật sự", "Trời ơi", "Không thể tin nổi" trừ khi góc độ hiện tại đúng thực sự là gây sốc/bất ngờ. Mỗi góc độ phải mở đầu theo đúng tinh thần của nó, ví dụ:
    - Nỗi đau (painpoint): mở đầu bằng cách gọi tên chính xác sự khó chịu, bực bội cụ thể mà người xem đang gặp phải với sản phẩm cũ.
    - Khan hiếm (fomo): mở đầu bằng tin tức cháy hàng, số lượng còn lại, tốc độ bán ra nhanh thế nào.
    - Đập hộp (unboxing): mở đầu bằng hành động thật đang cầm/mở/bóc sản phẩm trên tay.
    - Phân tích trực diện (hardsell): mở đầu bằng một nhận định, con số hoặc phép so sánh thẳng thắn về chất lượng.
    - Gây sốc (shock): đây là góc độ DUY NHẤT được phép dùng câu cảm thán mạnh kiểu "Sốc thật sự", câu thách thức hoặc sự thật gây bất ngờ.
    Tránh hô hào quảng cáo nhàm chán, thay vào đó là phong cách review bóc tách thực tế.

    YÊU CẦU ĐẦU RA (JSON FORMAT CHÍNH XÁC NHƯ SAU):
    {{
        "text_blocks": [
            {{
                "text": "TỪ KHOÁ MỞ ĐẦU",
                "voice_text": "Câu văn thứ nhất (Khoảng 40-50 từ): Nhập đề theo phong cách KOL, ĐÚNG tinh thần góc độ '{angle}' đã nêu ở trên (không mặc định là câu gây sốc trừ khi góc độ đó thực sự yêu cầu) để giữ chân người xem ngay lập tức.",
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
    return get_mock_data(angle)


def get_mock_data(angle: str = ""):
    angle_lower = angle.lower()
    if "nỗi đau" in angle_lower or "painpoint" in angle_lower:
        intro = "Anh chị em nào đang đau đầu vì đồ cũ dùng chán quá thì phải xem ngay video này. Thề luôn, tìm được con hàng này như vớ được vàng, giải quyết dứt điểm sự khó chịu bữa giờ!"
    elif "khan hiếm" in angle_lower or "hot" in angle_lower or "fomo" in angle_lower:
        intro = "Nhanh tay anh chị em ơi, con siêu phẩm này đang cháy hàng trên mọi mặt trận rồi! Mình canh me mãi mới chốt được 1 suất để review cho anh chị em xem đây này!"
    elif "gây sốc" in angle_lower or "shock" in angle_lower:
        intro = "Thật không thể tin nổi! Mình vừa tìm ra một bí mật về sản phẩm này mà chắc chắn sẽ làm anh chị em ngã ngửa. Phải xem kỹ video này kẻo lại tiếc hùi hụi nhé!"
    elif "đập hộp" in angle_lower or "unboxing" in angle_lower:
        intro = "Đợi mãi thì hàng cũng về, hôm nay cùng mình đập hộp bóc seal con hàng nóng hổi này xem bên trong có gì mà giang hồ đồn đại xịn sò thế nhé. Cầm trên tay nặng trịch luôn!"
    else:
        intro = "Hé lô anh chị em, hôm nay lên cho anh chị em một con hàng cực phẩm mà mình vừa test xong. Phải nói là nó quá xứng đáng với từng đồng tiền bát gạo luôn, anh chị em xem kỹ chi tiết nhé."

    return {
        "text_blocks": [
            {
                "text": "SẢN PHẨM MỚI",
                "voice_text": intro,
                "imageIndex": 0,
                "transition": "zoom"
            },
            {
                "text": "CHẤT LƯỢNG CAO",
                "voice_text": "Sờ tận tay mới thấy chất liệu của nó cực kỳ cao cấp, các chi tiết được gia công tỉ mỉ không một vết xước. Dùng thử mấy hôm mà thấy hiệu quả rõ rệt luôn. Thực sự là một trải nghiệm vượt xa mức giá, dùng xong là nghiền ngay lập tức.",
                "imageIndex": 1,
                "transition": "cut"
            },
            {
                "text": "MUA NGAY -30%",
                "voice_text": "Thông tin chi tiết sản phẩm mình để dưới phần bình luận, anh chị em bấm vào nhận ưu đãi giảm ngay 30% hôm nay nhé kẻo lỡ!",
                "imageIndex": 2,
                "transition": "slide"
            }
        ]
    }
