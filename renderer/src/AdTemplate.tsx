import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  Audio,
  staticFile,
  Sequence
} from "remotion";
import { z } from "zod";

export const adSchema = z.object({
  productImages: z.array(z.string()),
  audioPath: z.string().optional().nullable(),
  bgmPath: z.string().optional().nullable(),
  captions: z.array(
    z.object({
      text: z.string(),
      startFrame: z.number(),
      endFrame: z.number(),
      imageIndex: z.number().optional().default(0),
      transition: z.string().optional().default("cut"),
      sfxPath: z.string().optional(),
    })
  ),
});

export const AdTemplate: React.FC<z.infer<typeof adSchema>> = ({
  productImages,
  audioPath,
  bgmPath,
  captions,
}) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ 
      background: "radial-gradient(circle at center, #333333 0%, #000000 80%)", 
      color: "white" 
    }}>
      {/* Giọng đọc AI */}
      {audioPath && <Audio src={staticFile(audioPath)} />}
      
      {/* Nhạc nền (BGM) âm lượng nhỏ (Auto-ducking giả lập) + Lách bản quyền bằng cách tăng tốc độ 1.15x */}
      {bgmPath && <Audio src={staticFile(bgmPath)} volume={0.25} playbackRate={1.15} />}

      {captions.map((caption, index) => {
        const duration = caption.endFrame - caption.startFrame;
        const imgUrl = productImages[caption.imageIndex || 0] || productImages[0];

        return (
          <Sequence
            key={index}
            from={caption.startFrame}
            durationInFrames={duration}
          >
            <SceneContent
              caption={caption}
              imgUrl={imgUrl}
              fps={fps}
              transition={caption.transition}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneContent: React.FC<{
  caption: any;
  imgUrl: string;
  fps: number;
  transition?: string;
}> = ({ caption, imgUrl, fps, transition }) => {
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

  // 4. Hiệu ứng Camera Shake (Rung lắc mạnh trong 10 frame đầu tiên để tạo độ Impact)
  const shakeX = Math.sin(frame * 2.5) * Math.max(0, 15 - frame) * 2;
  const shakeY = Math.cos(frame * 3) * Math.max(0, 15 - frame) * 2;

  return (
    <AbsoluteFill style={{ 
      transform: `translate(${slideX + shakeX}px, ${shakeY}px)`, 
      justifyContent: "center", 
      alignItems: "center" 
    }}>
      {/* Hiệu ứng âm thanh chuyển cảnh */}
      {caption.sfxPath && <Audio src={staticFile(caption.sfxPath)} volume={0.8} />}

      <Img
        src={imgUrl.startsWith('http') ? imgUrl : staticFile(imgUrl)}
        style={{
          transform: `scale(${finalScale})`,
          maxHeight: "60%",
          maxWidth: "80%",
          objectFit: "contain",
          filter: "drop-shadow(0px 30px 40px rgba(0,0,0,1))"
        }}
      />
      
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          paddingBottom: "150px",
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "20px",
            padding: "20px",
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
