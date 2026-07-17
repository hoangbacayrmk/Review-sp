# Auto Video Ads

Tự động hoá sản xuất video quảng cáo TikTok/Reels từ ảnh sản phẩm bằng AI: xoá nền ảnh, viết kịch bản, đọc giọng KOL, dựng video có phụ đề động, nhạc nền và khung CTA chốt đơn — tất cả chỉ từ vài tấm ảnh sản phẩm.

## Pipeline hoạt động thế nào

```
input_images/ (ảnh sản phẩm gốc)
      │
      ▼
[1] image_processor.py  → rembg xoá nền + crop khít theo biên sản phẩm
      │
      ▼
[2] ai_writer.py         → Gemini (vision) viết kịch bản theo từng góc độ marketing
      │
      ▼
[3] audio_engine.py      → ElevenLabs đọc giọng KOL, TTS riêng từng cảnh (đồng bộ tuyệt đối)
      │
      ▼
[4] Remotion (renderer/) → dựng video dọc 1080x1920, phụ đề động, CTA, nhạc nền
      │
      ▼
output_videos/*.mp4
```

Mỗi lần chạy, hệ thống tạo **5 video độc lập** theo 5 góc độ marketing khác nhau (A/B testing):

| Angle | Chiến lược |
|---|---|
| `painpoint` | Xoáy vào nỗi đau khi dùng sản phẩm cũ |
| `fomo` | Khan hiếm, đang hot, sắp cháy hàng |
| `unboxing` | Trải nghiệm đập hộp chân thực |
| `hardsell` | Phân tích trực diện tính năng, chất liệu |
| `shock` | Ngôn từ gây sốc, thách thức người xem |

## Cấu trúc thư mục

```
backend/            Python - AI writer, TTS, xử lý ảnh, điều phối pipeline
  main.py           Điểm chạy chính
  ai_writer.py       Gemini viết kịch bản (google-genai SDK)
  audio_engine.py     ElevenLabs TTS + voice settings theo từng angle
  image_processor.py  rembg xoá nền + crop
  output_data/        JSON dữ liệu từng video (input cho Remotion)

renderer/           Remotion (React/TypeScript) - dựng video
  src/AdTemplate.tsx  Composition chính "AutoAd"
  public/images/      Ảnh sản phẩm đã xoá nền
  public/bgm/         Nhạc nền (.mp3, tự thêm - xem bên dưới)
  public/sfx/         Hiệu ứng âm thanh chuyển cảnh

input_images/       Ảnh sản phẩm gốc (thả ảnh vào đây)
output_videos/      Video hoàn chỉnh (.mp4)
```

## Cài đặt

**1. Python backend**

```bash
cd backend
pip install -r requirements.txt
```

**2. Remotion renderer**

```bash
cd renderer
npm install
```

**3. API keys**

Tạo file `backend/.env`:

```env
GEMINI_API_KEY=your_key_1,your_key_2,...
ELEVENLABS_API_KEY=your_key_1,your_key_2,...
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL   # tuỳ chọn, mặc định giọng Bella
```

Có thể điền nhiều key cách nhau bởi dấu phẩy — hệ thống tự động xoay vòng key khi một key hết credit hoặc bị giới hạn tốc độ (rate limit).

**4. Nhạc nền (tuỳ chọn nhưng nên có)**

Thả file `.mp3` bản quyền hợp lệ (Uppbeat, Mixkit, YouTube Audio Library...) vào `renderer/public/bgm/`. Không có thì video vẫn chạy được, chỉ là không có nhạc lót.

## Sử dụng

Thả ảnh sản phẩm (jpg/png/webp) vào `input_images/`, sau đó:

```bash
cd backend
python main.py                    # render cả 5 góc độ
python main.py --angle fomo       # chỉ render 1 góc độ
python main.py --angle fomo --force   # render lại dù đã tồn tại (mặc định sẽ bỏ qua để tiết kiệm credit AI)
```

Video ra ở `output_videos/ad_<angle>.mp4`. Bản render cũ (nếu ghi đè) được tự động lưu vào `output_videos/archive/<timestamp>/`.

## Ghi chú kỹ thuật

- Mỗi cảnh trong video có file voice TTS **riêng biệt**, thời lượng cảnh lấy chính xác từ độ dài audio thật (không đoán theo số ký tự) — đảm bảo hình luôn khớp lời.
- Nền video và tông giọng đọc được tinh chỉnh riêng theo từng góc độ marketing.
- Ảnh sản phẩm sau khi xoá nền được crop khít theo biên, và mỗi cảnh hiển thị một "góc máy" khác nhau (toàn cảnh / cận trên / cận dưới / cận trái-phải) từ cùng một tấm ảnh.
- Chi tiết cấu hình Remotion (fps, kích thước khung hình, dev server) xem thêm [renderer/README.md](renderer/README.md).
