import os
import json
import subprocess
import sys
import time
import argparse
import random
import shutil
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

from ai_writer import generate_ad_script
from audio_engine import generate_scene_voiceovers
from image_upscaler import upscale_image

# DANH SÁCH 5 GÓC ĐỘ (ANGLES) CHO A/B TESTING
ANGLES = [
    {"id": "painpoint", "desc": "Xoáy sâu vào nỗi đau, sự khó chịu khi dùng sản phẩm cũ, và giải pháp từ sản phẩm này"},
    {"id": "fomo", "desc": "Tạo sự khan hiếm, nhấn mạnh sản phẩm đang cực kỳ hot trên TikTok, cháy hàng liên tục"},
    {"id": "unboxing", "desc": "Trải nghiệm đập hộp, cảm nhận lần đầu tiên cầm trên tay cực kỳ chân thực"},
    {"id": "hardsell", "desc": "Phân tích trực diện tính năng, chất liệu cao cấp và sự bền bỉ của sản phẩm"},
    {"id": "shock", "desc": "Dùng ngôn từ gây sốc, thách thức người xem, ví dụ 'đừng mua nếu không muốn...'"}
]

CTA_DURATION_FRAMES = 90  # 3 giây end-card chốt đơn


def parse_args():
    parser = argparse.ArgumentParser(description="Tự động render video quảng cáo AI (A/B testing nhiều góc độ)")
    valid_ids = [a["id"] for a in ANGLES]
    parser.add_argument(
        "--angle", type=str, default=None, choices=valid_ids,
        help=f"Chỉ chạy 1 góc độ cụ thể thay vì cả {len(valid_ids)} góc độ. Chọn 1 trong: {', '.join(valid_ids)}"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Render lại dù video đã tồn tại (mặc định sẽ bỏ qua để tiết kiệm credit AI)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=== TỰ ĐỘNG HÓA RENDER VIDEO QUẢNG CÁO ===")

    # 1. Quét thư mục ảnh đầu vào
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input_images")
    public_img_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public", "images")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(public_img_dir, exist_ok=True)

    input_images = []
    remotion_images = []
    
    for file in os.listdir(input_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            src_path = os.path.join(input_dir, file)
            dest_path = os.path.join(public_img_dir, file)
            
            # Bỏ qua nếu ảnh này đã được upscale từ trước (chưa bị đè bằng ảnh mới hơn),
            # tránh chạy lại AI Upscale tốn CPU vô ích ở những lần chạy sau
            if os.path.exists(dest_path) and os.path.getmtime(dest_path) >= os.path.getmtime(src_path):
                print(f"⏭️  Đã upscale sẵn, bỏ qua: {file}")
            else:
                # Áp dụng AI Upscale để tăng nét ảnh gấp 4 lần trước khi copy
                success = upscale_image(src_path, dest_path)
                if not success:
                    print(f"⚠️ Dùng ảnh gốc vì upscale lỗi: {file}")
                    shutil.copy2(src_path, dest_path)
            
            input_images.append(src_path)  # Để AI đọc viết kịch bản
            remotion_images.append(f"images/{file}")  # Để Remotion dùng làm cảnh video

    if not input_images:
        print("❌ Thư mục trống! Anh hãy copy/tải ảnh sản phẩm từ Shopee, TikTok ném vào thư mục này nhé:")
        print(f"👉 {input_dir}")
        print("Sau đó chạy lại lệnh này.")
        return

    print(f"[1] Đã nhận {len(input_images)} ảnh sản phẩm từ máy tính.")

    angles = [a for a in ANGLES if a["id"] == args.angle] if args.angle else ANGLES

    output_data_dir = os.path.join(os.path.dirname(__file__), "output_data")
    os.makedirs(output_data_dir, exist_ok=True)
    renderer_dir = os.path.join(os.path.dirname(__file__), "..", "renderer")
    output_videos_dir = os.path.join(os.path.dirname(__file__), "..", "output_videos")
    os.makedirs(output_videos_dir, exist_ok=True)

    bgm_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public", "bgm")
    os.makedirs(bgm_dir, exist_ok=True)
    bgm_files = [f for f in os.listdir(bgm_dir) if f.lower().endswith('.mp3')]
    if not bgm_files:
        print("⚠️  CẢNH BÁO: Chưa có nhạc nền (BGM) nào trong thư mục sau, video sẽ chạy KHÔNG có nhạc lót:")
        print(f"   👉 {bgm_dir}")
        print("   Hãy tải nhạc royalty-free hợp pháp (Uppbeat, Mixkit, YouTube Audio Library...) rồi bỏ .mp3 vào đó.")

    sfx_dir = os.path.join(os.path.dirname(__file__), "..", "renderer", "public", "sfx")
    os.makedirs(sfx_dir, exist_ok=True)
    sfx_files = [f for f in os.listdir(sfx_dir) if f.lower().endswith('.mp3')]

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n🚀 BẮT ĐẦU CHIẾN DỊCH A/B TESTING - {len(angles)} VIDEO...\n")

    for i, angle_info in enumerate(angles):
        angle_id = angle_info["id"]
        angle_desc = angle_info["desc"]

        print("=" * 40)
        print(f"🎬 VIDEO {i + 1}/{len(angles)}: Góc độ [{angle_id.upper()}]")
        print("=" * 40)

        output_video_path = os.path.join(output_videos_dir, f"ad_{angle_id}.mp4")

        # Bỏ qua nếu đã render trước đó, tránh tốn credit Gemini/ElevenLabs vô ích
        if os.path.exists(output_video_path) and not args.force:
            print(f"⏭️  Đã tồn tại {output_video_path}, bỏ qua (dùng --force để render lại).")
            continue

        # 2. Sinh kịch bản
        print("[2] Đang gọi AI viết kịch bản quảng cáo...")
        script = generate_ad_script(input_images, angle=angle_desc)
        captions = script.get("text_blocks", [])

        # 3. Tạo Audio RIÊNG cho từng cảnh -> lấy thời lượng THẬT (chính xác tuyệt đối,
        # không còn đoán tỷ lệ theo số ký tự nên hình luôn khớp lời)
        print("[3] Đang gọi ElevenLabs tạo Voiceover cho từng phân cảnh...")
        scene_audio = generate_scene_voiceovers(captions, angle_id)

        # 3.5 Quét nhạc nền ngẫu nhiên
        selected_bgm = f"bgm/{random.choice(bgm_files)}" if bgm_files else None
        if selected_bgm:
            print(f"[3.5] Đã trộn ngẫu nhiên nhạc nền: {selected_bgm}")

        # 3.6 Gán Start/End Frame theo thời lượng audio thật + trộn SFX chuyển cảnh
        current_frame = 0
        for i_cap, (cap, audio_info) in enumerate(zip(captions, scene_audio)):
            duration_frames = audio_info["durationFrames"]
            cap["audioPath"] = audio_info["audioPath"]
            cap["startFrame"] = current_frame
            cap["endFrame"] = current_frame + duration_frames
            
            # QUAN TRỌNG: Ghi đè imageIndex để video sử dụng xoay vòng toàn bộ các ảnh 
            # (POV) vừa được tự động đẻ ra, giúp mỗi cảnh là một bối cảnh khác nhau.
            if len(remotion_images) > 0:
                cap["imageIndex"] = i_cap % len(remotion_images)
                
            current_frame += duration_frames

            if i_cap > 0 and sfx_files:
                cap["sfxPath"] = f"sfx/{random.choice(sfx_files)}"

        # 3.7 Thêm cảnh CTA/End-card chốt đơn (khung hình riêng, không lẫn với cảnh sản phẩm)
        cta_scene = {
            "isCta": True,
            "text": "MUA NGAY HÔM NAY",
            "subtext": "Link sản phẩm ở phần bình luận 👇",
            "imageIndex": len(remotion_images) - 1,
            "startFrame": current_frame,
            "endFrame": current_frame + CTA_DURATION_FRAMES,
        }
        if sfx_files:
            cta_scene["sfxPath"] = f"sfx/{random.choice(sfx_files)}"
        captions.append(cta_scene)
        current_frame += CTA_DURATION_FRAMES

        # 4. Gói dữ liệu JSON cho Remotion
        ad_data = {
            "productImages": remotion_images,
            "captions": captions,
            "bgmPath": selected_bgm,
            "angleId": angle_id
        }

        json_path = os.path.join(output_data_dir, f"ad_data_{angle_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ad_data, f, ensure_ascii=False, indent=4)
        print(f"[4] Đã tạo file dữ liệu cấu hình: {json_path}")

        # Lưu lại bản render cũ (nếu có) trước khi ghi đè, để so sánh A/B giữa các lần chạy
        if os.path.exists(output_video_path):
            archive_dir = os.path.join(output_videos_dir, "archive", run_timestamp)
            os.makedirs(archive_dir, exist_ok=True)
            shutil.move(output_video_path, os.path.join(archive_dir, f"ad_{angle_id}.mp4"))
            print(f"🗃️  Đã lưu bản cũ vào: {archive_dir}")

        # 5. Gọi Remotion để Render
        print("[5] Kích hoạt Xưởng Render Video (Remotion)...")

        remotion_cmd = [
            "npx", "remotion", "render", "AutoAd",
            f'"{output_video_path}"',
            f'--props="{json_path}"'
        ]

        print(f"Executing: {' '.join(remotion_cmd)}")
        subprocess.run(" ".join(remotion_cmd), shell=True, cwd=renderer_dir)
        print(f"✅ HOÀN THÀNH VIDEO {i + 1}: {output_video_path}\n")

        if i < len(angles) - 1:
            print("⏳ Nghỉ 5 giây trước khi sang góc độ tiếp theo...")
            time.sleep(5)

    print(f"🎉 XONG! {len(angles)} VIDEO ĐÃ ĐƯỢC XỬ LÝ. SẴN SÀNG CHẠY ADS!")


if __name__ == "__main__":
    main()
