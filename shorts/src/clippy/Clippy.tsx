import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame } from "remotion";
import { GRAY, TEAL, NAVY, YELLOW, bevel, pixel, inter, vt, Win, Scanlines, Cursor } from "../ui";
import vo from "../../scripts/clippy-vo.json";

/* Clippy at 30. Voice: Pedro's recording, cut and aligned by vo_cut.py (scripts/clippy-vo.json).
   33 shots, one every 1.7 s on average, each starting on a word of the voiceover and entering in a
   different way. Every fact on screen is in the post. */

export const FPS = 30;
export const END_CARD = 1.6;
export const CLIPPY_FRAMES = Math.ceil((vo.duration + END_CARD) * FPS);

type W = { w: string; s: number; e: number };
const words = vo.words as W[];
const D = vo.duration;

type Entr = "cut" | "slideL" | "slideR" | "slideUp" | "slideDown" | "zoomIn" | "zoomOut" | "wipeL" | "wipeR" | "iris" | "rotIn" | "flip";
const SHOTS: { id: string; s: number; title: string; in: Entr }[] = [
  { id: "hook", s: 0, title: "clippit.exe", in: "cut" },
  { id: "lab", s: 2.3, title: "focus_lab.avi", in: "wipeR" },
  { id: "crowd", s: 4.45, title: "users.exe", in: "zoomOut" },
  { id: "off", s: 7.15, title: "Options", in: "slideL" },
  { id: "pause", s: 8.45, title: "PAUSED", in: "cut" },
  { id: "stanford", s: 12.75, title: "stanford.txt", in: "iris" },
  { id: "hands", s: 14.05, title: "media_equation.avi", in: "slideUp" },
  { id: "face", s: 15.95, title: "office.exe", in: "zoomIn" },
  { id: "cast", s: 18.6, title: "characters.bmp", in: "flip" },
  { id: "winner", s: 21.9, title: "winner.bmp", in: "zoomIn" },
  { id: "mac", s: 24.35, title: "Macintosh HD", in: "slideDown" },
  { id: "setup", s: 26.3, title: "Office 97 Setup", in: "slideR" },
  { id: "everyone", s: 28.1, title: "network.exe", in: "cut" },
  { id: "letter", s: 29.0, title: "Document1 - Microsoft Word", in: "wipeL" },
  { id: "minutes", s: 32.62, title: "focus_group.xls", in: "rotIn" },
  { id: "years", s: 34.92, title: "calendar.exe", in: "slideL" },
  { id: "slam", s: 37.4, title: "2001", in: "cut" },
  { id: "memo", s: 39.45, title: "memo.doc", in: "slideUp" },
  { id: "curtains", s: 40.45, title: "office_xp_launch.avi", in: "cut" },
  { id: "suit", s: 41.35, title: "office_xp_launch.avi", in: "zoomIn" },
  { id: "beg", s: 43.45, title: "office_xp_launch.avi", in: "cut" },
  { id: "magnet", s: 44.8, title: "office_xp_launch.avi", in: "slideDown" },
  { id: "drag", s: 45.85, title: "office_xp_launch.avi", in: "cut" },
  { id: "thirty", s: 46.85, title: "birthday.exe", in: "iris" },
  { id: "photo", s: 48.92, title: "My Pictures", in: "rotIn" },
  { id: "emoji", s: 50.25, title: "Emoji", in: "slideR" },
  { id: "copilot", s: 51.1, title: "Copilot", in: "slideUp" },
  { id: "tap", s: 52.72, title: "Copilot", in: "zoomOut" },
  { id: "back", s: 55.9, title: "clippit.exe", in: "cut" },
  { id: "end", s: D, title: "404memoryfound.com", in: "zoomIn" },
];

const SHAKES = [1.2, 38.86, 39.98, 45.9];

const SFX: [number, string, number][] = [
  [0.0, "crt_on", 0.5], [0.3, "pop", 0.6], [1.2, "thud", 0.75],
  [2.3, "whoosh", 0.3], [4.45, "whoosh", 0.3], [7.84, "click", 0.7], [8.45, "tapestop", 0.55],
  [12.75, "crt_on", 0.3], [14.05, "whoosh", 0.25], [15.95, "whoosh", 0.25], [18.16, "chord", 0.35],
  [18.6, "whoosh", 0.3], [20.6, "tick", 0.5], [21.9, "whoosh_long", 0.35], [23.12, "ding", 0.45],
  [24.35, "whoosh", 0.3], [24.9, "chord", 0.3],
  [26.3, "whoosh", 0.3], [28.1, "thud", 0.5],
  [29.0, "whoosh", 0.25], [29.16, "pop", 0.65],
  [32.62, "whoosh", 0.3], [34.92, "whoosh", 0.3],
  [37.2, "riser", 0.35], [38.86, "bassdrop", 0.6], [39.45, "whoosh", 0.25], [39.98, "thud", 0.85],
  [40.5, "whoosh_long", 0.45], [40.9, "clunk", 0.6], [41.35, "whoosh", 0.2], [44.8, "hum", 0.45], [45.9, "zap", 0.5], [45.95, "whoosh", 0.45], [46.4, "thud", 0.35],
  [46.85, "whoosh", 0.3], [48.08, "sparkle", 0.5], [48.1, "ding", 0.3],
  [48.92, "whoosh", 0.3], [50.32, "pop", 0.45], [51.16, "pop", 0.4], [52.72, "whoosh", 0.25],
  [55.98, "sparkle", 0.55], [56.0, "pop", 0.5],
  [D, "chord", 0.3], [D + END_CARD - 0.55, "crt_off", 0.5],
];
for (let i = 0; i < 14; i++) SFX.push([5.5 + i * 0.09, "click", 0.16]);
for (let i = 0; i < 8; i++) SFX.push([26.45 + i * 0.18, "tick", 0.22]);
for (let i = 0; i < 4; i++) SFX.push([28.6 + i * 0.1, "key", 0.4]);
for (let i = 0; i < 7; i++) SFX.push([32.8 + i * 0.25, "tick", 0.25]);
[35.0, 35.45, 35.8, 36.1, 36.32, 36.5, 36.65, 36.78].forEach((s) => SFX.push([s, "pop", 0.32]));
for (let i = 0; i < 12; i++) SFX.push([53.0 + i * 0.21, "click", 0.45]);

/* ---------------- helpers ---------------- */

const useT = () => useCurrentFrame() / FPS;
const sp = (frame: number, at: number, damping = 13, stiffness = 170) =>
  spring({ frame: frame - Math.round(at * FPS), fps: FPS, config: { damping, stiffness } });
const lin = (t: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(t, [a, b], [from, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
const shotAt = (t: number) => {
  let cur = SHOTS[0];
  for (const s of SHOTS) if (t >= s.s) cur = s;
  return cur;
};

const KEY = /^(six|fired|Mac|everyone|years|minutes|30|250|97|2001|back|face|trust|stage|magnet|off|millions|psychologists|dozen|emoji|Copilot|letter|help)$/i;
const PUNCH = words.filter((w) => KEY.test(w.w.replace(/[.,?!]/g, ""))).map((w) => w.s);

const entrance = (kind: Entr, f: number): React.CSSProperties => {
  const s = spring({ frame: f, fps: FPS, config: { damping: 14, stiffness: 190 } });
  const k = spring({ frame: f, fps: FPS, config: { damping: 11, stiffness: 230 } });
  switch (kind) {
    case "slideL": return { transform: `translateX(${(1 - k) * -1000}px)` };
    case "slideR": return { transform: `translateX(${(1 - k) * 1000}px)` };
    case "slideUp": return { transform: `translateY(${(1 - k) * 900}px)` };
    case "slideDown": return { transform: `translateY(${(1 - k) * -900}px)` };
    case "zoomIn": return { transform: `scale(${0.3 + 0.7 * s})`, opacity: Math.min(1, s * 2) };
    case "zoomOut": return { transform: `scale(${2.2 - 1.2 * s})`, opacity: Math.min(1, s * 2) };
    case "wipeL": return { clipPath: `inset(0 0 0 ${(1 - s) * 100}%)` };
    case "wipeR": return { clipPath: `inset(0 ${(1 - s) * 100}% 0 0)` };
    case "iris": return { clipPath: `circle(${s * 75}% at 50% 50%)` };
    case "rotIn": return { transform: `rotate(${(1 - k) * -14}deg) scale(${0.6 + 0.4 * k})`, opacity: Math.min(1, k * 2) };
    case "flip": return { transform: `perspective(1400px) rotateY(${(1 - s) * 85}deg)`, transformOrigin: "left center" };
    default: return {};
  }
};

/** The paperclip, drawn from scratch: wire, highlight, googly eyes, eyebrows. */
const Clip: React.FC<{ size: number; look?: number; brow?: number; blink?: boolean; hat?: boolean; style?: React.CSSProperties }> = ({
  size, look = 0, brow = 0, blink, hat, style,
}) => {
  const wire = "M 40 122 L 40 44 A 13 13 0 0 1 66 44 L 66 134 A 22 22 0 0 1 22 134 L 22 30 A 31 31 0 0 1 84 30 L 84 112";
  return (
    <svg viewBox="0 0 106 170" style={{ width: size, height: size * 1.6, overflow: "visible", ...style }}>
      {hat && <polygon points="40,-34 66,-34 53,-78" fill="#ff3b6b" stroke="#000" strokeWidth={2.5} />}
      <path d={wire} fill="none" stroke="#5d6670" strokeWidth={11} strokeLinecap="round" strokeLinejoin="round" />
      <path d={wire} fill="none" stroke="#b7c0ca" strokeWidth={6.5} strokeLinecap="round" strokeLinejoin="round" />
      <path d={wire} fill="none" stroke="#f1f4f7" strokeWidth={2} strokeLinecap="round" transform="translate(-1.2,-1.2)" />
      {[34, 70].map((cx, i) => (
        <g key={i}>
          <path d={`M ${cx - 12} ${33 - brow * 7} Q ${cx} ${23 - brow * 9} ${cx + 12} ${33 - brow * 7}`} fill="none" stroke="#000" strokeWidth={3.5} strokeLinecap="round" />
          <ellipse cx={cx} cy={50} rx={13} ry={blink ? 1.5 : 14} fill="#fff" stroke="#000" strokeWidth={2.5} />
          {!blink && <circle cx={cx + look * 5} cy={52} r={5.5} fill="#000" />}
        </g>
      ))}
    </svg>
  );
};

const Balloon: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; tail?: "left" | "right" }> = ({ children, style, tail = "right" }) => (
  <div style={{ position: "absolute", background: "#ffffe1", border: "4px solid #000", borderRadius: 26, padding: "22px 28px", boxShadow: "8px 8px 0 rgba(0,0,0,.35)", ...style }}>
    {children}
    <div style={{ position: "absolute", bottom: -34, [tail]: 60, width: 0, height: 0, borderLeft: "22px solid transparent", borderRight: "22px solid transparent", borderTop: "34px solid #000" } as React.CSSProperties} />
    <div style={{ position: "absolute", bottom: -27, [tail]: 64, width: 0, height: 0, borderLeft: "18px solid transparent", borderRight: "18px solid transparent", borderTop: "29px solid #ffffe1" } as React.CSSProperties} />
  </div>
);

const Stamp: React.FC<{ text: string; at: number; color?: string; size?: number; rot?: number; style?: React.CSSProperties }> = ({ text, at, color = "#d40000", size = 150, rot = -12, style }) => {
  const frame = useCurrentFrame();
  if (frame / FPS < at) return null;
  const s = sp(frame, at, 9, 260);
  return (
    <div style={{ position: "absolute", left: "50%", top: "50%", transform: `translate(-50%,-50%) rotate(${rot}deg) scale(${1 + 2 * Math.max(-0.05, 1 - s)})`, opacity: Math.min(1, s * 1.4), ...style }}>
      <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: size, color, border: `12px solid ${color}`, padding: "4px 30px", letterSpacing: 4, background: "rgba(255,255,255,.15)", whiteSpace: "nowrap" }}>{text}</span>
    </div>
  );
};

const Typed: React.FC<{ text: string; from: number; cps?: number; style?: React.CSSProperties }> = ({ text, from, cps = 28, style }) => {
  const t = useT();
  if (t < from) return null;
  const n = Math.max(0, Math.floor((t - from) * cps));
  return <span style={style}>{text.slice(0, n)}{n < text.length && Math.floor(t * 4) % 2 ? "_" : ""}</span>;
};

const Label: React.FC<{ text: string; at: number; style?: React.CSSProperties; bg?: string; fg?: string; size?: number; wrap?: boolean }> = ({ text, at, style, bg = NAVY, fg = YELLOW, size = 64, wrap }) => {
  const frame = useCurrentFrame();
  if (frame / FPS < at) return null;
  const s = sp(frame, at, 11, 220);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${s})`, ...style }}>
      <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: size, background: bg, color: fg, padding: "6px 24px", boxShadow: "8px 8px 0 #000", whiteSpace: wrap ? "normal" : "nowrap", maxWidth: 860, textAlign: "center", lineHeight: 1.15 }}>{text}</span>
    </div>
  );
};

/* ---------------- shots ---------------- */

const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const inn = sp(frame, 0.3, 9, 220);
  const head = sp(frame, 0.05, 14, 200);
  return (
    <AbsoluteFill style={{ background: "#fff" }}>
      <div style={{ position: "absolute", left: 60, top: 40, right: 60, bottom: 40, border: "2px solid #ccc" }}>
        <div style={{ position: "absolute", left: 50, top: 300, width: 4, height: 54, background: "#000", opacity: Math.floor(t * 2.2) % 2 }} />
      </div>
      <div style={{ position: "absolute", top: 44, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 12, transform: `translateY(${(1 - head) * -260}px)` }}>
        {["MICROSOFT FIRED HIM.", "ON STAGE."].map((l, i) => (
          <span key={i} style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: i ? 96 : 82, color: i ? YELLOW : "#fff", background: i ? "#d40000" : NAVY, padding: "6px 26px", boxShadow: "10px 10px 0 #000", transform: `rotate(${i ? 1.5 : -1.5}deg)` }}>{l}</span>
        ))}
        <span style={{ ...pixel, fontSize: 46, color: "#333", marginTop: 6 }}>30 years ago this week</span>
      </div>
      <div style={{ position: "absolute", left: 400, top: 395, transform: `scale(${inn}) rotate(${(1 - inn) * -25}deg)`, transformOrigin: "50% 100%" }}>
        <Clip size={190} look={Math.sin(t * 2.2)} brow={t > 0.5 && t < 1.2 ? 1 : 0} />
      </div>
      <Stamp text="FIRED" at={1.2} size={150} style={{ top: "74%" }} />
    </AbsoluteFill>
  );
};

/** Psychologists behind a one-way mirror, scoring the paperclip */
const Lab: React.FC = () => {
  const t = useT();
  const checks = ["Trustworthy", "Likeable", "Funny"];
  return (
    <AbsoluteFill style={{ background: "#1d2733" }}>
      <div style={{ position: "absolute", left: 40, right: 40, top: 40, height: 380, background: "linear-gradient(135deg,#9fb6c9,#6f8aa1)", border: "10px solid #3a4652", display: "flex", alignItems: "flex-end", justifyContent: "center", gap: 70, paddingBottom: 10 }}>
        {["🧑‍🔬", "👩‍🔬", "🧑‍🔬"].map((e, i) => <span key={i} style={{ fontSize: 150, opacity: 0.75, transform: `translateY(${Math.sin(t * 2 + i) * 6}px)` }}>{e}</span>)}
        <div style={{ position: "absolute", top: 14, left: 20, ...pixel, fontSize: 40, color: "#fff" }}>ONE-WAY MIRROR</div>
      </div>
      <div style={{ position: "absolute", left: 60, bottom: 40, width: 470, background: "#fffbe6", padding: 26, boxShadow: "8px 8px 0 #000", transform: "rotate(-3deg)" }}>
        <div style={{ ...pixel, fontSize: 46, marginBottom: 10 }}>CANDIDATE: PAPERCLIP</div>
        {checks.map((c, i) => (
          <div key={c} style={{ ...pixel, fontSize: 48, display: "flex", gap: 14 }}>
            <span style={{ color: "#00a000", width: 34 }}>{t > 2.7 + i * 0.45 ? "✓" : ""}</span>{c}
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", right: 70, bottom: 60 }}><Clip size={170} look={-1} brow={1} /></div>
      <Label text="6 MONTHS OF TESTS" at={2.4} style={{ top: 440 }} size={60} />
    </AbsoluteFill>
  );
};

/** Hundreds of millions of office workers, multiplying */
const Crowd: React.FC = () => {
  const t = useT();
  const n = Math.round(lin(t, 5.4, 6.9, 1, 120));
  const people = ["🧑‍💼", "👩‍💼", "👨‍💼"];
  return (
    <AbsoluteFill style={{ background: "#f2f4f7" }}>
      <div style={{ position: "absolute", inset: 30, display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gap: 2, alignContent: "start" }}>
        {Array.from({ length: n }).map((_, i) => (
          <span key={i} style={{ fontSize: 58, textAlign: "center", position: "relative" }}>
            {people[i % 3]}
            {t > 6.9 + (i % 17) * 0.02 && <span style={{ position: "absolute", right: 2, bottom: 2, fontSize: 28 }}>🚫</span>}
          </span>
        ))}
      </div>
      <Label text="HUNDREDS OF MILLIONS" at={5.5} style={{ bottom: 60 }} size={70} bg="#d40000" fg="#fff" />
    </AbsoluteFill>
  );
};

const Off: React.FC = () => {
  const t = useT();
  const box = (on: boolean, label: string, hot?: boolean) => (
    <div style={{ display: "flex", alignItems: "center", gap: 18, ...pixel, fontSize: hot ? 56 : 46, color: hot ? "#000" : "#444" }}>
      <span style={{ ...bevel(true), background: "#fff", width: hot ? 64 : 44, height: hot ? 64 : 44, display: "flex", alignItems: "center", justifyContent: "center", fontSize: hot ? 66 : 48 }}>{on ? "✓" : ""}</span>
      {label}
    </div>
  );
  return (
    <AbsoluteFill style={{ background: GRAY }}>
      <div style={{ position: "absolute", left: 60, right: 60, top: 120, transform: `scale(${1 + lin(t, 7.2, 8.4, 0, 0.12)})` }}>
        <Win title="Office Assistant" small>
          <div style={{ background: GRAY, padding: "26px 30px", display: "flex", flexDirection: "column", gap: 22 }}>
            {box(true, "Respond to F1 key")}
            {box(true, "Display alerts")}
            {box(t < 7.84, "Show the Office Assistant", true)}
          </div>
        </Win>
      </div>
      <Cursor from={[820, 760]} to={[150, 460]} at={Math.round((7.3 - 7.15) * FPS)} clickAt={Math.round((7.84 - 7.15) * FPS)} />
    </AbsoluteFill>
  );
};

const Pause: React.FC = () => {
  const t = useT();
  const z = 1 + lin(t, 10.2, 12.6, 0, 0.45);
  return (
    <AbsoluteFill style={{ background: "#111", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", filter: "grayscale(1) contrast(1.3)", transform: `translateX(${Math.sin(t * 60) * 3}px) scale(${z})` }}>
        <Clip size={300} look={-1} />
      </div>
      <div style={{ position: "absolute", left: 40, top: 30, fontFamily: vt.fontFamily, fontSize: 84, color: "#fff", textShadow: "4px 0 #f00, -4px 0 #0ff" }}>|| PAUSE</div>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 70, textAlign: "center" }}>
        <Typed text="HOW DO YOU FIRE A PAPERCLIP?" from={8.9} cps={22} style={{ fontFamily: vt.fontFamily, fontSize: 78, color: YELLOW, background: "rgba(0,0,0,.6)", padding: "4px 18px" }} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: `${(t * 37) % 100}%`, height: 46, background: "rgba(255,255,255,.08)" }} />
      <Scanlines strength={0.3} />
    </AbsoluteFill>
  );
};

const Stanford: React.FC = () => (
  <AbsoluteFill style={{ background: "#0b1b0b", padding: 50, display: "flex", flexDirection: "column", gap: 14 }}>
    <Typed text="C:\STANFORD> research.exe" from={12.8} cps={30} style={{ fontFamily: vt.fontFamily, fontSize: 56, color: "#5cff5c" }} />
    <Typed text="THE MEDIA EQUATION (1996)" from={13.3} style={{ fontFamily: vt.fontFamily, fontSize: 64, color: "#b8ffb8" }} />
    <Typed text="Clifford Nass & Byron Reeves" from={13.75} style={{ fontFamily: vt.fontFamily, fontSize: 52, color: "#5cff5c" }} />
    <Scanlines strength={0.25} />
  </AbsoluteFill>
);

const Hands: React.FC = () => {
  const t = useT();
  const beat = Math.abs(Math.sin(t * 5));
  return (
    <AbsoluteFill style={{ background: "#fff3f6", display: "flex", alignItems: "center", justifyContent: "center", gap: 40 }}>
      <span style={{ fontSize: 230, transform: `translateX(${lin(t, 14.1, 14.6, -300, 0)}px)` }}>🧍</span>
      <span style={{ fontSize: 120, transform: `scale(${t > 14.4 ? 0.9 + beat * 0.25 : 0})` }}>❤️</span>
      <span style={{ fontSize: 230, transform: `translateX(${lin(t, 14.1, 14.6, 300, 0)}px)` }}>🖥️</span>
      <Label text="PEOPLE TREAT COMPUTERS LIKE PEOPLE" at={14.4} style={{ bottom: 60 }} size={62} wrap />
    </AbsoluteFill>
  );
};

const Face: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const smile = sp(frame, 16.95, 9, 180);
  return (
    <AbsoluteFill style={{ background: "#dfe7ef" }}>
      <div style={{ position: "absolute", left: 130, right: 130, top: 60, height: 560, background: "#d8d0b8", borderRadius: 36, border: "6px solid #8a826c" }}>
        <div style={{ position: "absolute", left: 50, right: 50, top: 46, bottom: 70, background: "#0b1b0b", borderRadius: 26, overflow: "hidden", border: "8px solid #6d6655" }}>
          <svg viewBox="0 0 200 120" style={{ width: "100%", height: "100%", transform: `scale(${Math.max(0.001, smile)})` }}>
            {[70, 130].map((cx) => <ellipse key={cx} cx={cx} cy={50} rx={10} ry={Math.floor(t * 3) % 7 === 0 ? 1.5 : 13} fill="#5cff5c" />)}
            <path d="M 60 82 Q 100 112 140 82" fill="none" stroke="#5cff5c" strokeWidth={8} strokeLinecap="round" />
          </svg>
          <Scanlines strength={0.25} />
        </div>
      </div>
      <Label text="GIVE OFFICE A FACE" at={17.3} style={{ bottom: 50 }} size={70} />
    </AbsoluteFill>
  );
};

const CAST = ["🐶", "🐱", "🤖", "🧙", "🦉", "🐬", "⚽", "🎩", "🌵", "🐌", "🦊", "🐸", "👽", "🐢", "🦄", "🐼", "🐵", "🍎", "🔧", "🎈"];

const Cast: React.FC = () => {
  const t = useT();
  const count = Math.round(lin(t, 19.6, 20.75, 0, 250));
  return (
    <AbsoluteFill style={{ background: "#fff" }}>
      <div style={{ position: "absolute", top: 16, left: 0, right: 0, textAlign: "center", ...pixel, fontSize: 60 }}>
        CHARACTERS DRAWN: <b style={{ color: "#d40000" }}>{count}</b>
      </div>
      <div style={{ position: "absolute", left: 22, right: 22, top: 100, display: "grid", gridTemplateColumns: "repeat(14, 1fr)", gap: 4, transform: `scale(${1 + lin(t, 18.6, 21.9, 0, 0.08)})` }}>
        {Array.from({ length: 250 }).map((_, i) => (
          <div key={i} style={{ height: 46, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 34, opacity: t >= 18.7 + (i / 250) * 1.9 ? 1 : 0 }}>
            {i === 117 ? "📎" : CAST[(i * 7) % CAST.length]}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Winner: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const s = sp(frame, 22.0, 12, 140);
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #fff6c8, #ffd400 70%)", overflow: "hidden" }}>
      {Array.from({ length: 16 }).map((_, i) => (
        <div key={i} style={{ position: "absolute", left: "50%", top: "45%", width: 1400, height: 60, background: "rgba(255,255,255,.35)", transformOrigin: "0 50%", transform: `rotate(${i * 22.5 + t * 20}deg)` }} />
      ))}
      <div style={{ position: "absolute", left: 0, right: 0, top: 70, display: "flex", justifyContent: "center", transform: `scale(${s})` }}>
        <Clip size={260} brow={t > 23.1 ? 1 : 0} look={Math.sin(t * 3)} />
      </div>
      <Stamp text="#1 ON TRUST" at={23.12} color={NAVY} size={96} rot={-6} style={{ top: "84%" }} />
    </AbsoluteFill>
  );
};

const Mac: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  return (
    <AbsoluteFill style={{ background: "#c9d3dc", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 24 }}>
      <div style={{ width: 430, height: 520, background: "#e9e3d3", border: "6px solid #9b9482", borderRadius: 30, position: "relative", boxShadow: "16px 16px 0 rgba(0,0,0,.25)", transform: `rotate(${Math.sin(t * 2) * 1.5}deg)` }}>
        <div style={{ position: "absolute", left: 50, right: 50, top: 46, height: 280, background: "#cfd8cf", border: "8px solid #6f6a5c", borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Clip size={100} />
        </div>
        <div style={{ position: "absolute", left: 160, right: 60, top: 380, height: 16, background: "#555", borderRadius: 5 }} />
      </div>
      <Label text="DRAWN ON A MAC" at={25.0} style={{ position: "relative" }} size={70} />
    </AbsoluteFill>
  );
};

const Setup: React.FC = () => {
  const t = useT();
  const pct = Math.round(lin(t, 26.4, 27.95, 0, 100));
  return (
    <AbsoluteFill style={{ background: "#008080" }}>
      <div style={{ position: "absolute", left: 60, right: 60, top: 90 }}>
        <Win title="Setup" small>
          <div style={{ background: GRAY, padding: 30, display: "flex", flexDirection: "column", gap: 20 }}>
            <div style={{ ...pixel, fontSize: 54 }}>Microsoft Office 97</div>
            <div style={{ ...pixel, fontSize: 40, color: "#333" }}>Released November 19, 1996</div>
            <div style={{ ...bevel(true), height: 56, background: "#fff", padding: 4 }}><div style={{ width: `${pct}%`, height: "100%", background: NAVY }} /></div>
            <div style={{ ...pixel, fontSize: 44 }}>{pct < 100 ? `Copying files... ${pct}%` : "Office Assistant: ON"}</div>
          </div>
        </Win>
      </div>
    </AbsoluteFill>
  );
};

/** Switched on for everyone: every screen in the office gets one */
const Everyone: React.FC = () => {
  const t = useT();
  return (
    <AbsoluteFill style={{ background: "#1f2a36" }}>
      <div style={{ position: "absolute", inset: 30, display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 14 }}>
        {Array.from({ length: 20 }).map((_, i) => (
          <div key={i} style={{ background: "#0e3b5c", border: "6px solid #c0c0c0", display: "flex", alignItems: "center", justifyContent: "center", height: 150 }}>
            {t > 28.15 + (i % 7) * 0.06 && <Clip size={44} brow={1} />}
          </div>
        ))}
      </div>
      <Stamp text="ON FOR EVERYONE" at={28.25} size={56} rot={-8} style={{ top: "50%" }} />
    </AbsoluteFill>
  );
};

const Letter: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const pop = sp(frame, 29.16, 8, 240);
  const balloonWords = words.filter((w) => w.s >= 29.3 && w.s < 32.4);
  return (
    <AbsoluteFill style={{ background: "#fff", transform: `translateX(${t > 29.16 && t < 29.4 ? Math.sin(t * 90) * 8 : 0}px)` }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 64, background: GRAY, borderBottom: "3px solid #808080", display: "flex", alignItems: "center", gap: 26, padding: "0 22px", ...pixel, fontSize: 40 }}>
        <b>B</b><i>I</i><u>U</u><span>Times New Roman</span><span>12</span>
      </div>
      <div style={{ position: "absolute", left: 60, top: 110, fontFamily: "Times New Roman, serif", fontSize: 64 }}><Typed text="Dear Sir," from={28.62} cps={14} /></div>
      <div style={{ position: "absolute", right: 70, bottom: 30, transform: `scale(${pop})`, transformOrigin: "80% 100%" }}>
        <Clip size={180} look={-1} brow={1} />
      </div>
      {t > 29.2 && (
        <Balloon style={{ left: 50, right: 70, top: 220, transform: `scale(${pop})`, transformOrigin: "85% 100%" }}>
          <div style={{ fontFamily: "Tahoma, Arial, sans-serif", fontSize: 52, lineHeight: 1.25 }}>{(() => { const x = balloonWords.filter((w) => t >= w.s - 0.05).map((w) => w.w).join(" "); return x.charAt(0).toUpperCase() + x.slice(1); })()}</div>
          {t > 31.9 && (
            <div style={{ marginTop: 18, display: "flex", flexDirection: "column", gap: 10, fontFamily: "Tahoma, Arial, sans-serif", fontSize: 38, color: "#00007a" }}>
              <span>● Get help with writing the letter</span>
              <span>● Just type the letter without help</span>
            </div>
          )}
        </Balloon>
      )}
    </AbsoluteFill>
  );
};

const Minutes: React.FC = () => {
  const t = useT();
  const secs = Math.round(lin(t, 32.8, 34.5, 0, 299));
  return (
    <AbsoluteFill style={{ background: "#eef3f8", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24 }}>
      <div style={{ ...pixel, fontSize: 60 }}>FOCUS GROUP</div>
      <div style={{ width: 380, height: 380, borderRadius: 190, border: "16px solid #000", background: "#fff", position: "relative" }}>
        <div style={{ position: "absolute", left: 182, top: 36, width: 16, height: 154, background: "#d40000", transformOrigin: "50% 100%", transform: `rotate(${(secs % 60) * 6}deg)` }} />
      </div>
      <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 110 }}>{String(Math.floor(secs / 60)).padStart(2, "0")}:{String(secs % 60).padStart(2, "0")}</div>
    </AbsoluteFill>
  );
};

const Years: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const years = ["1997", "1998", "1999", "2000", "2001"];
  const yi = Math.min(4, Math.max(0, Math.floor(lin(t, 35.0, 36.7, 0, 5))));
  const pops = [35.0, 35.45, 35.8, 36.1, 36.32, 36.5, 36.65, 36.78];
  return (
    <AbsoluteFill style={{ background: "#fff7e0", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: 40, left: 0, right: 0, textAlign: "center", ...pixel, fontSize: 60 }}>THE OFFICE, EVERY DAY</div>
      <div style={{ position: "absolute", top: 130, left: 180, right: 180, height: 250, ...bevel(), background: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 150, color: "#d40000" }}>{years[yi]}</span>
      </div>
      {pops.map((p, i) => t >= p && (
        <div key={i} style={{ position: "absolute", left: 40 + ((i * 113) % 760), top: 410 + ((i * 61) % 260), transform: `scale(${sp(frame, p, 8, 260)}) rotate(${i % 2 ? 10 : -10}deg)` }}>
          <Clip size={80} brow={1} look={i % 2 ? 1 : -1} />
        </div>
      ))}
    </AbsoluteFill>
  );
};

const Slam: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const big = sp(frame, 38.86, 8, 240);
  return (
    <AbsoluteFill style={{ background: "#000", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
      <Typed text="SO, IN..." from={37.5} cps={14} style={{ fontFamily: vt.fontFamily, fontSize: 90, color: "#fff" }} />
      {t > 38.8 && <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 300, color: YELLOW, transform: `scale(${2.4 - 1.4 * big})`, textShadow: "12px 12px 0 #d40000" }}>2001</span>}
    </AbsoluteFill>
  );
};

const Memo: React.FC = () => (
  <AbsoluteFill style={{ background: "#f4f1e8" }}>
    <div style={{ position: "absolute", left: 60, right: 60, top: 50, fontFamily: "Courier New, monospace", fontSize: 46, lineHeight: 1.5, background: "#fff", padding: 40, boxShadow: "10px 10px 0 rgba(0,0,0,.2)", transform: "rotate(-1.5deg)" }}>
      <div style={{ fontWeight: 900, fontSize: 58 }}>MEMORANDUM</div>
      <div>DATE: April 11, 2001</div>
      <div>TO: Clippit</div>
      <div>RE: Office XP</div>
      <div style={{ marginTop: 18 }}>Switched off by default.</div>
    </div>
    <Stamp text="FIRED" at={39.98} size={200} rot={-14} style={{ top: "62%" }} />
  </AbsoluteFill>
);

/** The Office XP launch stage, shot five ways */
const StageSet: React.FC<{ zoom: number; focusY: number; children?: React.ReactNode; curtainOpen: number; spot: boolean }> = ({ zoom, focusY, children, curtainOpen, spot }) => (
  <AbsoluteFill style={{ background: "#120707", overflow: "hidden" }}>
    <div style={{ position: "absolute", inset: 0, transform: `scale(${zoom})`, transformOrigin: `50% ${focusY}%` }}>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 170, background: "repeating-linear-gradient(90deg,#6b3f1d 0 60px,#5b3418 60px 120px)" }} />
      {spot && <div style={{ position: "absolute", left: "50%", top: -60, width: 760, height: 900, transform: "translateX(-50%)", background: "radial-gradient(ellipse at 50% 100%, rgba(255,250,210,.55), rgba(255,250,210,0) 70%)" }} />}
      {children}
      <div style={{ position: "absolute", top: 0, bottom: 0, left: 0, width: `${50 - curtainOpen * 42}%`, background: "repeating-linear-gradient(90deg,#8f0000 0 40px,#b30000 40px 80px)", boxShadow: "10px 0 30px rgba(0,0,0,.6)" }} />
      <div style={{ position: "absolute", top: 0, bottom: 0, right: 0, width: `${50 - curtainOpen * 42}%`, background: "repeating-linear-gradient(90deg,#b30000 0 40px,#8f0000 40px 80px)", boxShadow: "-10px 0 30px rgba(0,0,0,.6)" }} />
    </div>
  </AbsoluteFill>
);

const Suit: React.FC<{ beg?: boolean; drag?: number; look?: number }> = ({ beg, drag = 0, look = 0 }) => {
  const t = useT();
  const bob = beg ? Math.abs(Math.sin(t * 9)) * 22 : 0;
  return (
    <div style={{ position: "absolute", left: "50%", bottom: 150 - bob * 0.2, transform: `translateX(calc(-50% + ${drag * 900}px)) rotate(${drag * 25 + (beg ? -6 : 0)}deg)`, filter: drag > 0 ? `blur(${drag * 6}px)` : "none" }}>
      <div style={{ position: "relative" }}>
        <Clip size={230} brow={1} look={look} />
        <div style={{ position: "absolute", left: 70, bottom: -40, width: 14, height: 70, background: "#222", transform: `rotate(${beg ? 25 : 8}deg)` }} />
        <div style={{ position: "absolute", left: 150, bottom: -40, width: 14, height: 70, background: "#222", transform: `rotate(${beg ? -25 : -8}deg)` }} />
        {beg && <div style={{ position: "absolute", left: -70, top: -10, fontSize: 90 }}>🙏</div>}
      </div>
    </div>
  );
};

const Curtains: React.FC = () => {
  const t = useT();
  return (
    <StageSet zoom={1} focusY={50} curtainOpen={lin(t, 40.5, 41.2)} spot={t > 40.9}>
      <Suit />
      <div style={{ position: "absolute", left: 0, right: 0, top: 34, textAlign: "center", ...pixel, fontSize: 40, color: "#ffd9a0" }}>OFFICE XP LAUNCH · NEW YORK · MAY 31, 2001</div>
    </StageSet>
  );
};

const SuitClose: React.FC = () => (
  <StageSet zoom={1.9} focusY={72} curtainOpen={1} spot>
    <Suit look={1} />
    <div style={{ position: "absolute", left: 20, bottom: 30, background: "#d40000", color: "#fff", ...pixel, fontSize: 26, padding: "4px 12px" }}>● LIVE · NEW YORK · MAY 31, 2001</div>
  </StageSet>
);

const Beg: React.FC = () => {
  const t = useT();
  return (
    <StageSet zoom={2.8} focusY={64} curtainOpen={1} spot>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${Math.sin(t * 40) * 3}px, 0)` }}><Suit beg look={-1} /></div>
    </StageSet>
  );
};

const Magnet: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const mag = sp(frame, 44.85, 12, 110);
  return (
    <AbsoluteFill style={{ background: "#120707", overflow: "hidden" }}>
      <svg viewBox="0 0 200 200" style={{ position: "absolute", width: 820, height: 820, left: 60, top: -820 + mag * 620 }}>
        <g transform="rotate(180 100 100)">
          <path d="M 40 20 L 40 110 A 60 60 0 0 0 160 110 L 160 20 L 120 20 L 120 110 A 20 20 0 0 1 80 110 L 80 20 Z" fill="#d40000" stroke="#000" strokeWidth={4} />
          <rect x={40} y={10} width={40} height={30} fill="#cfd6dd" stroke="#000" strokeWidth={3} />
          <rect x={120} y={10} width={40} height={30} fill="#cfd6dd" stroke="#000" strokeWidth={3} />
        </g>
      </svg>
      {t > 45.0 && Array.from({ length: 8 }).map((_, i) => (
        <div key={i} style={{ position: "absolute", left: 160 + i * 90, top: 560 + ((i * 47) % 120), width: 80, height: 8, background: YELLOW, transform: `rotate(${-60 + i * 16}deg)`, opacity: (Math.floor(t * 20) + i) % 2 }} />
      ))}
      <Label text="A GIANT MAGNET" at={45.0} style={{ bottom: 50 }} size={70} bg="#d40000" fg="#fff" />
    </AbsoluteFill>
  );
};

const Drag: React.FC = () => {
  const t = useT();
  return (
    <StageSet zoom={1} focusY={50} curtainOpen={1 - lin(t, 46.35, 46.8)} spot>
      <Suit drag={lin(t, 45.9, 46.35)} look={1} />
    </StageSet>
  );
};

const Thirty: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const year = Math.round(lin(t, 47.0, 48.05, 1996, 2026));
  const big = sp(frame, 48.08, 8, 220);
  return (
    <AbsoluteFill style={{ background: NAVY, overflow: "hidden" }}>
      {t > 48.08 && Array.from({ length: 40 }).map((_, i) => (
        <div key={i} style={{ position: "absolute", left: `${(i * 37) % 100}%`, top: `${((t - 48.08) * (120 + (i % 7) * 40)) % 110 - 10}%`, width: 18, height: 18, background: [YELLOW, "#ff3b6b", "#3bd1ff", "#7dff6b"][i % 4], transform: `rotate(${i * 30 + t * 200}deg)` }} />
      ))}
      <div style={{ position: "absolute", top: 50, left: 0, right: 0, textAlign: "center", ...pixel, fontSize: 76, color: "#fff" }}>1996 → {year}</div>
      <div style={{ position: "absolute", top: 170, left: 0, right: 0, display: "flex", justifyContent: "center", alignItems: "center", gap: 30, transform: `scale(${Math.max(0.001, big)})` }}>
        <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 330, color: YELLOW, textShadow: "14px 14px 0 #000" }}>30</span>
        <Clip size={170} hat brow={1} />
      </div>
    </AbsoluteFill>
  );
};

const Photo: React.FC = () => {
  const t = useT();
  return (
    <AbsoluteFill style={{ background: "#e9eef3", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 640, background: "#fff", padding: "22px 22px 90px", boxShadow: "14px 14px 0 rgba(0,0,0,.25)", transform: `rotate(-4deg) scale(${1 + lin(t, 49, 50.3, 0, 0.06)})`, position: "relative" }}>
        <Img src={staticFile("clippy/costume.jpg")} style={{ width: "100%", height: 600, objectFit: "cover", objectPosition: "50% 30%" }} />
        <div style={{ position: "absolute", bottom: 22, left: 0, right: 0, textAlign: "center", fontFamily: "Comic Sans MS, cursive", fontSize: 44 }}>Finland, 2024</div>
      </div>
    </AbsoluteFill>
  );
};

const Emoji: React.FC = () => {
  const t = useT();
  const row = ["😀", "📁", "✂️", "📌", "📎", "🖇️", "📝", "📅", "💾"];
  return (
    <AbsoluteFill style={{ background: "#f5f5f5", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 760, ...bevel(), padding: 18 }}>
        <div style={{ ...pixel, fontSize: 46, marginBottom: 10 }}>Emoji · Microsoft 365</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, background: "#fff", padding: 16 }}>
          {row.map((e, i) => (
            <span key={i} style={{ fontSize: 110, textAlign: "center", background: e === "📎" ? YELLOW : "transparent", outline: e === "📎" ? `8px solid ${NAVY}` : "none", transform: e === "📎" ? `scale(${1 + 0.12 * Math.abs(Math.sin(t * 6))})` : "none" }}>{e}</span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const CopilotCard: React.FC = () => {
  const t = useT();
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg,#fdfbff,#e8f0ff)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 800, background: "#fff", borderRadius: 40, padding: 40, boxShadow: "12px 12px 0 rgba(0,0,0,.18)", display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
        <div style={{ width: 230, height: 230, borderRadius: 115, background: "conic-gradient(#ffb36b,#ff6bd5,#6bb6ff,#6bffb8,#ffb36b)", transform: `rotate(${t * 40}deg)` }} />
        <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 80 }}>Copilot</div>
        <div style={{ ...pixel, fontSize: 50, color: "#555" }}>🔒 a secret hidden inside</div>
      </div>
    </AbsoluteFill>
  );
};

const Tap: React.FC = () => {
  const t = useT();
  const taps = t < 53 ? 0 : Math.min(12, Math.floor((t - 53.0) / 0.21) + 1);
  const pulse = taps > 0 && taps < 12 && (t - 53.0) % 0.21 < 0.06 ? 0.9 : 1;
  return (
    <AbsoluteFill style={{ background: "#f5f7fb" }}>
      <div style={{ position: "absolute", top: 30, left: 0, right: 0, textAlign: "center", ...pixel, fontSize: 70 }}>TAPS: <b style={{ color: "#d40000" }}>{taps}</b> / 12</div>
      <div style={{ position: "absolute", left: "50%", top: 420, transform: `translate(-50%,-50%) scale(${pulse})`, width: 380, height: 380, borderRadius: 190, background: "conic-gradient(#ffb36b,#ff6bd5,#6bb6ff,#6bffb8,#ffb36b)", boxShadow: "0 0 60px rgba(255,107,213,.6)" }} />
      <Cursor from={[860, 760]} to={[560, 430]} at={8} />
    </AbsoluteFill>
  );
};

const Back: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const back = sp(frame, 55.95, 8, 220);
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #ffffff, #ffe4f6 70%)" }}>
      <div style={{ position: "absolute", left: "50%", top: 60, transform: `translateX(-50%) scale(${back}) rotate(${(1 - back) * 30}deg)`, transformOrigin: "50% 100%" }}>
        <Clip size={250} brow={1} look={Math.sin(t * 3)} blink={Math.floor(t * 9) % 13 === 0} />
      </div>
      {t > 56.3 && (
        <Balloon tail="left" style={{ left: 60, right: 60, bottom: 40, transform: `scale(${sp(frame, 56.3, 10, 220)})`, transformOrigin: "20% 0%" }}>
          <div style={{ fontFamily: "Tahoma, Arial, sans-serif", fontSize: 48, lineHeight: 1.25 }}>It looks like you're watching a Short. Would you like help?</div>
        </Balloon>
      )}
    </AbsoluteFill>
  );
};

const End: React.FC = () => (
  <AbsoluteFill style={{ background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 26 }}>
    <Clip size={150} brow={1} />
    <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 66, color: "#fff", textShadow: "6px 6px 0 #000" }}>Full story + sources</span>
    <span style={{ ...bevel(), ...pixel, fontSize: 60, padding: "8px 30px" }}>404memoryfound.com</span>
  </AbsoluteFill>
);

const BODY: Record<string, React.FC> = {
  hook: Hook, lab: Lab, crowd: Crowd, off: Off, pause: Pause, stanford: Stanford, hands: Hands, face: Face,
  cast: Cast, winner: Winner, mac: Mac, setup: Setup, everyone: Everyone, letter: Letter, minutes: Minutes,
  years: Years, slam: Slam, memo: Memo, curtains: Curtains, suit: SuitClose, beg: Beg, magnet: Magnet,
  drag: Drag, thirty: Thirty, photo: Photo, emoji: Emoji, copilot: CopilotCard, tap: Tap, back: Back, end: End,
};

/* ---------------- captions: word by word, following the voice ---------------- */

type Chunk = { words: W[]; s: number; e: number };
// Caption phrases: split at punctuation first, fold one-word fragments into the next clause, and cut
// a clause longer than 7 words where the halves balance without stranding a small word at either end.
const GLUE = /^(of|to|the|a|an|in|on|for|with|as|and|but|so|is|his|this|that|about|inside|at)$/i;
const BAD_START = /^(of|it|him|times|off|me)$/i;
const bare = (x: W) => x.w.replace(/[.,?!]/g, "");
const chunks: Chunk[] = (() => {
  const clauses: W[][] = [];
  let cur: W[] = [];
  words.forEach((w) => {
    cur.push(w);
    if (/[.,?!]$/.test(w.w)) { clauses.push(cur); cur = []; }
  });
  if (cur.length) clauses.push(cur);
  const merged: W[][] = [];
  for (let i = 0; i < clauses.length; i++) {
    if (clauses[i].length === 1 && i + 1 < clauses.length) { clauses[i + 1] = [...clauses[i], ...clauses[i + 1]]; continue; }
    merged.push(clauses[i]);
  }
  const split = (c: W[], max: number): W[][] => {
    if (c.length <= max) return [c];
    let best = -1, bestScore = Infinity;
    for (let b = 3; b <= c.length - 3; b++) {
      const compound = /^[A-Z]/.test(bare(c[b - 1])) && b > 1 && /^[a-z]/.test(bare(c[b])) ? 1.2 : 0; // "Clippy | suit"
      const score = Math.abs(b - c.length / 2) + (GLUE.test(bare(c[b - 1])) ? 10 : 0) + (BAD_START.test(bare(c[b])) ? 4 : 0) + compound;
      if (score < bestScore) { bestScore = score; best = b; }
    }
    return [...split(c.slice(0, best), 7), ...split(c.slice(best), 7)];
  };
  const out: Chunk[] = [];
  merged.forEach((c, i) => split(c, i === 0 ? 10 : 7).forEach((part) => out.push({ words: part, s: part[0].s, e: 0 })));
  out.forEach((c, i) => (c.e = i + 1 < out.length ? out[i + 1].s - 0.02 : D));
  out[0].s = 0;
  return out;
})();

const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const c = chunks.find((x) => t >= x.s - 0.06 && t < x.e);
  if (!c) return null;
  const first = c === chunks[0];
  const size = c.words.length > 6 ? 62 : 76;
  const pop = first ? 1 : sp(frame, c.s - 0.06, 12, 260);
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "14px 10px", maxWidth: 980, transform: `scale(${0.85 + 0.15 * pop})` }}>
      {c.words.map((w, i) => {
        if (!first && t < w.s - 0.04) return null;
        const current = t >= w.s - 0.04 && t < w.e + 0.04;
        const key = KEY.test(w.w.replace(/[.,?!]/g, "")) && t >= w.s;
        return (
          <span key={i} style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: size, lineHeight: 1.1, padding: "4px 14px", background: current ? YELLOW : key ? NAVY : "#fff", color: current ? NAVY : key ? YELLOW : "#000", boxShadow: "7px 7px 0 #000" }}>
            {w.w}
          </span>
        );
      })}
    </div>
  );
};

/* ---------------- shell ---------------- */

export const ClippyShort: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const total = CLIPPY_FRAMES;
  const shot = shotAt(t);
  const idx = SHOTS.indexOf(shot);
  const local = frame - Math.round(shot.s * FPS);
  const shake = SHAKES.reduce((acc, s) => acc + (t >= s && t < s + 0.28 ? Math.sin(t * 95) * 18 * (1 - (t - s) / 0.28) : 0), 0);
  const flash = SHAKES.reduce((acc, s) => Math.max(acc, t >= s && t < s + 0.1 ? 0.55 * (1 - (t - s) / 0.1) : 0), 0);
  const punch = PUNCH.reduce((acc, k) => Math.max(acc, t >= k && t < k + 0.6 ? Math.exp(-(t - k) * 7) : 0), 0);
  const off = lin(t, D + END_CARD - 0.45, D + END_CARD - 0.05, 1, 0.01);
  const on = lin(t, 0, 0.3, 0.02, 1);
  const Body = BODY[shot.id];

  return (
    <AbsoluteFill style={{ background: TEAL }}>
      <Audio src={staticFile("clippy/vo.wav")} />
      <Audio src={staticFile("music.wav")} loop volume={(f) => interpolate(f, [0, FPS * 0.8, total - FPS * 1.4, total], [0, 0.04, 0.04, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
      {SFX.map(([at, name, v], i) => (
        <Sequence key={i} from={Math.round(at * FPS)} durationInFrames={FPS * 3}>
          <Audio src={staticFile(`sfx/${name}.wav`)} volume={v} />
        </Sequence>
      ))}

      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
      <div style={{ position: "absolute", top: 70, left: 60, right: 60, ...bevel(), display: "flex", alignItems: "center", gap: 18, padding: "10px 18px" }}>
        <Img src={staticFile("logo.png")} style={{ width: 64, height: 64 }} />
        <span style={{ ...pixel, fontSize: 52 }}>404 Memory Found</span>
        <span style={{ marginLeft: "auto", ...pixel, fontSize: 44 }}>{Math.min(idx + 1, SHOTS.length - 1)}/{SHOTS.length - 1}</span>
      </div>

      <div style={{ position: "absolute", top: 210, left: 60, right: 60, height: 900, transform: `translateX(${shake}px) scaleY(${Math.min(off, on)})` }}>
        <Win title={shot.title} style={{ height: "100%" }}>
          <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
            <div style={{ position: "absolute", inset: 0, transform: `scale(${1 + 0.07 * punch}) rotate(${(idx % 2 ? 1 : -1) * 0.8 * punch}deg)` }}>
              <div style={{ position: "absolute", inset: 0, ...entrance(shot.in, local) }}>
                <Body />
              </div>
            </div>
          </div>
          {flash > 0 && <div style={{ position: "absolute", inset: 0, background: `rgba(255,255,255,${flash})` }} />}
        </Win>
      </div>

      <div style={{ position: "absolute", top: 1160, left: 40, right: 40, height: 430, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {shot.id !== "end" && <Captions />}
      </div>

      <div style={{ position: "absolute", bottom: 90, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
        <div style={{ ...bevel(true), display: "flex", gap: 6, padding: 8, width: 900 }}>
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} style={{ flex: 1, height: 26, background: i < Math.round((frame / total) * 24) ? NAVY : "transparent" }} />
          ))}
        </div>
        <span style={{ fontFamily: vt.fontFamily, fontSize: 40, color: "#fff" }}>Sourced. Dated. No invented numbers.</span>
      </div>
      <Scanlines strength={0.04} />
    </AbsoluteFill>
  );
};
