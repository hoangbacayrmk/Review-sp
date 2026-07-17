import os
import time
import requests

ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella - Turbo v2.5 đọc tiếng Việt ổn định

# Tinh chỉnh giọng đọc theo từng góc độ cảm xúc (angle), để giọng KOL "diễn" đúng vibe
# thay vì dùng chung 1 setting trung tính cho mọi kiểu kịch bản.
ANGLE_VOICE_SETTINGS = {
    "painpoint": {"stability": 0.80, "similarity_boost": 0.75, "style": 0.15},  # trầm, đồng cảm
    "fomo":      {"stability": 0.40, "similarity_boost": 0.80, "style": 0.55},  # dồn dập, gấp gáp
    "unboxing":  {"stability": 0.55, "similarity_boost": 0.80, "style": 0.40},  # hào hứng tự nhiên
    "hardsell":  {"stability": 0.70, "similarity_boost": 0.75, "style": 0.25},  # tự tin, chắc chắn
    "shock":     {"stability": 0.30, "similarity_boost": 0.80, "style": 0.65},  # gằn giọng, gây sốc
}
DEFAULT_VOICE_SETTINGS = {"stability": 0.6, "similarity_boost": 0.75, "style": 0.3}


def _post_tts(text: str, voice_id: str, api_key: str, voice_settings: dict, max_retries: int = 3):
    """Gọi 1 request TTS tới ElevenLabs. Tự động chờ + thử lại (exponential backoff) khi bị 429."""
    url = ELEVEN_TTS_URL.format(voice_id=voice_id)
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": voice_settings,
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=60)
        except Exception as e:
            print(f"   Lỗi kết nối ElevenLabs: {e}")
            return None, "connection_error"

        if response.status_code == 200:
            return response.content, None

        if response.status_code == 429:
            wait = (2 ** attempt) * 3  # 3s, 6s, 12s
            print(f"   ⏳ Bị giới hạn tốc độ (429). Chờ {wait}s rồi thử lại (lần {attempt + 1}/{max_retries})...")
            time.sleep(wait)
            continue

        if response.status_code == 401:
            return None, "unauthorized"

        print(f"   Lỗi ElevenLabs {response.status_code}: {response.text[:150]}")
        return None, "error"

    return None, "rate_limited"


def generate_voiceover(text: str, filename: str, voice_settings: dict = None):
    """
    Sinh 1 file MP3 từ 1 đoạn thoại. Tự động xoay vòng API Key khi hết credit,
    và tự động chờ + thử lại (exponential backoff) khi bị giới hạn tốc độ.
    Trả về tên file (để dùng với staticFile của Remotion) hoặc None nếu thất bại.
    """
    keys_str = os.getenv("ELEVENLABS_API_KEY", "")
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

    if not api_keys:
        print("Warning: Không tìm thấy ELEVENLABS_API_KEY, bỏ qua tạo audio.")
        return None

    if not text:
        return None

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    settings = voice_settings or DEFAULT_VOICE_SETTINGS

    output_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    for key in api_keys:
        print(f"   Đang gọi ElevenLabs bằng Key: {key[:8]}...")
        audio_bytes, err = _post_tts(text, voice_id, key, settings)

        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return filename

        if err == "unauthorized":
            print(f"   Key {key[:8]}... hết credit hoặc không hợp lệ. Tự động đổi key...")
        elif err == "rate_limited":
            print(f"   Key {key[:8]}... vẫn bị giới hạn tốc độ sau khi retry. Tự động đổi key...")
        continue

    print("❌ THẤT BẠI: Toàn bộ danh sách Key ElevenLabs đều đã hết Credit hoặc bị lỗi.")
    return None


def generate_scene_voiceovers(text_blocks: list, angle_id: str) -> list:
    """
    Sinh audio RIÊNG cho từng phân cảnh (thay vì gộp 1 file rồi đoán thời lượng theo tỷ lệ
    ký tự). Nhờ vậy mỗi cảnh có thời lượng CHÍNH XÁC TUYỆT ĐỐI khớp với giọng đọc thật,
    không còn bị lệch hình/lệch phụ đề với lời thoại.

    Trả về list dict: {"audioPath": str|None, "durationFrames": int}, cùng thứ tự text_blocks.
    """
    from mutagen.mp3 import MP3

    voice_settings = ANGLE_VOICE_SETTINGS.get(angle_id, DEFAULT_VOICE_SETTINGS)
    renderer_public = os.path.join(os.path.dirname(__file__), "..", "renderer", "public")

    results = []
    for i, block in enumerate(text_blocks):
        text = block.get("voice_text", block.get("text", ""))
        filename = f"voice_{angle_id}_{i}.mp3"

        print(f"[3.{i + 1}] Đang tạo Voiceover cho cảnh {i + 1}/{len(text_blocks)}...")
        audio_path = generate_voiceover(text, filename, voice_settings=voice_settings)

        duration_frames = 150  # fallback ~5s nếu TTS lỗi, để cảnh không bị duration 0
        if audio_path:
            full_path = os.path.join(renderer_public, audio_path)
            if os.path.exists(full_path):
                audio = MP3(full_path)
                duration_frames = max(1, round(audio.info.length * 30))  # 30 FPS

        results.append({"audioPath": audio_path, "durationFrames": duration_frames})

    return results
