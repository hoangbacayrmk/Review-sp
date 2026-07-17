import os
import requests
import json

def generate_voiceover(script_data: dict, filename: str = "voice.mp3"):
    """
    Sử dụng ElevenLabs để sinh file MP3 từ kịch bản.
    Tự động quét mảng danh sách API Key và tự động fallback khi key hết Credit.
    """
    keys_str = os.getenv("ELEVENLABS_API_KEY", "")
    # Tách chuỗi thành mảng các key, loại bỏ khoảng trắng
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    if not api_keys:
        print("Warning: Không tìm thấy ELEVENLABS_API_KEY, bỏ qua tạo audio.")
        return None
        
    # Lấy text từ kịch bản Gemini (Dùng voice_text để đọc tiếng dài, text chỉ để hiện lên màn hình)
    texts = [block.get("voice_text", block.get("text", "")) for block in script_data.get("text_blocks", [])]
    full_text = ". ".join(texts)
    
    if not full_text:
        return None

    # Sử dụng Voice ID mặc định: Bella (Hoạt động trên Free Plan, kết hợp Turbo v2.5 sẽ rất chuẩn tiếng Việt)
    # Anh có thể thay mã Voice ID khác vào biến môi trường nếu muốn
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL") 
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    data = {
        "text": full_text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.75
        }
    }
    
    # Chuẩn bị thư mục lưu file audio (thư mục public của Remotion)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # Thuật toán Fallback: Duyệt qua từng key
    for key in api_keys:
        print(f"Đang gọi ElevenLabs bằng Key: {key[:8]}...")
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": key
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print("✅ Tạo Voiceover thành công!")
                
                # Trả về tên file để Remotion dùng staticFile
                return filename
                
            elif response.status_code in [401, 429]:
                print(f"Key {key[:8]}... hết credit hoặc lỗi {response.status_code}. Tự động đổi key...")
                continue # Nhảy sang vòng lặp tiếp theo dùng key khác
            else:
                print(f"Lỗi ElevenLabs (Không phải do credit): {response.status_code} - {response.text}")
                continue # Vẫn thử key khác cho chắc chắn
                
        except Exception as e:
            print(f"Lỗi khi gửi request tới ElevenLabs: {e}")
            continue

    print("❌ THẤT BẠI: Toàn bộ danh sách Key ElevenLabs đều đã hết Credit hoặc bị lỗi.")
    return None
