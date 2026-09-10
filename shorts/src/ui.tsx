import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadVT } from "@remotion/google-fonts/VT323";

export const inter = loadInter("normal", { weights: ["700", "900"] });
export const vt = loadVT("normal", { weights: ["400"] });

export const GRAY = "#c0c0c0";
export const TEAL = "#008080";
export const NAVY = "#000080";
export const YELLOW = "#ffd400";

export const bevel = (inset = false): React.CSSProperties => ({
  borderStyle: "solid",
  borderWidth: 6,
  borderColor: inset ? "#808080 #ffffff #ffffff #808080" : "#ffffff #808080 #808080 #ffffff",
  background: GRAY,
});

export const pixel: React.CSSProperties = { fontFamily: vt.fontFamily, color: "#000" };

export const TitleBar: React.FC<{ text: string; small?: boolean }> = ({ text, small }) => (
  <div
    style={{
      background: NAVY,
      color: "#fff",
      fontFamily: vt.fontFamily,
      fontSize: small ? 40 : 54,
      padding: small ? "6px 16px" : "10px 22px",
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
        width: small ? 44 : 56,
        height: small ? 40 : 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: small ? 34 : 44,
        lineHeight: 1,
      }}
    >
      ×
    </span>
  </div>
);

export const Win: React.FC<{ title: string; style?: React.CSSProperties; small?: boolean; children: React.ReactNode }> = ({
  title,
  style,
  small,
  children,
}) => (
  <div style={{ ...bevel(), padding: 8, display: "flex", flexDirection: "column", ...style }}>
    <TitleBar text={title} small={small} />
    <div style={{ flex: 1, ...bevel(true), margin: 6, overflow: "hidden", position: "relative", background: "#fff" }}>
      {children}
    </div>
  </div>
);

export const Scanlines: React.FC<{ strength?: number }> = ({ strength = 0.12 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      backgroundImage: `repeating-linear-gradient(0deg, rgba(0,0,0,${strength}) 0px, rgba(0,0,0,${strength}) 2px, transparent 2px, transparent 5px)`,
    }}
  />
);

export const KenBurns: React.FC<{ src: string; seed: number; dim?: number; pos?: string }> = ({ src, seed, dim = 0, pos = "center 35%" }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 220], [1.02, 1.18], { extrapolateRight: "clamp" });
  const dx = interpolate(frame, [0, 220], [0, seed % 2 ? -24 : 24], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: pos, transform: `scale(${zoom}) translateX(${dx}px)` }} />
      {dim > 0 && <div style={{ position: "absolute", inset: 0, background: `rgba(0,0,0,${dim})` }} />}
    </div>
  );
};

/** Win95 arrow cursor that glides to a point and clicks */
export const Cursor: React.FC<{ from: [number, number]; to: [number, number]; at: number; clickAt?: number }> = ({ from, to, at, clickAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = spring({ frame: frame - at, fps, config: { damping: 20, stiffness: 60 } });
  const x = from[0] + (to[0] - from[0]) * t;
  const y = from[1] + (to[1] - from[1]) * t;
  const click = clickAt !== undefined && frame >= clickAt && frame < clickAt + 6;
  return (
    <svg style={{ position: "absolute", left: x, top: y, width: 54, height: 72, transform: click ? "scale(0.85)" : "none" }} viewBox="0 0 18 24">
      <path d="M1 1 L1 19 L6 14 L9 22 L12 21 L9 13 L16 13 Z" fill="#fff" stroke="#000" strokeWidth="1.4" />
    </svg>
  );
};

/** Classic Win95 push button */
export const Button: React.FC<{ label: string; pressed?: boolean; style?: React.CSSProperties }> = ({ label, pressed, style }) => (
  <span style={{ ...bevel(!!pressed), ...pixel, fontSize: 40, padding: "6px 34px", display: "inline-block", ...style }}>{label}</span>
);
