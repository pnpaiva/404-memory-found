import React from "react";
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Button, Cursor, NAVY, Scanlines, YELLOW, bevel, inter, pixel, vt } from "./ui";

/* Story-specific scenes. Each one belongs to a subject and should appear in ONE video, so no two
   shorts look alike inside the shared Win95 shell. Data always comes from the video's script. */

const mono: React.CSSProperties = { fontFamily: "Menlo, Courier New, monospace", fontWeight: 700 };

/* ------------------------------------------------------------------ Blockbuster: the tape itself */

/** VHS cassette: reels turn, the tape counter runs a number down (stores, users, whatever the script says). */
export const VhsTape: React.FC<{ data: { label: string; sub?: string; from: number; to: number; unit: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const spin = frame * 7;
  const n = Math.round(interpolate(frame, [14, 100], [data.from, data.to], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const wind = interpolate(frame, [14, 100], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const Reel: React.FC<{ fill: number; dir: number }> = ({ fill, dir }) => (
    <div style={{ width: 190, height: 190, borderRadius: 95, background: "#151515", border: "5px solid #000", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
      <div style={{ position: "absolute", width: 60 + fill * 120, height: 60 + fill * 120, borderRadius: 200, background: "#2b2b2b", border: "3px solid #444" }} />
      <div style={{ position: "absolute", width: 70, height: 70, borderRadius: 35, background: "#d8d8d8", transform: `rotate(${spin * dir}deg)` }}>
        {[0, 60, 120].map((a) => (
          <div key={a} style={{ position: "absolute", left: 31, top: 0, width: 8, height: 70, background: "#151515", transform: `rotate(${a}deg)` }} />
        ))}
      </div>
    </div>
  );
  return (
    <div style={{ position: "absolute", inset: 0, background: "#191919", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 850, height: 520, background: "#0d0d0d", border: "7px solid #000", borderRadius: 10, position: "relative", boxShadow: "0 26px 60px rgba(0,0,0,.65)", transform: "rotate(-1.5deg)", padding: 24 }}>
        <div style={{ height: 210, background: "#242424", border: "5px solid #000", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "space-around", padding: "0 40px" }}>
          <Reel fill={1 - wind} dir={1} />
          <Reel fill={wind} dir={-1} />
        </div>
        <div style={{ marginTop: 22, background: "#f4f1e4", border: "4px solid #000", padding: "14px 20px", display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ ...mono, fontSize: 44, color: "#111" }}>{data.label}</div>
          {data.sub && <div style={{ ...mono, fontSize: 30, color: "#666" }}>{data.sub}</div>}
        </div>
        <div style={{ position: "absolute", right: 28, bottom: 26, background: "#000", border: "4px solid #333", padding: "6px 18px", display: "flex", alignItems: "baseline", gap: 12 }}>
          <span style={{ ...mono, fontSize: 26, color: "#888" }}>{data.unit}</span>
          <span style={{ ...mono, fontSize: 62, color: n === data.to ? "#3cff6a" : "#ff5b4a", letterSpacing: 2 }}>{String(n).padStart(4, "0")}</span>
        </div>
        <div style={{ position: "absolute", left: 26, bottom: 24, background: YELLOW, border: "3px solid #000", padding: "6px 14px", transform: "rotate(-4deg)", ...mono, fontSize: 26 }}>
          BE KIND, REWIND
        </div>
      </div>
      <Scanlines strength={0.08} />
    </div>
  );
};

/** Airport-style split-flap board: rows clatter through characters and settle on the surviving locations. */
const FLAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,'-";
const Flap: React.FC<{ ch: string; delay: number; w?: number; tone?: string }> = ({ ch, delay, w = 30, tone }) => {
  const frame = useCurrentFrame();
  const t = frame - delay;
  const settled = t > 12;
  const shown = t < 0 ? " " : settled ? ch : FLAP[Math.floor(Math.abs(t) * 2.4) % FLAP.length];
  return (
    <span style={{ display: "inline-block", width: w, height: 54, lineHeight: "54px", textAlign: "center", background: "#101010", color: settled ? tone || "#fff" : "#b9b9b9", ...mono, fontSize: 34, marginRight: 3, borderTop: "2px solid #2e2e2e", borderBottom: "2px solid #000", boxShadow: "inset 0 -1px 0 #3a3a3a" }}>
      {shown}
    </span>
  );
};
export const SplitFlapBoard: React.FC<{ data: { title: string; rows: [string, string][]; footer?: string } }> = ({ data }) => {
  const pad = (s: string, n: number) => (s.toUpperCase() + " ".repeat(n)).slice(0, n);
  return (
    <div style={{ position: "absolute", inset: 0, background: "#0b0b0b", padding: "22px 18px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <div style={{ ...mono, fontSize: 34, color: YELLOW, letterSpacing: 3, marginBottom: 8 }}>{data.title.toUpperCase()}</div>
      <div style={{ display: "flex", ...mono, fontSize: 24, color: "#6a6a6a", letterSpacing: 4, marginBottom: 8 }}>
        <span style={{ width: 578 }}>LOCATION</span><span>STATUS</span>
      </div>
      {data.rows.map(([a, b], i) => {
        const tone = /open|live|yes/i.test(b) ? "#3cff6a" : /clos|gone|no/i.test(b) ? "#ff5b4a" : "#fff";
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", marginBottom: 9 }}>
            {pad(a, 17).split("").map((c, j) => <Flap key={j} ch={c} delay={8 + i * 11 + j * 1.5} />)}
            <span style={{ width: 16 }} />
            {pad(b, 7).split("").map((c, j) => <Flap key={"b" + j} ch={c} delay={20 + i * 11 + j * 1.5} w={30} tone={tone} />)}
          </div>
        );
      })}
      {data.footer && <div style={{ ...mono, fontSize: 30, color: "#9a9a9a", marginTop: 14 }}>{data.footer}</div>}
    </div>
  );
};

/** A rental membership card that slides in, tilts, and shows the owner details embossed. */
export const MemberCard: React.FC<{ data: { brand: string; name: string; number: string; rows: [string, string][] } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 4, fps, config: { damping: 15, stiffness: 90 } });
  return (
    <div style={{ position: "absolute", inset: 0, background: "linear-gradient(160deg,#123 0%,#245 100%)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 820, height: 500, borderRadius: 26, background: "linear-gradient(150deg,#f6c945 0%,#e8a90f 55%,#f6c945 100%)", border: "5px solid #6b4c00", boxShadow: "0 26px 50px rgba(0,0,0,.5)", padding: 30, transform: `translateX(${(1 - s) * -1200}px) rotate(${-3 + (1 - s) * 8}deg)`, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: 96, height: 66, background: "#1b1b1b" }} />
        <div style={{ ...inter, fontWeight: 900, fontSize: 56, color: NAVY, letterSpacing: -1 }}>{data.brand}</div>
        <div style={{ ...mono, fontSize: 30, color: "#6b4c00" }}>MEMBER CARD</div>
        <div style={{ marginTop: 104, ...mono, fontSize: 46, color: "#2a1e00", letterSpacing: 4, textShadow: "1px 1px 0 rgba(255,255,255,.55)" }}>{data.number}</div>
        <div style={{ marginTop: 18, display: "flex", flexDirection: "column", gap: 8 }}>
          {data.rows.map(([k, v], i) => {
            const show = frame > 26 + i * 14;
            return (
              <div key={k} style={{ display: "flex", gap: 14, ...mono, fontSize: 30, color: "#231900", opacity: show ? 1 : 0.12 }}>
                <span style={{ width: 260, color: "#6b4c00", flexShrink: 0 }}>{k.toUpperCase()}</span>
                <span style={{ fontWeight: 700 }}>{v}</span>
              </div>
            );
          })}
        </div>
        <div style={{ position: "absolute", right: 30, top: 30, ...inter, fontWeight: 900, fontSize: 34, color: NAVY, background: "rgba(255,255,255,.55)", padding: "4px 12px", border: "3px solid #6b4c00" }}>{data.name}</div>
      </div>
    </div>
  );
};

/** Due-date card: dates stamped one by one, the last one stamped in red at an angle. */
export const DueDateCard: React.FC<{ data: { title: string; dates: string[]; final: string; finalNote: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stampAt = 16 + data.dates.length * 16;
  const st = spring({ frame: frame - stampAt, fps, config: { damping: 9, stiffness: 260 } });
  return (
    <div style={{ position: "absolute", inset: 0, background: "#5b5147", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 720, background: "#fbf7e8", border: "3px solid #cbbfa2", padding: "26px 30px 40px", transform: "rotate(1deg)", boxShadow: "0 20px 40px rgba(0,0,0,.45)" }}>
        <div style={{ ...mono, fontSize: 38, textAlign: "center", letterSpacing: 3, borderBottom: "3px solid #333", paddingBottom: 12 }}>{data.title.toUpperCase()}</div>
        <div style={{ ...mono, fontSize: 26, color: "#888", textAlign: "center", margin: "10px 0 18px" }}>DATE DUE</div>
        {data.dates.map((d, i) => {
          const show = frame > 14 + i * 16;
          return (
            <div key={d} style={{ borderBottom: "2px dotted #bbb", padding: "10px 6px", ...mono, fontSize: 36, color: "#2b2b2b", opacity: show ? 1 : 0, transform: show ? `rotate(${(i % 2 ? 1 : -1) * 0.8}deg)` : "none" }}>
              {d}
            </div>
          );
        })}
        <div style={{ position: "relative", height: 140 }}>
          <div style={{ position: "absolute", left: 40, top: 26, border: "7px solid #c0392b", color: "#c0392b", padding: "10px 24px", ...mono, fontSize: 52, transform: `rotate(-11deg) scale(${0.4 + 0.6 * st})`, opacity: st, letterSpacing: 3 }}>
            {data.final.toUpperCase()}
          </div>
        </div>
        <div style={{ ...mono, fontSize: 28, color: "#666", textAlign: "center" }}>{data.finalNote}</div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ Kmart: the Blue Light Special */

export const BlueLight: React.FC<{ data: { announce: string; detail: string; count: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rot = frame * 5;
  const pulse = 0.55 + 0.45 * Math.abs(Math.sin(frame / 7));
  const drop = spring({ frame: frame - 6, fps, config: { damping: 14, stiffness: 110 } });
  const flash = Math.floor(frame / 9) % 2 === 0;
  return (
    <div style={{ position: "absolute", inset: 0, background: "#121a24", overflow: "hidden" }}>
      {/* aisle floor */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: "38%", background: "linear-gradient(180deg,#1b2530,#0d131a)" }} />
      {/* rotating light cone */}
      <div style={{ position: "absolute", left: "50%", top: 150, width: 900, height: 700, marginLeft: -450, transform: `rotate(${rot}deg)`, transformOrigin: "50% 0%" }}>
        <div style={{ position: "absolute", left: 450, top: 0, width: 0, height: 0, borderLeft: "150px solid transparent", borderRight: "150px solid transparent", borderTop: `700px solid rgba(60,140,255,${0.30 * pulse})`, marginLeft: -150, filter: "blur(6px)" }} />
      </div>
      {/* the beacon */}
      <div style={{ position: "absolute", left: "50%", top: 60, marginLeft: -70, width: 140, transform: `translateY(${(1 - drop) * -400}px)` }}>
        <div style={{ width: 26, height: 90, background: "#39414b", margin: "0 auto" }} />
        <div style={{ width: 140, height: 96, borderRadius: "70px 70px 12px 12px", background: `radial-gradient(circle at 50% 40%, #9fd0ff, #1f6fe0)`, border: "5px solid #0d2a52", boxShadow: `0 0 ${40 * pulse}px ${18 * pulse}px rgba(60,140,255,.85)` }} />
        <div style={{ width: 170, height: 22, background: "#39414b", marginLeft: -15, borderRadius: 4 }} />
      </div>
      {/* PA announcement */}
      <div style={{ position: "absolute", left: 30, right: 30, top: 330, textAlign: "center" }}>
        <div style={{ display: "inline-block", ...inter, fontWeight: 900, fontSize: 62, color: flash ? YELLOW : "#fff", background: flash ? NAVY : "rgba(0,0,0,.55)", padding: "10px 28px", border: "5px solid #fff", letterSpacing: -1 }}>
          {data.announce.toUpperCase()}
        </div>
        <div style={{ marginTop: 16, fontFamily: vt.fontFamily, fontSize: 42, color: "#cfe6ff" }}>{data.detail}</div>
      </div>
      {/* price-tag style count */}
      <div style={{ position: "absolute", left: "50%", bottom: 40, marginLeft: -230, width: 460, background: "#fff", border: "6px solid #c0392b", transform: "rotate(-2deg)", padding: "12px 0", textAlign: "center", boxShadow: "10px 10px 0 rgba(0,0,0,.5)" }}>
        <div style={{ ...mono, fontSize: 28, color: "#c0392b", letterSpacing: 4 }}>STORES OPEN TODAY</div>
        <div style={{ ...inter, fontWeight: 900, fontSize: 120, color: "#c0392b", lineHeight: 1 }}>{data.count}</div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ Ask Jeeves: the search page */

const Butler: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <svg viewBox="0 0 120 170" style={{ width: 150, height: 210, ...style }}>
    <ellipse cx="60" cy="40" rx="30" ry="34" fill="#f0cfae" stroke="#000" strokeWidth="3" />
    <path d="M30 30 Q60 4 90 30 Q78 18 60 18 Q42 18 30 30 Z" fill="#d9d9d9" stroke="#000" strokeWidth="2.5" />
    <circle cx="48" cy="40" r="4" fill="#000" /><circle cx="72" cy="40" r="4" fill="#000" />
    <path d="M48 56 Q60 64 72 56" stroke="#000" strokeWidth="3" fill="none" />
    <path d="M25 168 L25 92 Q60 70 95 92 L95 168 Z" fill="#1b1b2b" stroke="#000" strokeWidth="3" />
    <path d="M45 78 L60 108 L75 78 L60 88 Z" fill="#fff" stroke="#000" strokeWidth="2" />
    <path d="M52 84 L60 92 L68 84 L60 80 Z" fill="#8b1a1a" stroke="#000" strokeWidth="2" />
    <rect x="8" y="96" width="18" height="66" rx="8" fill="#1b1b2b" stroke="#000" strokeWidth="3" />
    <rect x="94" y="96" width="18" height="66" rx="8" fill="#1b1b2b" stroke="#000" strokeWidth="3" />
  </svg>
);

/** A 90s natural-language search page: the question types itself, the butler answers, then the site goes dark. */
export const AskPage: React.FC<{ data: { brand: string; question: string; answer: string; closed?: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const typed = data.question.slice(0, Math.max(0, Math.floor((frame - 10) * 1.5)));
  const done = typed.length >= data.question.length;
  const askAt = 10 + Math.ceil(data.question.length / 1.5) + 6;
  const ans = spring({ frame: frame - askAt - 10, fps, config: { damping: 15, stiffness: 130 } });
  const closeAt = askAt + 70;
  const fade = data.closed ? interpolate(frame, [closeAt, closeAt + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff" }}>
      <div style={{ position: "absolute", inset: 0, opacity: 1 - fade }}>
        <div style={{ textAlign: "center", paddingTop: 26 }}>
          <span style={{ ...inter, fontWeight: 900, fontSize: 66, color: "#1b3a8c", letterSpacing: -2 }}>{data.brand}</span>
        </div>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 10, padding: "10px 30px 0" }}>
          <Butler style={{ flexShrink: 0 }} />
          <div style={{ flex: 1, paddingBottom: 30 }}>
            <div style={{ ...pixel, fontSize: 34, color: "#444", marginBottom: 8 }}>Ask me a question, and I'll find the answer:</div>
            <div style={{ display: "flex", gap: 10, alignItems: "stretch" }}>
              <div style={{ flex: 1, ...bevel(true), background: "#fff", padding: "10px 14px", ...pixel, fontSize: 36, minHeight: 54 }}>
                {typed}{!done && frame % 20 < 10 ? "|" : ""}
              </div>
              <Button label="Ask!" pressed={frame > askAt && frame < askAt + 8} style={{ fontSize: 36 }} />
            </div>
          </div>
        </div>
        {ans > 0.02 && (
          <div style={{ margin: "6px 30px 0", ...bevel(), padding: 10, transform: `scale(${0.9 + 0.1 * ans})`, opacity: ans }}>
            <div style={{ background: "#1b3a8c", color: "#fff", ...pixel, fontSize: 30, padding: "6px 12px" }}>1 answer found</div>
            <div style={{ background: "#fff", padding: "16px 18px", ...inter, fontWeight: 700, fontSize: 40, color: "#111", lineHeight: 1.25 }}>
              {data.answer}
            </div>
          </div>
        )}
        <Cursor from={[880, 620]} to={[840, 250]} at={askAt - 14} clickAt={askAt} />
      </div>
      {data.closed && (
        <div style={{ position: "absolute", inset: 0, background: "#000", opacity: fade, display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ ...mono, fontSize: 46, color: "#8a8a8a", marginBottom: 14 }}>{data.brand.toUpperCase()}</div>
            <div style={{ ...inter, fontWeight: 900, fontSize: 60, color: "#fff", lineHeight: 1.2 }}>{data.closed}</div>
          </div>
        </div>
      )}
    </div>
  );
};

/* ------------------------------------------------------------------ Pets.com: TV and the market */

/** A wood-panel CRT set. Shows a photo or a game of Pong, with an on-screen price stamp. */
export const CrtSet: React.FC<{ data: { mode?: "photo" | "pong"; src?: string; channel?: string; stamp?: string; caption?: string; score?: [string, string] } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const on = spring({ frame, fps, config: { damping: 16, stiffness: 200 } });
  const bx = 60 + Math.abs(((frame * 9) % 620) - 310);
  const by = 60 + Math.abs(((frame * 6) % 360) - 180);
  const stampIn = spring({ frame: frame - 40, fps, config: { damping: 10, stiffness: 200 } });
  return (
    <div style={{ position: "absolute", inset: 0, background: "#2b2b2b", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 880, background: "linear-gradient(180deg,#6b4a2a,#4a3119)", border: "8px solid #2e1d0c", borderRadius: 18, padding: 26, boxShadow: "0 26px 50px rgba(0,0,0,.55)" }}>
        <div style={{ position: "relative", height: 520, background: "#000", borderRadius: 40, overflow: "hidden", border: "10px solid #111", transform: `scaleY(${Math.min(1, on * 1.2)})` }}>
          {data.mode === "pong" ? (
            <>
              <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 6, marginLeft: -3, backgroundImage: "repeating-linear-gradient(180deg,#fff 0 18px,transparent 18px 36px)" }} />
              <div style={{ position: "absolute", left: 30, top: by, width: 16, height: 110, background: "#fff" }} />
              <div style={{ position: "absolute", right: 30, top: 420 - by, width: 16, height: 110, background: "#fff" }} />
              <div style={{ position: "absolute", left: bx, top: by + 40, width: 18, height: 18, background: "#fff" }} />
              {data.score && (
                <div style={{ position: "absolute", left: 0, right: 0, top: 18, display: "flex", justifyContent: "space-around", ...mono, fontSize: 64, color: "#fff" }}>
                  <span>{data.score[0]}</span><span>{data.score[1]}</span>
                </div>
              )}
            </>
          ) : data.src ? (
            <Img src={staticFile(data.src)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(1.25) contrast(1.1)" }} />
          ) : null}
          <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at center, rgba(255,255,255,.06), rgba(0,0,0,.55))" }} />
          <Scanlines strength={0.2} />
          {data.channel && <div style={{ position: "absolute", top: 18, left: 26, ...mono, fontSize: 46, color: "#8dff8d", textShadow: "0 0 12px #4f4" }}>{data.channel}</div>}
          {data.stamp && (
            <div style={{ position: "absolute", left: 30, bottom: 34, background: YELLOW, border: "5px solid #000", padding: "8px 20px", ...inter, fontWeight: 900, fontSize: 52, color: "#111", transform: `rotate(-3deg) scale(${0.5 + 0.5 * stampIn})`, opacity: stampIn }}>
              {data.stamp}
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 18 }}>
          <div style={{ ...mono, fontSize: 30, color: "#e6cfae" }}>{data.caption || ""}</div>
          <div style={{ display: "flex", gap: 12 }}>
            {[0, 1, 2].map((i) => <div key={i} style={{ width: 42, height: 42, borderRadius: 21, background: "linear-gradient(180deg,#d8c39b,#8a7448)", border: "3px solid #2e1d0c" }} />)}
          </div>
        </div>
      </div>
    </div>
  );
};

/** Stock ticker tape plus a share price falling off a cliff. */
export const StockCrash: React.FC<{ data: { symbol: string; tape: string[]; from: number; to: number; note: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const prog = interpolate(frame, [14, 105], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const price = data.from + (data.to - data.from) * prog;
  const W = 860, H = 420;
  const pts = Array.from({ length: 60 }).map((_, i) => {
    const t = i / 59;
    const wobble = Math.sin(i * 1.7) * 0.035;
    const y = t <= prog ? 1 - Math.pow(1 - t, 2.2) + wobble : null;
    return y === null ? null : [30 + t * (W - 60), 30 + Math.max(0, Math.min(1, y)) * (H - 70)];
  }).filter(Boolean) as [number, number][];
  const path = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  return (
    <div style={{ position: "absolute", inset: 0, background: "#07110b" }}>
      <div style={{ height: 74, background: "#000", borderBottom: "4px solid #1c3", overflow: "hidden", display: "flex", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 44, whiteSpace: "nowrap", transform: `translateX(${-((frame * 6) % 1600)}px)`, ...mono, fontSize: 40, color: "#25d366" }}>
          {[...data.tape, ...data.tape, ...data.tape].map((t, i) => (
            <span key={i} style={{ color: t.includes("-") ? "#ff5b4a" : "#25d366" }}>{t}</span>
          ))}
        </div>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: 430, display: "block" }}>
        {[0, 1, 2, 3].map((i) => <line key={i} x1={30} x2={W - 30} y1={30 + i * ((H - 70) / 3)} y2={30 + i * ((H - 70) / 3)} stroke="#123" strokeWidth="2" />)}
        <path d={path} stroke="#ff3b2f" strokeWidth="7" fill="none" strokeLinejoin="round" />
        {pts.length > 1 && <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="12" fill="#ff3b2f" />}
      </svg>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "6px 34px" }}>
        <span style={{ ...mono, fontSize: 54, color: "#fff" }}>{data.symbol}</span>
        <span style={{ ...inter, fontWeight: 900, fontSize: 104, color: "#ff3b2f", letterSpacing: -3 }}>${price.toFixed(2)}</span>
      </div>
      <div style={{ ...mono, fontSize: 32, color: "#5f8f6f", padding: "0 34px" }}>{data.note}</div>
    </div>
  );
};

/* ------------------------------------------------------------------ Sears: the catalog */

export const CatalogBook: React.FC<{ data: { brand: string; pages: { year: string; items: [string, string][] }[]; footer?: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const per = 42;
  const idx = Math.min(data.pages.length - 1, Math.floor(Math.max(0, frame - 10) / per));
  const local = Math.max(0, frame - 10) - idx * per;
  const flip = interpolate(local, [per - 14, per], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const page = data.pages[idx];
  return (
    <div style={{ position: "absolute", inset: 0, background: "#4a3f33", display: "flex", alignItems: "center", justifyContent: "center", perspective: 1600 }}>
      <div style={{ display: "flex", boxShadow: "0 26px 50px rgba(0,0,0,.5)" }}>
        <div style={{ width: 430, height: 640, background: "#efe7d2", borderRight: "4px solid #cdbf9d", padding: "26px 24px", ...mono }}>
          <div style={{ fontSize: 34, textAlign: "center", letterSpacing: 3, borderBottom: "3px solid #6b5b3e", paddingBottom: 10, color: "#3a2f1c" }}>{data.brand.toUpperCase()}</div>
          <div style={{ fontSize: 26, textAlign: "center", color: "#8a7a56", margin: "8px 0 18px" }}>CATALOG {page.year}</div>
          {page.items.map(([n, p], i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "12px 0", borderBottom: "2px dotted #c3b391", fontSize: 30, color: "#3a2f1c" }}>
              <span>{n}</span><span>{p}</span>
            </div>
          ))}
        </div>
        <div style={{ width: 430, height: 640, background: "#f4eddb", padding: 24, transformOrigin: "left center", transform: `rotateY(${-flip * 118}deg)`, backfaceVisibility: "hidden", boxShadow: flip > 0.05 ? "-14px 0 30px rgba(0,0,0,.3)" : "none" }}>
          <div style={{ height: "100%", border: "3px solid #cdbf9d", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 14 }}>
            <div style={{ ...inter, fontWeight: 900, fontSize: 120, color: "#6b5b3e", lineHeight: 1 }}>{page.year}</div>
            <div style={{ ...mono, fontSize: 30, color: "#8a7a56", textAlign: "center", padding: "0 20px" }}>{data.footer || "ORDER BY MAIL"}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ RuneScape: the level-up */

export const LevelUp: React.FC<{ data: { skill: string; line1: string; line2: string; xpFrom: number; xpTo: number; peak: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const box = spring({ frame: frame - 8, fps, config: { damping: 13, stiffness: 150 } });
  const xp = Math.round(interpolate(frame, [10, 96], [data.xpFrom, data.xpTo], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const bars = 40;
  const grown = interpolate(frame, [10, 96], [0, bars], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", inset: 0, background: "#2c2412" }}>
      <div style={{ position: "absolute", inset: 0, backgroundImage: "repeating-linear-gradient(45deg,rgba(0,0,0,.12) 0 6px,transparent 6px 12px)" }} />
      {/* player-count bars climbing */}
      <div style={{ position: "absolute", left: 40, right: 40, bottom: 120, height: 300, display: "flex", alignItems: "flex-end", gap: 5 }}>
        {Array.from({ length: bars }).map((_, i) => {
          const on = i < grown;
          const h = 16 + Math.pow(i / bars, 1.9) * 280;
          return <div key={i} style={{ flex: 1, height: on ? h : 4, background: i > bars - 6 ? YELLOW : "#7a5c1d", border: "2px solid #4a3610" }} />;
        })}
      </div>
      <div style={{ position: "absolute", left: 40, bottom: 60, ...mono, fontSize: 34, color: "#d8c288" }}>PLAYERS ONLINE</div>
      <div style={{ position: "absolute", right: 40, bottom: 46, ...inter, fontWeight: 900, fontSize: 76, color: YELLOW, textShadow: "4px 4px 0 #000" }}>{xp.toLocaleString("en-US")}</div>
      {/* the classic level-up box */}
      <div style={{ position: "absolute", left: 60, right: 60, top: 90, background: "#c8b083", border: "5px solid #7a5c1d", boxShadow: "8px 8px 0 rgba(0,0,0,.45)", padding: "22px 26px", display: "flex", gap: 22, alignItems: "center", transform: `scale(${0.7 + 0.3 * box})`, opacity: box }}>
        <div style={{ width: 96, height: 96, background: "#6b4f16", border: "4px solid #3a2a08", display: "flex", alignItems: "center", justifyContent: "center", ...inter, fontWeight: 900, fontSize: 46, color: YELLOW, flexShrink: 0 }}>
          {data.skill.slice(0, 2).toUpperCase()}
        </div>
        <div>
          <div style={{ ...mono, fontSize: 36, color: "#1d3d8f" }}>{data.line1}</div>
          <div style={{ ...mono, fontSize: 36, color: "#111", marginTop: 6 }}>{data.line2}</div>
          <div style={{ ...mono, fontSize: 28, color: "#5a4a22", marginTop: 8 }}>{data.peak}</div>
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ Atari: the cartridge slot */

export const CartSlot: React.FC<{ data: { rows: [string, string][]; note?: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const per = 34;
  const idx = Math.min(data.rows.length - 1, Math.floor(Math.max(0, frame - 6) / per));
  const local = Math.max(0, frame - 6) - idx * per;
  const insert = spring({ frame: local, fps, config: { damping: 16, stiffness: 130 } });
  const [owner, price] = data.rows[idx];
  return (
    <div style={{ position: "absolute", inset: 0, background: "#20242b", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 }}>
      {/* the cartridge sliding down into the slot */}
      <div style={{ width: 460, height: 240, background: "linear-gradient(180deg,#3b3b3b,#1e1e1e)", border: "5px solid #000", borderRadius: "8px 8px 0 0", transform: `translateY(${(1 - insert) * -260}px)`, padding: "18px 20px", boxShadow: "0 14px 28px rgba(0,0,0,.5)" }}>
        <div style={{ background: "#efe6cf", border: "4px solid #000", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4 }}>
          <div style={{ ...inter, fontWeight: 900, fontSize: 40, color: "#111", textAlign: "center", padding: "0 10px" }}>{owner}</div>
          <div style={{ ...mono, fontSize: 44, color: "#c0392b" }}>{price}</div>
        </div>
      </div>
      {/* console body with the slot */}
      <div style={{ width: 820, height: 250, background: "linear-gradient(180deg,#4b4b4b,#262626)", border: "6px solid #000", borderRadius: 14, position: "relative", boxShadow: "0 22px 44px rgba(0,0,0,.55)" }}>
        <div style={{ position: "absolute", left: "50%", top: -12, marginLeft: -240, width: 480, height: 26, background: "#0a0a0a", border: "4px solid #000", borderRadius: 4 }} />
        <div style={{ position: "absolute", left: 0, right: 0, top: 60, height: 90, background: "repeating-linear-gradient(180deg,#3a3a3a 0 10px,#2c2c2c 10px 20px)" }} />
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 58, background: "linear-gradient(180deg,#7a4f22,#4d3115)", borderTop: "4px solid #000", borderRadius: "0 0 8px 8px" }} />
        <div style={{ position: "absolute", left: 26, bottom: 70, display: "flex", gap: 16 }}>
          {[0, 1, 2, 3].map((i) => <div key={i} style={{ width: 60, height: 20, background: "#c9c9c9", border: "3px solid #000", borderRadius: 3 }} />)}
        </div>
      </div>
      <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
        {data.rows.map(([o], i) => (
          <div key={i} style={{ width: 16, height: 16, background: i <= idx ? YELLOW : "#4a4a4a", border: "3px solid #000" }} />
        ))}
      </div>
      {data.note && <div style={{ ...mono, fontSize: 30, color: "#9aa3ad" }}>{data.note}</div>}
    </div>
  );
};

/* ------------------------------------------------------------------ Toys R Us: the aisle */

export const ToyAisle: React.FC<{ data: { sign: string; sub: string; mode: "closing" | "open" } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const slam = spring({ frame: frame - 26, fps, config: { damping: 9, stiffness: 220 } });
  const colors = ["#e8412f", "#f5a623", "#2fa84f", "#2f6fe8", "#8e44ad", "#e84393"];
  const closing = data.mode === "closing";
  return (
    <div style={{ position: "absolute", inset: 0, background: closing ? "#1b1b1b" : "#f7f7f2", overflow: "hidden" }}>
      {[0, 1, 2].map((shelf) => (
        <div key={shelf} style={{ position: "absolute", left: 0, right: 0, top: 60 + shelf * 240, height: 210 }}>
          <div style={{ display: "flex", gap: 14, padding: "0 22px", alignItems: "flex-end", height: 170 }}>
            {Array.from({ length: 7 }).map((_, i) => {
              const gone = closing && (i + shelf * 3) % 7 < Math.floor(interpolate(frame, [4, 40], [0, 7], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
              const h = 90 + ((i * 37 + shelf * 19) % 70);
              return (
                <div key={i} style={{ flex: 1, height: h, background: colors[(i + shelf) % colors.length], border: "4px solid rgba(0,0,0,.55)", borderRadius: 4, opacity: gone ? 0.12 : 1, boxShadow: closing ? "none" : "0 6px 0 rgba(0,0,0,.25)" }} />
              );
            })}
          </div>
          <div style={{ height: 26, background: closing ? "#333" : "#c9c2ae", borderTop: "5px solid rgba(0,0,0,.5)" }} />
        </div>
      ))}
      <div style={{ position: "absolute", left: 40, right: 40, top: 300, transform: `rotate(${closing ? -3 : 2}deg) scale(${0.6 + 0.4 * slam})`, opacity: slam }}>
        <div style={{ background: closing ? "#ffe600" : NAVY, border: "8px solid #000", padding: "18px 10px", textAlign: "center", boxShadow: "14px 14px 0 rgba(0,0,0,.55)" }}>
          <div style={{ ...inter, fontWeight: 900, fontSize: 84, color: closing ? "#c0392b" : YELLOW, lineHeight: 1, letterSpacing: -2 }}>{data.sign.toUpperCase()}</div>
          <div style={{ ...inter, fontWeight: 900, fontSize: 40, color: closing ? "#111" : "#fff", marginTop: 8 }}>{data.sub}</div>
        </div>
      </div>
    </div>
  );
};
