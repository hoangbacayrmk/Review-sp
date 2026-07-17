import "./index.css";
import { Composition } from "remotion";
import { AdTemplate, adSchema } from "./AdTemplate";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AutoAd"
        component={AdTemplate}
        durationInFrames={450} // Tạm mặc định 15 giây
        fps={30}
        width={1080} // Dọc cho Reels/TikTok
        height={1920}
        schema={adSchema}
        calculateMetadata={({ props }) => {
          const lastCaption = props.captions?.[props.captions.length - 1];
          return {
            durationInFrames: lastCaption ? lastCaption.endFrame : 450,
          };
        }}
        defaultProps={{
          productImages: [
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1524592094714-0f0654e20314?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1524805444758-089113d48a6d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
          ],
          bgmPath: null,
          captions: [
            { text: "SẢN PHẨM MỚI", startFrame: 0, endFrame: 45, imageIndex: 0, transition: "zoom", isCta: false },
            { text: "SIÊU GIẢM GIÁ 50%", startFrame: 45, endFrame: 90, imageIndex: 1, transition: "cut", isCta: false },
            { text: "MUA NGAY HÔM NAY", startFrame: 90, endFrame: 150, imageIndex: 2, transition: "slide", isCta: false },
            {
              text: "MUA NGAY HÔM NAY",
              subtext: "Link sản phẩm ở phần bình luận 👇",
              startFrame: 150,
              endFrame: 240,
              imageIndex: 2,
              transition: "cut",
              isCta: true,
            },
          ],
        }}
      />
    </>
  );
};
