import React from "react";
import { Composition } from "remotion";
import { Short, Cover } from "./Short";
import script from "../script.json";

const total = script.scenes.reduce((n, s) => n + s.frames, 0);

export const Root: React.FC = () => (
  <>
  <Composition
    id="Cover"
    component={Cover as any}
    durationInFrames={1}
    fps={script.fps}
    width={script.width}
    height={script.height}
    defaultProps={{ script }}
  />
  <Composition
    id="Short"
    component={Short}
    durationInFrames={total}
    fps={script.fps}
    width={script.width}
    height={script.height}
    defaultProps={{ script }}
  />
  </>
);
