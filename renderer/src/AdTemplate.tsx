import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  Html5Audio as Audio,
  staticFile,
  Sequence
} from "remotion";
import { z } from "zod";

export const adSchema = z.object({
  productImages: z.array(z.string()),
  bgmPath: z.string().optional().nullable(),
  angleId: z.string().optional(),
  captions: z.array(
    z.object({
      text: z.string(),
      subtext: z.string().optional(),
      startFrame: z.number(),
      endFrame: z.number(),
      imageIndex: z.number().optional().default(0),
      transition: z.string().optional().default("cut"),
      sfxPath: z.string().optional(),
      audioPath: z.string().optional().nullable(),
      isCta: z.boolean().optional().default(false),
    })
  ),
});

type Caption = z.infer<typeof adSchema>["captions"][number];

// Tông nền riêng cho từng góc độ (angle) - tránh mọi video đều dùng chung 1 nền
// đen-xám lặp lại, mỗi angle có "mood" màu sắc khớp với cảm xúc kịch bản.
const ANGLE_THEMES: Record<string, { from: string; to: string }> = {
  painpoint: { from: "#1c2740", to: "#020306" }, // xanh navy trầm, đồng cảm
  fomo: { from: "#4a1010", to: "#050101" }, // đỏ lửa khẩn cấp
  unboxing: { from: "#4a3210", to: "#070502" }, // vàng ấm hào hứng
  hardsell: { from: "#2a2a38", to: "#040406" }, // xám thép tự tin
  shock: { from: "#3f0f38", to: "#070106" }, // tím-magenta gây sốc
};
const DEFAULT_THEME = { from: "#333333", to: "#000000" };

// Các kiểu "khung hình" (crop đa góc) xoay vòng theo thứ tự cảnh, để cùng 1 tấm
// ảnh sản phẩm vẫn tạo cảm giác nhiều góc máy khác nhau thay vì lặp y hệt.
// Cảnh đầu luôn "contain/center" để mở đầu bằng toàn cảnh sản phẩm rõ ràng.
const FRAMINGS: { position: string; fit: "contain" | "cover" }[] = [
  { position: "center", fit: "contain" },
  { position: "top", fit: "cover" },
  { position: "bottom", fit: "cover" },
  { position: "left", fit: "cover" },
  { position: "right", fit: "cover" },
];

export const AdTemplate: React.FC<z.infer<typeof adSchema>> = ({
  productImages,
  bgmPath,
  angleId,
  captions,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();
  const theme = (angleId && ANGLE_THEMES[angleId]) || DEFAULT_THEME;

  // Auto-ducking thật (không phải giả lập bằng volume cố định): fade in 15 frame đầu,
  // fade out 30 frame cuối, giữ mức nền thấp suốt video vì giọng đọc gần như xuyên suốt.
  // Phát đúng tốc độ gốc (không pitch-shift) -> bắt buộc dùng nhạc royalty-free hợp lệ.
  const fadeOutStart = Math.max(durationInFrames - 30, 1);
  const bgmFadeIn = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const bgmFadeOut = interpolate(frame, [fadeOutStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bgmVolume = 0.18 * Math.min(bgmFadeIn, bgmFadeOut);

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(circle at center, ${theme.from} 0%, ${theme.to} 80%)`,
      color: "white"
    }}>
      {bgmPath && <Audio src={staticFile(bgmPath)} volume={bgmVolume} />}

      {captions.map((caption, index) => {
        const duration = caption.endFrame - caption.startFrame;
        const imgUrl = productImages[caption.imageIndex || 0] || productImages[0];

        return (
          <Sequence
            key={index}
            from={caption.startFrame}
            durationInFrames={duration}
          >
            {caption.isCta ? (
              <CtaCard caption={caption} imgUrl={imgUrl} fps={fps} />
            ) : (
              <SceneContent
                caption={caption}
                imgUrl={imgUrl}
                fps={fps}
                transition={caption.transition}
                framing={FRAMINGS[index % FRAMINGS.length]}
              />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneContent: React.FC<{
  caption: Caption;
  imgUrl: string;
  fps: number;
  transition?: string;
  framing: { position: string; fit: "contain" | "cover" };
}> = ({ caption, imgUrl, fps, transition, framing }) => {
  const frame = useCurrentFrame();

  // 1. Ken Burns Zoom (Phóng to mượt mà)
  const zoomScale = interpolate(frame, [0, 150], [1, 1.2], {
    extrapolateRight: "clamp",
  });

  // 2. Slide Transition (Trượt từ phải sang)
  const slideX = transition === "slide" ? spring({
    frame,
    fps,
    config: { damping: 12 },
    from: 1000,
    to: 0
  }) : 0;

  // 3. Cut Transition (Mặc định) - Nảy (pop) lên nhẹ lúc mới cắt cảnh
  const cutScale = transition === "cut" ? spring({
      frame,
      fps,
      config: { damping: 12 },
      from: 0.8,
      to: 1
  }) : zoomScale;

  const finalScale = transition === "zoom" ? zoomScale : cutScale;

  const textY = spring({
    frame,
    fps,
    config: { damping: 10 },
    from: 50,
    to: 0
  });

  // 4. Camera Shake - cường độ khác nhau theo từng loại chuyển cảnh, tránh cảm giác
  // lặp lại y hệt nhau ở mọi cảnh (cut = giật mạnh nhất, slide = nhẹ vì đã có motion riêng)
  const shakeIntensity = transition === "cut" ? 1 : transition === "zoom" ? 0.5 : 0.25;
  const shakeX = Math.sin(frame * 2.5) * Math.max(0, 15 - frame) * 2 * shakeIntensity;
  const shakeY = Math.cos(frame * 3) * Math.max(0, 15 - frame) * 2 * shakeIntensity;

  return (
    <AbsoluteFill style={{
      transform: `translate(${slideX + shakeX}px, ${shakeY}px)`,
      justifyContent: "center",
      alignItems: "center"
    }}>
      {/* Giọng đọc AI riêng cho cảnh này - khớp tuyệt đối với thời lượng thật của audio */}
      {caption.audioPath && <Audio src={staticFile(caption.audioPath)} />}

      {/* Hiệu ứng âm thanh chuyển cảnh */}
      {caption.sfxPath && <Audio src={staticFile(caption.sfxPath)} volume={0.8} />}

      {/* Hộp khung hình cố định để "cover" crop vào từng góc ảnh có ý nghĩa (giả lập
          nhiều góc máy từ cùng 1 tấm ảnh sản phẩm), thay vì luôn hiện trọn ảnh giống hệt nhau */}
      <div
        style={{
          width: "80%",
          height: "62%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: framing.fit === "cover" ? "hidden" : "visible",
        }}
      >
        <Img
          src={imgUrl.startsWith('http') ? imgUrl : staticFile(imgUrl)}
          style={{
            transform: `scale(${finalScale})`,
            width: framing.fit === "cover" ? "100%" : "auto",
            height: framing.fit === "cover" ? "100%" : "auto",
            maxHeight: framing.fit === "contain" ? "100%" : undefined,
            maxWidth: framing.fit === "contain" ? "100%" : undefined,
            objectFit: framing.fit,
            objectPosition: framing.position,
            filter: framing.fit === "contain" ? "drop-shadow(0px 30px 40px rgba(0,0,0,1))" : "none",
          }}
        />
      </div>

      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          // Chừa khoảng an toàn (safe zone) tránh bị thanh caption/UI của TikTok & Reels che mất
          paddingBottom: "300px",
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "20px",
            padding: "20px",
            maxWidth: "85%",
            transform: `translateY(${textY}px)`,
          }}
        >
          {caption.text.split(" ").map((word: string, i: number) => {
            // Hiệu ứng nhảy chữ từng từ (Hormozi Style)
            const delay = i * 4; // Từ sau hiện chậm hơn từ trước 4 frame
            const wordScale = spring({
              frame: frame - delay,
              fps,
              config: { damping: 12, mass: 0.8 },
            });

            // Highlight màu xen kẽ cực gắt
            const isHighlight = i % 2 !== 0;
            const wordColor = isHighlight
              ? "linear-gradient(to right, #ff0844, #ffb199)" // Đỏ cam cháy
              : "linear-gradient(to right, #00f2fe, #4facfe)"; // Xanh biển sâu

            return (
              <span
                key={i}
                style={{
                  transform: `scale(${wordScale})`,
                  fontSize: "85px",
                  fontWeight: "900",
                  textShadow: "0px 10px 20px rgba(0,0,0,1)",
                  background: wordColor,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  lineHeight: 1.2,
                  display: "inline-block"
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Cảnh CTA/End-card riêng biệt để chốt đơn - không lẫn vào cảnh sản phẩm,
// đây là khung hình quan trọng nhất cho tỷ lệ chuyển đổi nên tách hẳn ra.
const CtaCard: React.FC<{
  caption: Caption;
  imgUrl: string;
  fps: number;
}> = ({ caption, imgUrl, fps }) => {
  const frame = useCurrentFrame();

  const scale = spring({ frame, fps, config: { damping: 12 }, from: 0.7, to: 1 });
  const pulse = 1 + Math.sin(frame / 6) * 0.04; // nhịp đập nhẹ liên tục để hút mắt vào nút CTA
  const arrowBounce = Math.abs(Math.sin(frame / 10)) * 20;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {caption.sfxPath && <Audio src={staticFile(caption.sfxPath)} volume={0.7} />}

      <Img
        src={imgUrl.startsWith("http") ? imgUrl : staticFile(imgUrl)}
        style={{
          position: "absolute",
          opacity: 0.35,
          maxHeight: "70%",
          maxWidth: "90%",
          objectFit: "contain",
          filter: "blur(2px)",
        }}
      />

      <div
        style={{
          transform: `scale(${scale * pulse})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "24px",
          padding: "40px 60px",
          maxWidth: "85%",
          background: "linear-gradient(135deg, #ff0844, #ff6a00)",
          borderRadius: "24px",
          boxShadow: "0px 20px 50px rgba(0,0,0,0.6)",
        }}
      >
        <span style={{ fontSize: "72px", fontWeight: 900, color: "white", textAlign: "center", lineHeight: 1.2 }}>
          {caption.text}
        </span>
        {caption.subtext && (
          <span style={{ fontSize: "36px", fontWeight: 600, color: "white", textAlign: "center" }}>
            {caption.subtext}
          </span>
        )}
      </div>

      <div
        style={{
          position: "absolute",
          bottom: `${260 + arrowBounce}px`,
          fontSize: "60px",
        }}
      >
        👇
      </div>
    </AbsoluteFill>
  );
};
