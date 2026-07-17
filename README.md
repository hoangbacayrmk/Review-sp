# Auto Video SP (Siêu Tốc & Tinh Gọn)

Hệ thống tự động hoá sản xuất video quảng cáo TikTok/Reels/Shorts từ kho ảnh có sẵn.
Đã được tinh gọn tối đa: bỏ qua các khâu AI xoá nền nặng nề, chuyển sang phong cách **review ảnh chân thực**. Chỉ việc thả ảnh thật (feedback, màn hình cap) vào, hệ thống sẽ tự động phóng to full màn hình (không viền đen), thêm hiệu ứng lia máy (Ken Burns), viết kịch bản, lồng tiếng KOL và xuất ra 5 camp video thần tốc.

## Quy trình hoạt động mới

```
input_images/ (Thả các ảnh sạch logo vào đây)
      │
      ▼
[1] main.py              → Bốc thẳng ảnh đưa vào xưởng (Tối đa hoá tốc độ)
      │
      ▼
[2] ai_writer.py         → Gemini (Vision) quét toàn bộ ảnh, lên kịch bản A/B Testing 5 góc độ
      │
      ▼
[3] audio_engine.py      → ElevenLabs đọc giọng KOL, gán thời lượng khớp tuyệt đối từng khung hình
      │
      ▼
[4] Remotion (renderer/) → Lắp ráp thành video 1080x1920 (Hiệu ứng Ken Burns full màn, phụ đề động gắt)
      │
      ▼
output_videos/           → 5 Video đuôi .mp4
```

Mỗi lần chạy, hệ thống tạo **5 video độc lập** theo 5 góc độ marketing khác nhau (A/B testing):

| Angle | Chiến lược |
|---|---|
| `painpoint` | Xoáy vào nỗi đau khi dùng sản phẩm cũ |
| `fomo` | Khan hiếm, đang hot, sắp cháy hàng |
| `unboxing` | Trải nghiệm đập hộp chân thực |
| `hardsell` | Phân tích trực diện tính năng, chất liệu |
| `shock` | Ngôn từ gây sốc, thách thức người xem |

## Cấu trúc thư mục (Đã tối giản)

```
backend/              Lõi điều phối Python
  main.py             Máy trưởng điều phối quy trình
  ai_writer.py        "KOL" viết kịch bản (Gemini)
  audio_engine.py     "Voice talent" lồng tiếng (ElevenLabs)
  output_data/        Nơi xuất file cấu hình kịch bản JSON

renderer/             Xưởng dựng video (React/Remotion)
  src/AdTemplate.tsx  Giao diện video (Ken Burns 100% full viền, phụ đề giật gân Hormozi)
  public/images/      Kho chứa tạm ảnh nguồn
  public/bgm/         Nhạc nền (Anh em tự thả file .mp3 vào)
  public/sfx/         Hiệu ứng quẹt chuyển cảnh

input_images/         Thả ảnh nguyên liệu vào đây!
output_videos/        Video thành phẩm xuất ra ở đây!
```

## Cài đặt (Chưa tới 1 phút)

**1. Môi trường Python (Backend)**
Cực nhẹ, đã xoá sạch các thư viện AI nặng nề (rembg, onnxruntime...).
```bash
cd backend
pip install -r requirements.txt
```

**2. Môi trường Remotion (Xưởng Video)**
```bash
cd renderer
npm install
```

**3. Khai báo API Key**
Tạo file `.env` ở trong mục `backend/` như sau:
```env
# Cho phép nạp nhiều key cách nhau bằng dấu phẩy để hệ thống tự xoay vòng khi hết tiền
GEMINI_API_KEY=key_gemini_cua_ban
ELEVENLABS_API_KEY=key_elevenlabs_cua_ban
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
```

## Hướng dẫn sử dụng (Bấm 1 Nút)

1. **Chuẩn bị:** Quét sạch thư mục `input_images/`.
2. **Nạp đạn:** Thả toàn bộ ảnh bạn muốn ghép thành video vào `input_images/`. 
   > 💡 **Tip:** Hệ thống sẽ tự động ép ảnh fill kín toàn bộ màn hình 9:16 mà không để hở viền đen, nên ảnh dọc là đẹp nhất. Nhớ crop bỏ logo TikTok/FB (khoảng 15% viền trên dưới) trước khi thả vào để video sạch sẽ 100%.
3. **Khai Hoả:** Mở Terminal tại thư mục `backend` và chạy:
   ```bash
   python main.py
   ```
4. **Hưởng thụ:** Nhâm nhi ngụm trà, 2 phút sau vào `output_videos/` lấy 5 video đi vít Ads!
