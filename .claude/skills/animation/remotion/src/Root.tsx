import { Composition, CalculateMetadataFunction } from "remotion";
import { MapComposition, MapCompositionProps } from "./MapComposition";

const FPS = 30;
const DEFAULT_DURATION_SECONDS = 8;

const calculateMetadata: CalculateMetadataFunction<MapCompositionProps> = async ({
  props,
}) => {
  const durationSeconds = props.durationSeconds ?? DEFAULT_DURATION_SECONDS;
  return {
    durationInFrames: Math.ceil(durationSeconds * FPS),
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MapComposition"
        component={MapComposition}
        durationInFrames={DEFAULT_DURATION_SECONDS * FPS}
        width={1920}
        height={1080}
        fps={FPS}
        defaultProps={{
          variant: "region-highlight" as const,
          title: "Sample Location",
          locations: [
            { name: "Mexico City", x: 0.35, y: 0.55 },
            { name: "Guadalajara", x: 0.25, y: 0.48 },
          ],
          connections: [],
          durationSeconds: DEFAULT_DURATION_SECONDS,
        }}
        calculateMetadata={calculateMetadata}
      />
    </>
  );
};
