import "./index.css";
import { Composition } from "remotion";
import { HelloWorld, myCompSchema } from "./HelloWorld";
import { Logo, myCompSchema2 } from "./HelloWorld/Logo";
import { AdTemplate, adSchema } from "./AdTemplate";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        // You can take the "id" to render a video:
        // npx remotion render HelloWorld
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        // You can override these props for each render:
        // https://www.remotion.dev/docs/parametrized-rendering
        schema={myCompSchema}
        defaultProps={{
          titleText: "Welcome to Remotion",
          titleColor: "#000000",
          logoColor1: "#91EAE4",
          logoColor2: "#86A8E7",
        }}
      />

      {/* Mount any React component to make it show up in the sidebar and work on it individually! */}
      <Composition
        id="OnlyLogo"
        component={Logo}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        schema={myCompSchema2}
        defaultProps={{
          logoColor1: "#91dAE2" as const,
          logoColor2: "#86A8E7" as const,
        }}
      />

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
