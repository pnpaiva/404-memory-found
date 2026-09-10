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
type Script = {
  fps: number;
  width: number;
  height: number;
  hero: string;
  hero2?: string;
  title: string;
  slug: string;
  scenes: Scene[];
  chart: { label: string; value: number; text: string }[];
  props: [string, string][];
  timeline: [string, string][];
};

const GRAY = "#c0c0c0";
const TEAL = "#008080";
const NAVY = "#000080";
const YELLOW = "#ffd400";

const bevel = (inset = false): React.CSSProperties => ({
  borderStyle: "solid",
  borderWidth: 6,
  borderColor: inset ? "#808080 #ffffff #ffffff #808080" : "#ffffff #808080 #808080 #ffffff",
  background: GRAY,
});

const pixel: React.CSSProperties = { fontFamily: vt.fontFamily, color: "#000" };

/* ---------- reusable chrome ---------- */

const TitleBar: React.FC<{ text: string; small?: boolean }> = ({ text, small }) => (
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

const Win: React.FC<{ title: string; style?: React.CSSProperties; small?: boolean; children: React.ReactNode }> = ({
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

const BigText: React.FC<{ lines: string[]; accent?: boolean; delay?: number }> = ({ lines, accent, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "center" }}>
      {lines.map((l, i) => {
        const s = spring({ frame: frame - delay - i * 6, fps, config: { damping: 14, stiffness: 160 } });
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
              color: big ? YELLOW : "#000",
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

/* ---------- effects ---------- */

const Scanlines: React.FC<{ strength?: number }> = ({ strength = 0.12 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      backgroundImage: `repeating-linear-gradient(0deg, rgba(0,0,0,${strength}) 0px, rgba(0,0,0,${strength}) 2px, transparent 2px, transparent 5px)`,
    }}
  />
);

/** VHS look: RGB split that jitters, a tracking bar rolling down, PLAY OSD */
const VhsPhoto: React.FC<{ src: string }> = ({ src }) => {
  const frame = useCurrentFrame();
  const jitter = Math.sin(frame * 1.7) * 4 + (frame % 23 === 0 ? 14 : 0);
  const zoom = interpolate(frame, [0, 120], [1.05, 1.14], { extrapolateRight: "clamp" });
  const bar = ((frame * 9) % 1400) - 200;
  const img: React.CSSProperties = { position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" };
  return (
    <div style={{ position: "absolute", inset: 0, background: "#000", overflow: "hidden" }}>
      <Img src={staticFile(src)} style={{ ...img, transform: `scale(${zoom})`, filter: "contrast(1.1) saturate(1.2)" }} />
      <Img src={staticFile(src)} style={{ ...img, transform: `translateX(${jitter}px) scale(${zoom})`, mixBlendMode: "screen", opacity: 0.35, filter: "sepia(1) hue-rotate(-50deg) saturate(6)" }} />
      <Img src={staticFile(src)} style={{ ...img, transform: `translateX(${-jitter}px) scale(${zoom})`, mixBlendMode: "screen", opacity: 0.35, filter: "sepia(1) hue-rotate(140deg) saturate(6)" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: bar, height: 46, background: "rgba(255,255,255,.35)", filter: "blur(2px)" }} />
      <Scanlines strength={0.22} />
      <div style={{ position: "absolute", top: 26, left: 30, fontFamily: vt.fontFamily, fontSize: 64, color: "#fff", textShadow: "3px 3px 0 #000" }}>
        ▶ PLAY
      </div>
      <div style={{ position: "absolute", top: 26, right: 30, fontFamily: vt.fontFamily, fontSize: 56, color: "#fff", textShadow: "3px 3px 0 #000" }}>
        SP 0:{String(Math.floor(frame / 30)).padStart(2, "0")}:{String(frame % 30).padStart(2, "0")}
      </div>
    </div>
  );
};

const KenBurns: React.FC<{ src: string; seed: number; dim?: number }> = ({ src, seed, dim = 0 }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 220], [1.02, 1.18], { extrapolateRight: "clamp" });
  const dx = interpolate(frame, [0, 220], [0, seed % 2 ? -24 : 24], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom}) translateX(${dx}px)` }} />
      {dim > 0 && <div style={{ position: "absolute", inset: 0, background: `rgba(0,0,0,${dim})` }} />}
    </div>
  );
};

/** Win95 arrow cursor that glides to a point and clicks */
const Cursor: React.FC<{ from: [number, number]; to: [number, number]; at: number; clickAt?: number }> = ({ from, to, at, clickAt }) => {
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

/* ---------- scene bodies ---------- */

/** Scene 2: search dialog counts down from 9,000 to 1, then reveals the Bend store */
const FoundScene: React.FC<{ script: Script }> = ({ script }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const count = Math.round(interpolate(frame, [8, 60], [9000, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const reveal = spring({ frame: frame - 62, fps, config: { damping: 16, stiffness: 120 } });
  const dots = ".".repeat((Math.floor(frame / 8) % 3) + 1);
  const bars = Math.round(interpolate(frame, [8, 60], [0, 30], { extrapolateRight: "clamp", extrapolateLeft: "clamp" }));
  return (
    <>
      <KenBurns src={script.hero} seed={1} dim={interpolate(reveal, [0, 1], [0.7, 0.05])} />
      <div style={{ position: "absolute", left: 40, right: 40, top: 60, opacity: 1 - reveal * 0.1, transform: `translateY(${(1 - Math.min(1, frame / 10)) * -40}px)` }}>
        <Win title="Find: Blockbuster stores" small>
          <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ ...pixel, fontSize: 44 }}>Searching worldwide{dots}</div>
            <div style={{ ...bevel(true), padding: 6, display: "flex", gap: 4 }}>
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} style={{ flex: 1, height: 22, background: i < bars ? NAVY : "transparent" }} />
              ))}
            </div>
            <div style={{ ...pixel, fontSize: 60 }}>
              Stores found: <span style={{ color: count === 1 ? "#008000" : "#c00000", fontWeight: 700 }}>{count.toLocaleString("en-US")}</span>
            </div>
            {reveal > 0.05 && (
              <div style={{ ...pixel, fontSize: 46, transform: `scale(${reveal})`, transformOrigin: "left" }}>
                ▶ 211 NE Revere Ave, Bend, Oregon
              </div>
            )}
          </div>
        </Win>
      </div>
      <Cursor from={[880, 900]} to={[520, 560]} at={40} clickAt={62} />
    </>
  );
};

/** Scene 3: bar chart grows bar by bar with counting labels */
const ChartScene: React.FC<{ script: Script }> = ({ script }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const max = Math.max(...script.chart.map((c) => c.value));
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff", padding: "34px 50px 30px" }}>
      <div style={{ ...pixel, fontSize: 44, marginBottom: 10 }}>Blockbuster stores worldwide</div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 40, height: 560, borderLeft: "5px solid #000", borderBottom: "5px solid #000", padding: "0 30px" }}>
        {script.chart.map((c, i) => {
          const grow = spring({ frame: frame - 10 - i * 22, fps, config: { damping: 14, stiffness: 90 } });
          const h = Math.max(12, (c.value / max) * 520 * grow);
          const shown = Math.round(c.value * Math.min(1, grow));
          const done = grow > 0.95;
          return (
            <div key={c.label} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%" }}>
              <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 60, color: i === 0 ? NAVY : "#c00000", marginBottom: 8, opacity: grow }}>
                {done ? c.text : shown.toLocaleString("en-US")}
              </div>
              <div style={{ width: "100%", height: h, background: i === 0 ? NAVY : "#c00000", borderTop: `6px solid ${YELLOW}`, boxShadow: "8px 8px 0 #000" }} />
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 40, padding: "12px 30px 0" }}>
        {script.chart.map((c) => (
          <div key={c.label} style={{ flex: 1, textAlign: "center", ...pixel, fontSize: 48 }}>
            {c.label}
          </div>
        ))}
      </div>
      <Scanlines strength={0.05} />
    </div>
  );
};

/** Scene 4: properties dialog typed line by line, price ticks up */
const PropsScene: React.FC<{ script: Script }> = ({ script }) => {
  const frame = useCurrentFrame();
  const price = Math.round(interpolate(frame, [30, 90], [0, 320], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return (
    <>
      <KenBurns src={script.hero} seed={2} dim={0.55} />
      <div style={{ position: "absolute", left: 40, right: 40, top: 30 }}>
        <Win title="blockbuster.brand Properties" small>
          <div style={{ padding: "22px 26px", display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", gap: 14, alignItems: "center", marginBottom: 4 }}>
              <div style={{ width: 70, height: 70, background: YELLOW, border: "4px solid #000", display: "flex", alignItems: "center", justifyContent: "center", ...pixel, fontSize: 44 }}>B</div>
              <div style={{ ...pixel, fontSize: 46 }}>Blockbuster LLC</div>
            </div>
            <div style={{ height: 4, background: "#808080" }} />
            {script.props.map(([k, v], i) => {
              const start = 12 + i * 16;
              const chars = Math.max(0, Math.floor((frame - start) * 1.6));
              const text = v.slice(0, chars);
              const caret = frame >= start && chars < v.length ? "_" : "";
              return (
                <div key={k} style={{ display: "flex", gap: 20, ...pixel, fontSize: 46, opacity: frame >= start ? 1 : 0.25 }}>
                  <span style={{ width: 200, color: "#555" }}>{k}:</span>
                  <span>{text}{caret}</span>
                </div>
              );
            })}
            <div style={{ marginTop: 6, display: "flex", justifyContent: "center" }}>
              <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 110, color: NAVY, letterSpacing: -2 }}>${price}M</div>
            </div>
          </div>
        </Win>
      </div>
    </>
  );
};

/** Scene 5: timeline lights up dot by dot over the Alaska sign photo */
const TimelineScene: React.FC<{ script: Script }> = ({ script }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = script.timeline.length;
  return (
    <>
      <KenBurns src={script.hero2 || script.hero} seed={3} dim={0.62} />
      <div style={{ position: "absolute", left: 87, top: 90, bottom: 90, width: 6, background: "#fff" }} />
      <div style={{ position: "absolute", left: 70, right: 70, top: 50, bottom: 40, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        {script.timeline.map(([year, label], i) => {
          const s = spring({ frame: frame - 8 - i * 20, fps, config: { damping: 15, stiffness: 140 } });
          const last = i === n - 1;
          return (
            <div key={year} style={{ display: "flex", alignItems: "center", gap: 24, opacity: 0.25 + 0.75 * s, transform: `translateX(${(1 - s) * -40}px)` }}>
              <div style={{ width: 40, height: 40, borderRadius: 20, background: last ? YELLOW : "#fff", border: "5px solid #000", flexShrink: 0, transform: `scale(${0.6 + 0.6 * s})` }} />
              <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 64, color: YELLOW, textShadow: "4px 4px 0 #000", width: 180 }}>{year}</div>
              <div style={{ fontFamily: inter.fontFamily, fontWeight: 700, fontSize: 42, color: "#fff", background: last ? NAVY : "rgba(0,0,0,.7)", padding: "6px 16px", boxShadow: "6px 6px 0 #000" }}>{label}</div>
            </div>
          );
        })}
      </div>
    </>
  );
};

/** Scene 6: Start menu slides up, the cursor clicks Follow, then the CRT switches off */
const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const menu = spring({ frame: frame - 6, fps, config: { damping: 16, stiffness: 120 } });
  const items = ["Programs", "Documents", "Settings", "Find", "Help", "Run...", "Follow 404 Memory Found"];
  return (
    <div style={{ position: "absolute", inset: 0, background: TEAL, overflow: "hidden" }}>
      <div style={{ position: "absolute", right: 40, top: 20, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, width: 300 }}>
        <Img src={staticFile("logo.png")} style={{ width: 120, height: 120 }} />
        <div style={{ fontFamily: vt.fontFamily, fontSize: 38, color: "#fff", textAlign: "center", textShadow: "2px 2px 0 #000" }}>404memoryfound.com</div>
      </div>
      <div style={{ position: "absolute", left: 30, bottom: 100, width: 620, ...bevel(), transform: `translateY(${(1 - menu) * 700}px)`, display: "flex" }}>
        <div style={{ width: 64, background: NAVY, color: "#fff", writingMode: "vertical-rl", transform: "rotate(180deg)", fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 38, display: "flex", alignItems: "center", justifyContent: "center", padding: 10 }}>
          404 Memory Found
        </div>
        <div style={{ flex: 1, padding: 8 }}>
          {items.map((it, i) => {
            const hot = i === items.length - 1 && frame > 40;
            return (
              <div key={it} style={{ ...pixel, fontSize: 44, padding: "12px 16px", background: hot ? NAVY : "transparent", color: hot ? "#fff" : "#000", borderTop: i === items.length - 1 ? "3px solid #808080" : "none" }}>
                {it}
              </div>
            );
          })}
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 90, ...bevel(), display: "flex", alignItems: "center", padding: "0 16px", gap: 14 }}>
        <div style={{ ...bevel(), padding: "6px 20px", ...pixel, fontSize: 44, background: frame > 40 ? "#a0a0a0" : GRAY }}>▣ Start</div>
        <div style={{ marginLeft: "auto", ...bevel(true), padding: "6px 16px", ...pixel, fontSize: 40 }}>2026</div>
      </div>
      <Cursor from={[700, 300]} to={[330, 650]} at={10} clickAt={40} />
    </div>
  );
};

/* ---------- scene frame ---------- */

const TITLES: Record<string, string> = {
  hook: "blockbuster.avi",
  found: "find.exe",
  chart: "stores.xls",
  props: "properties",
  timeline: "history.txt",
  outro: "404memoryfound.com",
};

const SceneView: React.FC<{ scene: Scene; script: Script; index: number; offset: number; total: number }> = ({ scene, script, index, offset, total }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const windowIn = spring({ frame, fps, config: { damping: 18, stiffness: 120 } });
  const kind = scene.kind;
  const body =
    kind === "hook" ? <VhsPhoto src={script.hero} /> :
    kind === "found" ? <FoundScene script={script} /> :
    kind === "chart" ? <ChartScene script={script} /> :
    kind === "props" ? <PropsScene script={script} /> :
    kind === "timeline" ? <TimelineScene script={script} /> :
    <OutroScene />;

  // CRT power-off in the last frames of the outro
  const off = kind === "outro"
    ? interpolate(frame, [scene.frames - 14, scene.frames - 2], [1, 0.01], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 1;

  return (
    <AbsoluteFill style={{ background: TEAL }}>
      <Audio src={staticFile(scene.audio)} />
      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />

      <div style={{ position: "absolute", top: 70, left: 60, right: 60, ...bevel(), display: "flex", alignItems: "center", gap: 18, padding: "10px 18px" }}>
        <Img src={staticFile("logo.png")} style={{ width: 64, height: 64 }} />
        <span style={{ ...pixel, fontSize: 52 }}>404 Memory Found</span>
        <span style={{ marginLeft: "auto", ...pixel, fontSize: 44 }}>{index + 1}/{script.scenes.length}</span>
      </div>

      <div style={{ position: "absolute", top: 210, left: 60, right: 60, height: 900, transform: `scale(${0.9 + 0.1 * windowIn}) scaleY(${off})`, opacity: windowIn }}>
        <Win title={TITLES[kind] || "window"} style={{ height: "100%" }}>{body}</Win>
      </div>

      <div style={{ position: "absolute", top: 1180, left: 60, right: 60, display: "flex", justifyContent: "center", padding: 20 }}>
        <BigText lines={scene.lines} accent delay={kind === "found" ? 62 : 0} />
      </div>

      <div style={{ position: "absolute", bottom: 90, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
        <div style={{ ...bevel(true), display: "flex", gap: 6, padding: 8, width: 900 }}>
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} style={{ flex: 1, height: 26, background: i < Math.round(((frame + offset) / total) * 24) ? NAVY : "transparent" }} />
          ))}
        </div>
        <span style={{ fontFamily: vt.fontFamily, fontSize: 40, color: "#fff" }}>Sourced. Dated. No invented numbers.</span>
      </div>
      <Scanlines strength={0.04} />
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
