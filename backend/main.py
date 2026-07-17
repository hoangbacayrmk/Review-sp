import os
import json
import subprocess
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

from ai_writer import generate_ad_script
from audio_engine import generate_voiceover
from image_processor import process_image

def main():
    print("=== TỰ ĐỘNG HÓA RENDER VIDEO QUẢNG CÁO ===")
    
    # 1. Quét thư mục ảnh đầu vào
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input_images")
    public_img_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public", "images")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(public_img_dir, exist_ok=True)
    
    input_images = []
    remotion_images = []
    import shutil
    for file in os.listdir(input_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            src_path = os.path.join(input_dir, file)
            # Tạo tên file mới đuôi .png vì ảnh đã xóa phông
            base_name = os.path.splitext(file)[0]
            new_filename = f"{base_name}_nobg.png"
            dest_path = os.path.join(public_img_dir, new_filename)
            
            # Xóa phông bằng AI
            process_image(src_path, dest_path)
            
            input_images.append(src_path) # để Gemini đọc (ảnh gốc để hiểu bối cảnh)
            remotion_images.append(f"images/{new_filename}") # để Remotion đọc ảnh đã xóa phông
            
    if not input_images:
        print(f"❌ Thư mục trống! Anh hãy copy/tải ảnh sản phẩm từ Shopee, TikTok ném vào thư mục này nhé:")
        print(f"👉 {input_dir}")
        print("Sau đó chạy lại lệnh này.")
        return
        
    print(f"[1] Đã nhận {len(input_images)} ảnh sản phẩm từ máy tính.")
    
    # DANH SÁCH 5 GÓC ĐỘ (ANGLES) CHO A/B TESTING
    angles = [
        {"id": "painpoint", "desc": "Xoáy sâu vào nỗi đau, sự khó chịu khi dùng sản phẩm cũ, và giải pháp từ sản phẩm này"},
        {"id": "fomo", "desc": "Tạo sự khan hiếm, nhấn mạnh sản phẩm đang cực kỳ hot trên TikTok, cháy hàng liên tục"},
        {"id": "unboxing", "desc": "Trải nghiệm đập hộp, cảm nhận lần đầu tiên cầm trên tay cực kỳ chân thực"},
        {"id": "hardsell", "desc": "Phân tích trực diện tính năng, chất liệu cao cấp và sự bền bỉ của sản phẩm"},
        {"id": "shock", "desc": "Dùng ngôn từ gây sốc, thách thức người xem, ví dụ 'đừng mua nếu không muốn...'"}
    ]
    
    output_data_dir = os.path.join(os.path.dirname(__file__), "output_data")
    os.makedirs(output_data_dir, exist_ok=True)
    renderer_dir = os.path.join(os.path.dirname(__file__), "..", "renderer")
    
    import random
    bgm_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public", "bgm")
    os.makedirs(bgm_dir, exist_ok=True)
    bgm_files = [f for f in os.listdir(bgm_dir) if f.lower().endswith('.mp3')]
    
    sfx_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public", "sfx")
    os.makedirs(sfx_dir, exist_ok=True)
    sfx_files = [f for f in os.listdir(sfx_dir) if f.lower().endswith('.mp3')]
    
    print(f"\n🚀 BẮT ĐẦU CHẠY CHIẾN DỊCH A/B TESTING - TẠO {len(angles)} VIDEO...\n")
    
    for i, angle_info in enumerate(angles):
        angle_id = angle_info["id"]
        angle_desc = angle_info["desc"]
        
        print("=" * 40)
        print(f"🎬 VIDEO {i+1}/{len(angles)}: Góc độ [{angle_id.upper()}]")
        print("=" * 40)
        
        # 2. Sinh kịch bản
        print("[2] Đang gọi AI viết kịch bản quảng cáo...")
        script = generate_ad_script(input_images, angle=angle_desc)
        
        # 3. Tạo Audio
        print("[3] Đang gọi ElevenLabs tạo Voiceover...")
        audio_filename = f"voice_{angle_id}.mp3"
        audio_path = generate_voiceover(script, filename=audio_filename)

        # Đọc độ dài Audio thực tế để phân bổ Frame (Chính xác tuyệt đối)
        total_audio_frames = 900 # Mặc định 30s nếu có lỗi
        if audio_path:
            from mutagen.mp3 import MP3
            full_audio_path = os.path.join(renderer_dir, "public", audio_path)
            if os.path.exists(full_audio_path):
                audio = MP3(full_audio_path)
                total_audio_frames = int(audio.info.length * 30) # 30 FPS

        # 3.5 Quét nhạc nền ngẫu nhiên
        selected_bgm = f"bgm/{random.choice(bgm_files)}" if bgm_files else None
        if selected_bgm:
            print(f"[3.5] Đã trộn ngẫu nhiên nhạc nền: {selected_bgm}")
            
        # 3.6 Tính toán Start/End Frame và Trộn SFX Chuyển cảnh
        captions = script.get("text_blocks", [])
        
        # Tính tổng số chữ để chia tỷ lệ frame
        total_chars = sum(len(cap.get("voice_text", cap.get("text", ""))) for cap in captions)
        if total_chars == 0: total_chars = 1
        
        current_frame = 0
        for i_cap, cap in enumerate(captions):
            # Tính duration frame cho phân cảnh này
            char_count = len(cap.get("voice_text", cap.get("text", "")))
            duration_frames = int((char_count / total_chars) * total_audio_frames)
            
            # Cảnh cuối cùng sẽ nhận toàn bộ frame còn lại để đảm bảo không bị hụt/lệch
            if i_cap == len(captions) - 1:
                duration_frames = total_audio_frames - current_frame

            cap["startFrame"] = current_frame
            cap["endFrame"] = current_frame + duration_frames
            current_frame += duration_frames
            
            # Gắn SFX
            if i_cap > 0 and sfx_files:
                cap["sfxPath"] = f"sfx/{random.choice(sfx_files)}"

        # 4. Gói dữ liệu JSON cho Remotion
        ad_data = {
            "productImages": remotion_images,
            "captions": captions,
            "audioPath": audio_path,
            "bgmPath": selected_bgm
        }
        
        json_path = os.path.join(output_data_dir, f"ad_data_{angle_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ad_data, f, ensure_ascii=False, indent=4)
        print(f"[4] Đã tạo file dữ liệu cấu hình: {json_path}")
        
        # 5. Gọi Remotion để Render
        print("[5] Kích hoạt Xưởng Render Video (Remotion)...")
        output_video_path = os.path.join(os.path.dirname(__file__), "..", "output_videos", f"ad_{angle_id}.mp4")
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

        remotion_cmd = [
            "npx", "remotion", "render", "AutoAd", 
            f'"{output_video_path}"', 
            f'--props="{json_path}"'
        ]
        
        print(f"Executing: {' '.join(remotion_cmd)}")
        subprocess.run(" ".join(remotion_cmd), shell=True, cwd=renderer_dir)
        print(f"✅ HOÀN THÀNH VIDEO {i+1}: {output_video_path}\n")

    print(f"🎉 TẤT CẢ {len(angles)} VIDEO ĐÃ ĐƯỢC RENDER THÀNH CÔNG! SẴN SÀNG CHẠY ADS!")

if __name__ == "__main__":
    main()
