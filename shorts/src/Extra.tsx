import React from "react";
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Button, Cursor, GRAY, KenBurns, NAVY, Scanlines, Win, YELLOW, bevel, inter, pixel, vt } from "./ui";

/* Extra scene kinds and hook styles. Every visual here takes its data from the video's script so no two
   videos look the same: a folder of icons being deleted, a 90s browser that errors or redirects, a receipt
   printing out, a calendar flipping months, a polaroid gallery, and hook styles beyond the VHS look. */

/* ---------- hook styles ---------- */

/** Instant photo developing from white, with a slight hand-held wobble */
export const PolaroidHook: React.FC<{ src: string; pos?: string; caption?: string }> = ({ src, pos = "center 35%", caption }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dev = interpolate(frame, [6, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const drop = spring({ frame, fps, config: { damping: 13, stiffness: 90 } });
  const wob = Math.sin(frame / 9) * 0.6;
  return (
    <div style={{ position: "absolute", inset: 0, background: "#3a3a3a", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 760, padding: "26px 26px 120px", background: "#f7f5ef", boxShadow: "0 30px 60px rgba(0,0,0,.5)", transform: `translateY(${(1 - drop) * -900}px) rotate(${-3 + wob}deg)` }}>
        <div style={{ width: "100%", height: 720, background: "#e8e4d8", overflow: "hidden", position: "relative" }}>
          <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: pos, filter: `brightness(${0.3 + 0.7 * dev}) contrast(${0.6 + 0.5 * dev}) saturate(${dev}) sepia(${1 - dev})`, opacity: 0.15 + 0.85 * dev }} />
          <div style={{ position: "absolute", inset: 0, background: `rgba(255,255,255,${(1 - dev) * 0.8})` }} />
        </div>
        {caption && <div style={{ marginTop: 26, fontFamily: vt.fontFamily, fontSize: 52, color: "#2b2b2b", textAlign: "center" }}>{caption}</div>}
      </div>
    </div>
  );
};

/** Dial-up era image load: the photo arrives in horizontal bands, with a loading percentage */
export const InterlaceHook: React.FC<{ src: string; pos?: string; label?: string }> = ({ src, pos = "center 35%", label = "photo.jpg" }) => {
  const frame = useCurrentFrame();
  const bands = 24;
  const shown = Math.min(bands, Math.floor(interpolate(frame, [4, 78], [0, bands + 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })));
  const pct = Math.round((shown / bands) * 100);
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff" }}>
      <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(#ddd 1px, transparent 1px)", backgroundSize: "100% 12px" }} />
      {Array.from({ length: bands }).map((_, i) => (
        <div key={i} style={{ position: "absolute", left: 0, right: 0, top: `${(i / bands) * 100}%`, height: `${100 / bands + 0.2}%`, overflow: "hidden", opacity: i < shown ? 1 : 0 }}>
          <Img src={staticFile(src)} style={{ position: "absolute", left: 0, top: `-${i * 100}%`, width: "100%", height: `${bands * 100}%`, objectFit: "cover", objectPosition: pos, filter: i === shown - 1 ? "blur(3px)" : "none" }} />
        </div>
      ))}
      <div style={{ position: "absolute", left: 24, bottom: 24, ...bevel(), padding: "8px 18px", display: "flex", alignItems: "center", gap: 18 }}>
        <span style={{ ...pixel, fontSize: 40 }}>{label}</span>
        <div style={{ ...bevel(true), width: 300, height: 30, padding: 3 }}>
          <div style={{ width: `${pct}%`, height: "100%", background: NAVY }} />
        </div>
        <span style={{ ...pixel, fontSize: 40 }}>{pct}%</span>
      </div>
      <Scanlines strength={0.06} />
    </div>
  );
};

/* ---------- scene kinds ---------- */

const FolderIcon: React.FC<{ label: string; gone: boolean; keep: boolean; delay: number }> = ({ label, gone, keep, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const vanish = gone ? spring({ frame: frame - delay, fps, config: { damping: 12, stiffness: 180 } }) : 0;
  return (
    <div style={{ width: 150, display: "flex", flexDirection: "column", alignItems: "center", gap: 4, opacity: 1 - vanish, transform: `scale(${1 - vanish * 0.6})` }}>
      <div style={{ width: 84, height: 62, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: 36, height: 14, background: keep ? YELLOW : "#e8c84a", border: "3px solid #7a6a1a", borderBottom: "none" }} />
        <div style={{ position: "absolute", left: 0, top: 12, width: 84, height: 50, background: keep ? YELLOW : "#f0d65a", border: "3px solid #7a6a1a" }} />
        {keep && <div style={{ position: "absolute", inset: -8, border: `4px dashed ${NAVY}` }} />}
      </div>
      <span style={{ ...pixel, fontSize: 26, color: keep ? NAVY : "#000", background: keep ? YELLOW : "transparent", padding: "0 4px" }}>{label}</span>
    </div>
  );
};

/** Explorer folder full of icons; a delete dialog removes them until only `to` remain (highlighted). */
export const FolderScene: React.FC<{ data: { path: string; from: number; to: number; unit: string; keepLabels?: string[] } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const N = 40;
  const removed = Math.round(interpolate(frame, [12, 110], [0, N - data.to], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const count = Math.round(interpolate(frame, [12, 110], [data.from, data.to], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const done = frame > 112;
  const dots = ".".repeat((Math.floor(frame / 8) % 3) + 1);
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff" }}>
      <div style={{ ...bevel(true), margin: 0, padding: "6px 14px", ...pixel, fontSize: 36, background: "#fff", borderWidth: 4 }}>Address: {data.path}</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "18px 8px", padding: 20 }}>
        {Array.from({ length: N }).map((_, i) => {
          const keepIdx = i >= N - data.to;
          const label = keepIdx && data.keepLabels ? data.keepLabels[i - (N - data.to)] || data.unit : `${data.unit}_${String(i + 1).padStart(2, "0")}`;
          return <FolderIcon key={i} label={label} gone={i < removed} keep={keepIdx && done} delay={12 + (i / (N - data.to)) * 98} />;
        })}
      </div>
      <div style={{ position: "absolute", left: 120, right: 120, top: 380 }}>
        <Win title={done ? "Done" : "Deleting..."} small>
          <div style={{ padding: "18px 24px", display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ ...pixel, fontSize: 40 }}>{done ? `${data.to} ${data.unit}s left.` : `Closing ${data.unit}s${dots}`}</div>
            <div style={{ ...bevel(true), padding: 5, display: "flex", gap: 4 }}>
              {Array.from({ length: 28 }).map((_, i) => (
                <div key={i} style={{ flex: 1, height: 22, background: i < Math.round(((N - data.to - (N - data.to - removed)) / (N - data.to)) * 28) ? NAVY : "transparent" }} />
              ))}
            </div>
            <div style={{ ...pixel, fontSize: 56 }}>
              {data.unit}s: <span style={{ color: done ? "#008000" : "#c00000" }}>{count.toLocaleString("en-US")}</span>
            </div>
          </div>
        </Win>
      </div>
    </div>
  );
};

/** 90s browser: the URL is typed, the page loads, then either an error dialog or a redirect to another site. */
export const BrowserScene: React.FC<{ data: { url: string; mode: "error" | "redirect"; message?: string; redirectTo?: string; pageTitle?: string }; bg?: string; pos?: string }> = ({ data, bg, pos }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const typed = data.url.slice(0, Math.max(0, Math.floor((frame - 6) * 1.4)));
  const typingDone = typed.length >= data.url.length;
  const loadStart = 6 + Math.ceil(data.url.length / 1.4) + 8;
  const load = interpolate(frame, [loadStart, loadStart + 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const result = frame > loadStart + 44;
  const pop = spring({ frame: frame - (loadStart + 44), fps, config: { damping: 12, stiffness: 160 } });
  const redirectTyped = data.mode === "redirect" && result ? (data.redirectTo || "").slice(0, Math.floor((frame - loadStart - 44) * 1.6)) : "";
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff" }}>
      {bg && <KenBurns src={bg} seed={4} dim={0.75} pos={pos} />}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, ...bevel(), borderWidth: 4, display: "flex", flexDirection: "column", gap: 6, padding: "8px 12px" }}>
        <div style={{ display: "flex", gap: 14, ...pixel, fontSize: 34 }}>
          <span>File</span><span>Edit</span><span>View</span><span>Go</span><span>Favorites</span><span>Help</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Button label="Back" style={{ fontSize: 32, padding: "4px 18px" }} />
          <Button label="Stop" pressed={!result && typingDone} style={{ fontSize: 32, padding: "4px 18px" }} />
          <div style={{ flex: 1, ...bevel(true), background: "#fff", padding: "6px 14px", ...pixel, fontSize: 40, whiteSpace: "nowrap", overflow: "hidden" }}>
            {data.mode === "redirect" && result ? `http://${redirectTyped}` : `http://${typed}`}{!result && !typingDone ? "_" : ""}
          </div>
        </div>
      </div>
      {typingDone && !result && (
        <div style={{ position: "absolute", left: 40, right: 40, top: 200, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
          <span style={{ ...pixel, fontSize: 44, color: "#fff", textShadow: "2px 2px 0 #000" }}>Connecting to {data.url}...</span>
          <div style={{ ...bevel(true), width: 700, padding: 5, display: "flex", gap: 4 }}>
            {Array.from({ length: 30 }).map((_, i) => (
              <div key={i} style={{ flex: 1, height: 24, background: i < Math.round(load * 30) ? NAVY : "transparent" }} />
            ))}
          </div>
        </div>
      )}
      {result && data.mode === "error" && (
        <div style={{ position: "absolute", left: 60, right: 60, top: 300, transform: `scale(${0.7 + 0.3 * pop})`, opacity: pop }}>
          <Win title="Internet Explorer" small>
            <div style={{ padding: "22px 26px", display: "flex", gap: 24, alignItems: "flex-start" }}>
              <div style={{ width: 90, height: 90, borderRadius: 45, background: "#c00000", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 66, flexShrink: 0 }}>×</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div style={{ ...pixel, fontSize: 44 }}>The page cannot be displayed.</div>
                <div style={{ ...pixel, fontSize: 40, color: "#333" }}>{data.message}</div>
                <div style={{ marginTop: 6 }}><Button label="OK" /></div>
              </div>
            </div>
          </Win>
          <Cursor from={[900, 700]} to={[420, 560]} at={loadStart + 50} clickAt={loadStart + 80} />
        </div>
      )}
      {result && data.mode === "redirect" && (
        <div style={{ position: "absolute", left: 60, right: 60, top: 300, transform: `scale(${0.7 + 0.3 * pop})`, opacity: pop }}>
          <Win title={data.pageTitle || data.redirectTo || ""} small>
            <div style={{ padding: "22px 26px", display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ ...pixel, fontSize: 44 }}>Redirecting...</div>
              <div style={{ ...pixel, fontSize: 40, color: "#333" }}>{data.message}</div>
              <div style={{ ...bevel(true), background: "#fff", padding: "8px 14px", ...pixel, fontSize: 44, color: NAVY }}>{data.redirectTo}</div>
            </div>
          </Win>
        </div>
      )}
    </div>
  );
};

/** A till receipt printing line by line, the total in red. */
export const ReceiptScene: React.FC<{ data: { title: string; sub?: string; lines: [string, string][]; total: [string, string] } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const rows = data.lines.length + 3;
  const shown = Math.floor(interpolate(frame, [6, 6 + rows * 12], [0, rows + 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const mono: React.CSSProperties = { fontFamily: "Menlo, Courier New, monospace", fontWeight: 700, color: "#222" };
  return (
    <div style={{ position: "absolute", inset: 0, background: "#6d6d6d", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 70, background: "#333", borderBottom: "8px solid #111" }} />
      <div style={{ position: "absolute", left: 120, right: 120, top: 40, background: "#fbfbf6", padding: "30px 36px 50px", transform: `translateY(${-Math.max(0, (rows + 1 - shown)) * 0}px) rotate(-1deg)`, boxShadow: "0 20px 40px rgba(0,0,0,.4)", clipPath: `inset(0 0 ${Math.max(0, 100 - (shown / (rows + 1)) * 100)}% 0)` }}>
        <div style={{ ...mono, fontSize: 46, textAlign: "center", letterSpacing: 2 }}>{data.title}</div>
        {data.sub && <div style={{ ...mono, fontSize: 32, textAlign: "center", color: "#666", marginBottom: 14 }}>{data.sub}</div>}
        <div style={{ borderTop: "3px dashed #999", margin: "14px 0" }} />
        {data.lines.map(([k, v], i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", ...mono, fontSize: 40, padding: "8px 0", opacity: i + 2 < shown ? 1 : 0 }}>
            <span>{k}</span><span>{v}</span>
          </div>
        ))}
        <div style={{ borderTop: "3px dashed #999", margin: "14px 0" }} />
        <div style={{ display: "flex", justifyContent: "space-between", ...mono, fontSize: 56, color: "#c00000", opacity: data.lines.length + 2 < shown ? 1 : 0 }}>
          <span>{data.total[0]}</span><span>{data.total[1]}</span>
        </div>
        <div style={{ ...mono, fontSize: 30, color: "#888", textAlign: "center", marginTop: 20, opacity: data.lines.length + 3 < shown ? 1 : 0 }}>*** THANK YOU ***</div>
      </div>
    </div>
  );
};

/** Calendar pages flip from a start month to an end month while a day counter climbs. */
export const CalendarScene: React.FC<{ data: { start: string; end: string; days: number; startLabel: string; endLabel: string } }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = new Date(data.start + "T00:00:00Z");
  const e = new Date(data.end + "T00:00:00Z");
  const months = (e.getUTCFullYear() - s.getUTCFullYear()) * 12 + (e.getUTCMonth() - s.getUTCMonth());
  const prog = interpolate(frame, [10, 10 + months * 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const mi = Math.min(months, Math.floor(prog * months + 0.0001));
  const cur = new Date(Date.UTC(s.getUTCFullYear(), s.getUTCMonth() + mi, 1));
  const days = Math.round(prog * data.days);
  const flip = spring({ frame: frame - (10 + mi * 12), fps, config: { damping: 14, stiffness: 200 } });
  const name = cur.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  const first = cur.getUTCDay();
  const dim = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth() + 1, 0)).getUTCDate();
  const markStart = mi === 0 ? s.getUTCDate() : -1;
  const markEnd = mi === months ? e.getUTCDate() : -1;
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff", padding: 30 }}>
      <div style={{ ...bevel(), padding: 10, transform: `rotateX(${(1 - flip) * -70}deg)`, transformOrigin: "top" }}>
        <div style={{ background: NAVY, color: "#fff", fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 52, textAlign: "center", padding: "8px 0" }}>{name}</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 6, padding: 10, background: "#fff" }}>
          {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => <div key={i} style={{ ...pixel, fontSize: 32, textAlign: "center", color: "#666" }}>{d}</div>)}
          {Array.from({ length: first }).map((_, i) => <div key={"b" + i} />)}
          {Array.from({ length: dim }).map((_, i) => {
            const d = i + 1;
            const isS = d === markStart, isE = d === markEnd;
            return (
              <div key={d} style={{ ...pixel, fontSize: 40, textAlign: "center", padding: "6px 0", background: isS ? "#008000" : isE ? "#c00000" : "transparent", color: isS || isE ? "#fff" : "#000", border: isS || isE ? "3px solid #000" : "3px solid transparent" }}>{d}</div>
            );
          })}
        </div>
      </div>
      <div style={{ position: "absolute", left: 30, right: 30, bottom: 30, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div style={{ ...pixel, fontSize: 36 }}>
          <div><span style={{ background: "#008000", color: "#fff", padding: "0 10px" }}>■</span> {data.startLabel}</div>
          <div><span style={{ background: "#c00000", color: "#fff", padding: "0 10px" }}>■</span> {data.endLabel}</div>
        </div>
        <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 110, color: NAVY, lineHeight: 1 }}>
          {days}<span style={{ fontSize: 44, marginLeft: 10 }}>days</span>
        </div>
      </div>
    </div>
  );
};

/** Two to four photos drop in as prints with captions. */
export const GalleryScene: React.FC<{ items: { src: string; caption: string }[] }> = ({ items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = items.length;
  return (
    <div style={{ position: "absolute", inset: 0, background: "#2f4f4f", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(rgba(255,255,255,.08) 2px, transparent 2px)", backgroundSize: "28px 28px" }} />
      {items.map((it, i) => {
        const s = spring({ frame: frame - 6 - i * 22, fps, config: { damping: 13, stiffness: 110 } });
        const rot = [-6, 5, -3, 4][i % 4];
        const x = n === 2 ? [40, 420][i] : [30, 380, 200][i % 3];
        const y = n === 2 ? [60, 380][i] : [40, 300, 560][i % 3];
        return (
          <div key={i} style={{ position: "absolute", left: x, top: y, width: 520, padding: "16px 16px 60px", background: "#f7f5ef", boxShadow: "0 18px 36px rgba(0,0,0,.45)", transform: `translateY(${(1 - s) * -800}px) rotate(${rot}deg)`, opacity: s }}>
            <div style={{ width: "100%", height: 340, overflow: "hidden", background: "#ddd" }}>
              <Img src={staticFile(it.src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            <div style={{ marginTop: 14, fontFamily: vt.fontFamily, fontSize: 40, color: "#222", textAlign: "center" }}>{it.caption}</div>
          </div>
        );
      })}
    </div>
  );
};

/** VHS look: RGB split that jitters, a tracking bar rolling down, PLAY OSD */
export const VhsPhoto: React.FC<{ src: string; pos?: string }> = ({ src, pos = "center 35%" }) => {
  const frame = useCurrentFrame();
  const jitter = Math.sin(frame * 1.7) * 4 + (frame % 23 === 0 ? 14 : 0);
  const zoom = interpolate(frame, [0, 120], [1.05, 1.14], { extrapolateRight: "clamp" });
  const bar = ((frame * 9) % 1400) - 200;
  const img: React.CSSProperties = { position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", objectPosition: pos };
  return (
    <div style={{ position: "absolute", inset: 0, background: "#000", overflow: "hidden" }}>
      <Img src={staticFile(src)} style={{ ...img, transform: `scale(${zoom})`, filter: "contrast(1.1) saturate(1.2)" }} />
      <Img src={staticFile(src)} style={{ ...img, transform: `translateX(${jitter}px) scale(${zoom})`, mixBlendMode: "screen", opacity: 0.35, filter: "sepia(1) hue-rotate(-50deg) saturate(6)" }} />
      <Img src={staticFile(src)} style={{ ...img, transform: `translateX(${-jitter}px) scale(${zoom})`, mixBlendMode: "screen", opacity: 0.35, filter: "sepia(1) hue-rotate(140deg) saturate(6)" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: bar, height: 46, background: "rgba(255,255,255,.35)", filter: "blur(2px)" }} />
      <Scanlines strength={0.22} />
      <div style={{ position: "absolute", top: 26, left: 30, fontFamily: vt.fontFamily, fontSize: 64, color: "#fff", textShadow: "3px 3px 0 #000" }}>▶ PLAY</div>
      <div style={{ position: "absolute", top: 26, right: 30, fontFamily: vt.fontFamily, fontSize: 56, color: "#fff", textShadow: "3px 3px 0 #000" }}>
        SP 0:{String(Math.floor(frame / 30)).padStart(2, "0")}:{String(frame % 30).padStart(2, "0")}
      </div>
    </div>
  );
};
