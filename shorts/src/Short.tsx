import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadVT } from "@remotion/google-fonts/VT323";

const inter = loadInter("normal", { weights: ["700", "900"] });
const vt = loadVT("normal", { weights: ["400"] });

type Scene = { say: string; lines: string[]; kind: string; audio: string; frames: number };
type Script = { fps: number; width: number; height: number; hero: string; title: string; slug: string; scenes: Scene[] };

const GRAY = "#c0c0c0";
const TEAL = "#008080";
const NAVY = "#000080";

const bevel = (inset = false): React.CSSProperties => ({
  borderStyle: "solid",
  borderWidth: 6,
  borderColor: inset ? "#808080 #ffffff #ffffff #808080" : "#ffffff #808080 #808080 #ffffff",
  background: GRAY,
});

const TitleBar: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      background: NAVY,
      color: "#fff",
      fontFamily: vt.fontFamily,
      fontSize: 54,
      padding: "10px 22px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    }}
  >
    <span>{text}</span>
    <span
      style={{
        ...bevel(),
        color: "#000",
        width: 56,
        height: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 44,
        lineHeight: 1,
      }}
    >
      ×
    </span>
  </div>
);

const BigText: React.FC<{ lines: string[]; accent?: boolean }> = ({ lines, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "center" }}>
      {lines.map((l, i) => {
        const s = spring({ frame: frame - i * 6, fps, config: { damping: 14, stiffness: 160 } });
        const big = i === 0 && accent;
        const base = big ? 118 : 84;
        const size = Math.min(base, Math.floor(1380 / Math.max(l.length, 6)));
        return (
          <div
            key={i}
            style={{
              transform: `scale(${0.6 + 0.4 * s}) translateY(${(1 - s) * 30}px)`,
              opacity: s,
              fontFamily: inter.fontFamily,
              fontWeight: big ? 900 : 700,
              fontSize: size,
              lineHeight: 1.05,
              color: big ? "#ffd400" : "#000",
              background: big ? NAVY : "#fff",
              padding: big ? "8px 32px" : "6px 28px",
              textAlign: "center",
              boxShadow: "10px 10px 0 #000",
              letterSpacing: -1,
            }}
          >
            {l}
          </div>
        );
      })}
    </div>
  );
};

const Hero: React.FC<{ src: string; seed: number }> = ({ src, seed }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 200], [1.02, 1.16], { extrapolateRight: "clamp" });
  const dx = interpolate(frame, [0, 200], [0, seed % 2 ? -18 : 18], { extrapolateRight: "clamp" });
  return (
    <div style={{ width: "100%", height: "100%", overflow: "hidden", background: "#000" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${zoom}) translateX(${dx}px)`,
        }}
      />
    </div>
  );
};

const Progress: React.FC<{ total: number; offset: number }> = ({ total, offset }) => {
  const frame = useCurrentFrame() + offset;
  const blocks = 24;
  const filled = Math.round((frame / total) * blocks);
  return (
    <div style={{ ...bevel(true), display: "flex", gap: 6, padding: 8, width: 900 }}>
      {Array.from({ length: blocks }).map((_, i) => (
        <div key={i} style={{ flex: 1, height: 26, background: i < filled ? NAVY : "transparent" }} />
      ))}
    </div>
  );
};

const SceneView: React.FC<{ scene: Scene; script: Script; index: number; offset: number; total: number }> = ({
  scene,
  script,
  index,
  offset,
  total,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const windowIn = spring({ frame, fps, config: { damping: 18, stiffness: 120 } });
  const isHook = scene.kind === "hook";
  const isOutro = scene.kind === "outro";
  return (
    <AbsoluteFill style={{ background: TEAL }}>
      <Audio src={staticFile(scene.audio)} />
      {/* desktop pattern */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      {/* top strip */}
      <div
        style={{
          position: "absolute",
          top: 70,
          left: 60,
          right: 60,
          ...bevel(),
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "10px 18px",
        }}
      >
        <Img src={staticFile("logo.png")} style={{ width: 64, height: 64 }} />
        <span style={{ fontFamily: vt.fontFamily, fontSize: 52, color: "#000" }}>404 Memory Found</span>
        <span style={{ marginLeft: "auto", fontFamily: vt.fontFamily, fontSize: 44, color: "#000" }}>
          {index + 1}/{script.scenes.length}
        </span>
      </div>

      {/* main window */}
      <div
        style={{
          position: "absolute",
          top: 210,
          left: 60,
          right: 60,
          height: 900,
          ...bevel(),
          padding: 8,
          transform: `scale(${0.9 + 0.1 * windowIn})`,
          opacity: windowIn,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <TitleBar text={isOutro ? "404memoryfound.com" : `${script.slug.split("-").slice(0, 3).join("_")}.exe`} />
        <div style={{ flex: 1, ...bevel(true), margin: 6, overflow: "hidden", position: "relative" }}>
          {isOutro ? (
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 40,
                background: "#fff",
              }}
            >
              <Img src={staticFile("logo.png")} style={{ width: 420, height: 420 }} />
              <span style={{ fontFamily: vt.fontFamily, fontSize: 64, color: "#000" }}>the internet you grew up with</span>
            </div>
          ) : (
            <Hero src={script.hero} seed={index} />
          )}
          {isHook && (
            <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,.25)" }} />
          )}
        </div>
      </div>

      {/* caption box */}
      {(
        <div
          style={{
            position: "absolute",
            top: 1180,
            left: 60,
            right: 60,
            display: "flex",
            justifyContent: "center",
            padding: 20,
          }}
        >
          <BigText lines={scene.lines} accent />
        </div>
      )}

      {/* bottom: progress + note */}
      <div
        style={{
          position: "absolute",
          bottom: 90,
          left: 0,
          right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 18,
        }}
      >
        <Progress total={total} offset={offset} />
        <span style={{ fontFamily: vt.fontFamily, fontSize: 40, color: "#fff" }}>
          Sourced. Dated. No invented numbers.
        </span>
      </div>
    </AbsoluteFill>
  );
};

export const Short: React.FC<{ script: Script }> = ({ script }) => {
  const total = script.scenes.reduce((n, s) => n + s.frames, 0);
  let offset = 0;
  return (
    <AbsoluteFill>
      {script.scenes.map((scene, i) => {
        const from = offset;
        offset += scene.frames;
        return (
          <Sequence key={i} from={from} durationInFrames={scene.frames}>
            <SceneView scene={scene} script={script} index={i} offset={from} total={total} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
