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
import { GRAY, TEAL, NAVY, YELLOW, bevel, pixel, inter, vt, Win, Scanlines, KenBurns, Cursor } from "./ui";
import { VhsPhoto, PolaroidHook, InterlaceHook, FolderScene, BrowserScene, ReceiptScene, CalendarScene, GalleryScene } from "./Extra";
import { VhsTape, SplitFlapBoard, MemberCard, DueDateCard, BlueLight, AskPage, CrtSet, StockCrash, CatalogBook, LevelUp, CartSlot, ToyAisle } from "./Story";

type Word = { w: string; s: number; e: number };
type Scene = { say: string; text?: string; lines: string[]; kind: string; audio: string; frames: number; words?: Word[] };
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
  chartTitle?: string;
  props: [string, string][];
  propsTitle?: string;
  propsName?: string;
  ticker?: { to: number; prefix?: string; suffix?: string; decimals?: number };
  found?: { query: string; unit: string; from: number; to: number; result: string };
  timeline: [string, string][];
  subject?: string;
  heroPos?: string;
  hero2Pos?: string;
  hookStyle?: "vhs" | "polaroid" | "interlace";
  hookCaption?: string;
  folder?: { path: string; from: number; to: number; unit: string; keepLabels?: string[] };
  browser?: { url: string; mode: "error" | "redirect"; message?: string; redirectTo?: string; pageTitle?: string };
  receipt?: { title: string; sub?: string; lines: [string, string][]; total: [string, string] };
  calendar?: { start: string; end: string; days: number; startLabel: string; endLabel: string };
  gallery?: { src: string; caption: string }[];
  propsSkin?: "dialog" | "plaque" | "manila";
  tape?: any; flap?: any; card?: any; duedate?: any; bluelight?: any; ask?: any;
  crt?: any; crt2?: any; crash?: any; catalog?: any; levelup?: any; cart?: any; aisle?: any; aisle2?: any;
};

/* ---------- scene bodies ---------- */

/** Scene 2: search dialog counts down from 9,000 to 1, then reveals the Bend store */
const FoundScene: React.FC<{ script: Script }> = ({ script }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fd = script.found || { query: "stores", unit: "Stores found", from: 9000, to: 1, result: "" };
  const count = Math.round(interpolate(frame, [8, 60], [fd.from, fd.to], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const reveal = spring({ frame: frame - 62, fps, config: { damping: 16, stiffness: 120 } });
  const dots = ".".repeat((Math.floor(frame / 8) % 3) + 1);
  const bars = Math.round(interpolate(frame, [8, 60], [0, 30], { extrapolateRight: "clamp", extrapolateLeft: "clamp" }));
  return (
    <>
      <KenBurns src={script.hero} seed={1} pos={script.heroPos} dim={interpolate(reveal, [0, 1], [0.7, 0.05])} />
      <div style={{ position: "absolute", left: 40, right: 40, top: 60, opacity: 1 - reveal * 0.1, transform: `translateY(${(1 - Math.min(1, frame / 10)) * -40}px)` }}>
        <Win title={`Find: ${fd.query}`} small>
          <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ ...pixel, fontSize: 44 }}>Searching worldwide{dots}</div>
            <div style={{ ...bevel(true), padding: 6, display: "flex", gap: 4 }}>
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} style={{ flex: 1, height: 22, background: i < bars ? NAVY : "transparent" }} />
              ))}
            </div>
            <div style={{ ...pixel, fontSize: 60 }}>
              {fd.unit}: <span style={{ color: count === fd.to ? "#008000" : "#c00000", fontWeight: 700 }}>{count.toLocaleString("en-US")}</span>
            </div>
            {reveal > 0.05 && (
              <div style={{ ...pixel, fontSize: 46, transform: `scale(${reveal})`, transformOrigin: "left" }}>
                ▶ {fd.result}
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
      <div style={{ ...pixel, fontSize: 44, marginBottom: 10 }}>{script.chartTitle || "Over the years"}</div>
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
  const tk = script.ticker || { to: 0, prefix: "", suffix: "" };
  const priceRaw = interpolate(frame, [30, 90], [0, tk.to], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const price = tk.decimals ? priceRaw.toFixed(tk.decimals) : Math.round(priceRaw).toLocaleString("en-US");
  const skin = script.propsSkin || "dialog";
  const rows = script.props.map(([k, v], i) => {
    const start = 12 + i * 16;
    const chars = Math.max(0, Math.floor((frame - start) * 1.6));
    return [k, v.slice(0, chars) + (frame >= start && chars < v.length ? "_" : ""), frame >= start] as [string, string, boolean];
  });
  const big = tk.to > 0 ? `${tk.prefix || ""}${price}${tk.suffix || ""}` : "";

  if (skin === "plaque") {
    return (
      <>
        <KenBurns src={script.hero} seed={2} pos={script.heroPos} dim={0.6} />
        <div style={{ position: "absolute", left: 60, right: 60, top: 90, background: "linear-gradient(160deg,#d9b24c,#9c7a1e 55%,#e8cd7a)", border: "10px solid #5c4409", padding: "28px 32px", boxShadow: "0 20px 40px rgba(0,0,0,.55)" }}>
          <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 52, color: "#3a2b04", letterSpacing: 2, textShadow: "1px 1px 0 rgba(255,255,255,.5)", borderBottom: "5px solid #5c4409", paddingBottom: 12 }}>
            {script.propsName || script.subject}
          </div>
          {rows.map(([k, v, on], i) => (
            <div key={i} style={{ display: "flex", gap: 20, marginTop: 14, fontFamily: "Menlo, monospace", fontWeight: 700, fontSize: 40, color: "#3a2b04", opacity: on ? 1 : 0.2, textShadow: "1px 1px 0 rgba(255,255,255,.45)" }}>
              <span style={{ width: 300, color: "#6b5210", flexShrink: 0 }}>{k}</span><span>{v}</span>
            </div>
          ))}
          {big && <div style={{ textAlign: "center", marginTop: 14, fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 104, color: "#3a2b04", textShadow: "2px 2px 0 rgba(255,255,255,.5)" }}>{big}</div>}
        </div>
      </>
    );
  }
  if (skin === "manila") {
    return (
      <div style={{ position: "absolute", inset: 0, background: "#3f4a3a", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 860, background: "#d9c489", border: "4px solid #a48f52", boxShadow: "0 22px 44px rgba(0,0,0,.5)", position: "relative", padding: "34px 34px 42px", transform: "rotate(-1deg)" }}>
          <div style={{ position: "absolute", left: 40, top: -46, width: 300, height: 50, background: "#d9c489", border: "4px solid #a48f52", borderBottom: "none", borderRadius: "10px 10px 0 0" }} />
          <div style={{ position: "absolute", left: 60, top: -36, fontFamily: "Menlo, monospace", fontWeight: 700, fontSize: 30, color: "#5b4a1c" }}>FILE</div>
          <div style={{ background: "#fdfaf0", border: "2px solid #b9a771", padding: "24px 28px" }}>
            <div style={{ fontFamily: "Menlo, monospace", fontWeight: 700, fontSize: 44, color: "#2b2b2b", borderBottom: "3px solid #2b2b2b", paddingBottom: 10, letterSpacing: 2 }}>
              {(script.propsName || script.subject || "").toUpperCase()}
            </div>
            {rows.map(([k, v, on], i) => (
              <div key={i} style={{ display: "flex", gap: 20, marginTop: 16, fontFamily: "Menlo, monospace", fontWeight: 700, fontSize: 36, color: "#2b2b2b", opacity: on ? 1 : 0.18 }}>
                <span style={{ width: 300, color: "#7a6a3a", flexShrink: 0 }}>{k}</span><span>{v}</span>
              </div>
            ))}
            {big && <div style={{ marginTop: 18, textAlign: "center", fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 96, color: "#8b1a1a" }}>{big}</div>}
          </div>
        </div>
      </div>
    );
  }
  return (
    <>
      <KenBurns src={script.hero} seed={2} pos={script.heroPos} dim={0.55} />
      <div style={{ position: "absolute", left: 40, right: 40, top: 30 }}>
        <Win title={script.propsTitle || "Properties"} small>
          <div style={{ padding: "22px 26px", display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", gap: 14, alignItems: "center", marginBottom: 4 }}>
              <div style={{ width: 70, height: 70, background: YELLOW, border: "4px solid #000", display: "flex", alignItems: "center", justifyContent: "center", ...pixel, fontSize: 44 }}>{(script.propsName || script.subject || "?").slice(0, 1)}</div>
              <div style={{ ...pixel, fontSize: 46 }}>{script.propsName || script.subject}</div>
            </div>
            <div style={{ height: 4, background: "#808080" }} />
            {rows.map(([k, v, on], i) => (
              <div key={i} style={{ display: "flex", gap: 20, ...pixel, fontSize: 42, opacity: on ? 1 : 0.25 }}>
                <span style={{ width: 300, color: "#555", flexShrink: 0 }}>{k}:</span><span>{v}</span>
              </div>
            ))}
            {big && <div style={{ marginTop: 6, display: "flex", justifyContent: "center" }}>
              <div style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 110, color: NAVY, letterSpacing: -2 }}>{big}</div>
            </div>}
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
      <KenBurns src={script.hero2 || script.hero} seed={3} pos={script.hero2 ? script.hero2Pos : script.heroPos} dim={0.62} />
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


/** Word-by-word captions on continuous bars: each line is one white bar that grows as words are spoken;
 *  the current word is highlighted inside the bar. The hook shows its whole sentence from frame 1. */
const WordCaptions: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const words: Word[] = scene.words || (scene.text || scene.say).split(/\s+/).map((w, i) => ({ w, s: i * 0.3, e: i * 0.3 + 0.3 }));
  const allFromStart = scene.kind === "hook";
  const n = words.length;
  const size = n <= 8 ? 78 : n <= 14 ? 64 : 56;
  const budget = Math.floor(940 / (size * 0.58));
  // pre-wrap into lines so the bars never reflow while words appear
  const lines: Word[][] = [[]];
  let used = 0;
  for (const wd of words) {
    const len = wd.w.length + 1;
    if (used + len > budget && lines[lines.length - 1].length) {
      lines.push([]);
      used = 0;
    }
    lines[lines.length - 1].push(wd);
    used += len;
  }
  const isKey = (w: string) => /[\d$]/.test(w) || /^(yes|last|one|only)$/i.test(w.replace(/[.,!?]/g, ""));
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
      {lines.map((line, li) => {
        const shown = line.filter((wd) => allFromStart || t >= wd.s - 0.04);
        if (!shown.length) return <div key={li} style={{ height: size * 1.25 }} />;
        const first = line[0];
        const pop = spring({ frame: frame - Math.round(first.s * fps), fps, config: { damping: 14, stiffness: 200 } });
        return (
          <div
            key={li}
            style={{
              display: "inline-block",
              background: "#fff",
              boxShadow: "8px 8px 0 #000",
              padding: "6px 22px",
              fontFamily: inter.fontFamily,
              fontWeight: 900,
              fontSize: size,
              lineHeight: 1.15,
              color: "#000",
              whiteSpace: "nowrap",
              transform: allFromStart ? "none" : `scale(${0.85 + 0.15 * pop})`,
            }}
          >
            {line.map((wd, i) => {
              const spoken = allFromStart || t >= wd.s - 0.04;
              const current = t >= wd.s - 0.04 && t < wd.e + 0.06;
              if (!spoken) return null;
              const key = isKey(wd.w);
              return (
                <span
                  key={i}
                  style={{
                    padding: "0 8px",
                    marginRight: i < line.length - 1 ? 6 : 0,
                    color: current ? NAVY : key ? YELLOW : "#000",
                    background: current ? YELLOW : key ? NAVY : "transparent",
                    borderRadius: 2,
                  }}
                >
                  {wd.w}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};


/** A different way in for every scene, so the window opening never repeats. */
const entrance = (kind: string, frame: number, fps: number): React.CSSProperties => {
  const s = spring({ frame, fps, config: { damping: 16, stiffness: 130 } });
  const snappy = spring({ frame, fps, config: { damping: 11, stiffness: 200 } });
  switch (kind) {
    case "hook": {
      // CRT power-on: a bright horizontal line that opens vertically
      const y = interpolate(frame, [0, 10], [0.02, 1], { extrapolateRight: "clamp" });
      const x = interpolate(frame, [0, 4], [0.4, 1], { extrapolateRight: "clamp" });
      return { transform: `scale(${x}, ${y})`, filter: frame < 8 ? `brightness(${3 - frame / 4})` : "none" };
    }
    case "found":
      // slides in from the right with a small overshoot
      return { transform: `translateX(${(1 - snappy) * 1200}px)` };
    case "chart":
      // maximises from the bottom-left corner like a taskbar button
      return { transform: `scale(${0.15 + 0.85 * s})`, transformOrigin: "0% 100%", opacity: Math.min(1, s * 2), background: "#fff" };
    case "props":
      // drops from the top and settles
      return { transform: `translateY(${(1 - snappy) * -1400}px)` };
    case "timeline":
      // wipes open left to right
      return { clipPath: `inset(0 ${(1 - s) * 100}% 0 0)` };
    case "folder":
      // cascades open from the top like an Explorer window
      return { clipPath: `inset(0 0 ${(1 - s) * 100}% 0)` };
    case "browser":
      return { transform: `translateY(${(1 - snappy) * 1200}px)` };
    case "receipt":
      // rolls in from above like paper
      return { clipPath: `inset(0 0 ${(1 - s) * 100}% 0)`, transform: `translateY(${(1 - s) * -60}px)` };
    case "calendar":
      return { transform: `perspective(1200px) rotateY(${(1 - s) * 80}deg)`, transformOrigin: "left", opacity: Math.min(1, s * 1.5) };
    case "gallery":
      return { opacity: Math.min(1, s * 2) };
    case "tape":
    case "cart":
      return { transform: `translateY(${(1 - snappy) * -1300}px)` };
    case "flap":
      return { clipPath: `inset(${(1 - s) * 100}% 0 0 0)` };
    case "card":
    case "crash":
      return { transform: `translateX(${(1 - snappy) * -1200}px)` };
    case "duedate":
    case "catalog":
      return { transform: `scale(${0.5 + 0.5 * s}) rotate(${(1 - s) * 8}deg)`, opacity: s };
    case "bluelight":
    case "levelup":
      return { opacity: Math.min(1, s * 2.2), transform: `scale(${0.94 + 0.06 * s})` };
    case "ask":
      return { clipPath: `inset(0 ${(1 - s) * 100}% 0 0)` };
    case "crt":
    case "crt2":
      return { transform: `scale(${0.2 + 0.8 * s})`, opacity: Math.min(1, s * 2) };
    case "aisle":
    case "aisle2":
      return { transform: `translateX(${(1 - snappy) * 1200}px)` };
    default:
      // outro: zooms in with a slight twist
      return { transform: `scale(${0.6 + 0.4 * s}) rotate(${(1 - s) * -6}deg)`, opacity: s };
  }
};

/* ---------- scene frame ---------- */

const titlesFor = (subject: string): Record<string, string> => {
  const s = subject.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "video";
  return { hook: `${s}.avi`, found: "find.exe", chart: `${s}.xls`, props: "properties", timeline: "history.txt", outro: "404memoryfound.com", folder: "Exploring", browser: "Internet Explorer", receipt: "receipt.txt", calendar: "calendar.exe", gallery: "My Pictures", tape: `${s}.vhs`, flap: "departures", card: "member.card", duedate: "due_dates.txt", bluelight: "in_store.avi", ask: "Ask Jeeves", crt: "tv_guide.exe", crt2: "tv_guide.exe", crash: "ticker.exe", catalog: `${s}_catalog`, levelup: "levelup.dat", cart: "cartridge.bin", aisle: "aisle_07.avi", aisle2: "aisle_07.avi" };
};

const SceneView: React.FC<{ scene: Scene; script: Script; index: number; offset: number; total: number }> = ({ scene, script, index, offset, total }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const kind = scene.kind;
  const body =
    kind === "hook" ? (script.hookStyle === "polaroid" ? <PolaroidHook src={script.hero} pos={script.heroPos} caption={script.hookCaption} />
      : script.hookStyle === "interlace" ? <InterlaceHook src={script.hero} pos={script.heroPos} label={script.hookCaption} />
      : <VhsPhoto src={script.hero} pos={script.heroPos} />) :
    kind === "folder" ? <FolderScene data={script.folder!} /> :
    kind === "browser" ? <BrowserScene data={script.browser!} bg={script.hero2 || script.hero} pos={script.hero2Pos || script.heroPos} /> :
    kind === "receipt" ? <ReceiptScene data={script.receipt!} /> :
    kind === "calendar" ? <CalendarScene data={script.calendar!} /> :
    kind === "gallery" ? <GalleryScene items={script.gallery || []} /> :
    kind === "tape" ? <VhsTape data={script.tape} /> :
    kind === "flap" ? <SplitFlapBoard data={script.flap} /> :
    kind === "card" ? <MemberCard data={script.card} /> :
    kind === "duedate" ? <DueDateCard data={script.duedate} /> :
    kind === "bluelight" ? <BlueLight data={script.bluelight} /> :
    kind === "ask" ? <AskPage data={script.ask} /> :
    kind === "crt" ? <CrtSet data={script.crt} /> :
    kind === "crt2" ? <CrtSet data={script.crt2} /> :
    kind === "crash" ? <StockCrash data={script.crash} /> :
    kind === "catalog" ? <CatalogBook data={script.catalog} /> :
    kind === "levelup" ? <LevelUp data={script.levelup} /> :
    kind === "cart" ? <CartSlot data={script.cart} /> :
    kind === "aisle" ? <ToyAisle data={script.aisle} /> :
    kind === "aisle2" ? <ToyAisle data={script.aisle2} /> :
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
      {scene.audio ? <Audio src={staticFile(scene.audio)} /> : null}
      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />

      <div style={{ position: "absolute", top: 70, left: 60, right: 60, ...bevel(), display: "flex", alignItems: "center", gap: 18, padding: "10px 18px" }}>
        <Img src={staticFile("logo.png")} style={{ width: 64, height: 64 }} />
        <span style={{ ...pixel, fontSize: 52 }}>404 Memory Found</span>
        <span style={{ marginLeft: "auto", ...pixel, fontSize: 44 }}>{index + 1}/{script.scenes.length}</span>
      </div>

      {/* the window stays open for the whole video; only its contents animate in */}
      <div style={{ position: "absolute", top: 210, left: 60, right: 60, height: 900, ...(off < 1 ? { transform: `scaleY(${off})` } : {}) }}>
        <Win title={titlesFor(script.subject || script.title.split(" ")[1] || "video")[kind] || "window"} style={{ height: "100%" }}>
          <div style={{ position: "absolute", inset: 0, ...entrance(kind, frame, fps) }}>{body}</div>
        </Win>
      </div>

      <div style={{ position: "absolute", top: 1170, left: 40, right: 40, minHeight: 420, display: "flex", alignItems: "center", justifyContent: "center", padding: 10 }}>
        <WordCaptions scene={scene} />
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
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      {/* music bed: synthesised chiptune from gen_music.py, quiet under the voice, fades out with the CRT-off */}
      <Audio
        src={staticFile("music.wav")}
        loop
        volume={(f) => interpolate(f, [0, fps * 0.8, total - fps * 1.2, total], [0, 0.04, 0.04, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
      />
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

/** Cover / thumbnail: hero photo inside the Win95 window, 1 to 3 words of cover text in the top third,
 *  subject label below. Rendered with `remotion still ... Cover`. Text comes from script.cover. */
export const Cover: React.FC<{ script: Script & { cover?: { text: string; sub?: string; pos?: string; oneLine?: boolean } } }> = ({ script }) => {
  const c = script.cover || { text: script.subject || "", sub: "" };
  const words = c.oneLine ? [c.text] : c.text.split(" ");
  return (
    <AbsoluteFill style={{ background: TEAL }}>
      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
      <div style={{ position: "absolute", top: 70, left: 60, right: 60, ...bevel(), display: "flex", alignItems: "center", gap: 18, padding: "10px 18px" }}>
        <Img src={staticFile("logo.png")} style={{ width: 64, height: 64 }} />
        <span style={{ ...pixel, fontSize: 52 }}>404 Memory Found</span>
      </div>
      <div style={{ position: "absolute", top: 210, left: 60, right: 60, height: 1180 }}>
        <Win title={`${(script.subject || "video").toLowerCase().replace(/[^a-z0-9]+/g, "_")}.avi`} style={{ height: "100%" }}>
          <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
            <Img src={staticFile(script.hero)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: (script.cover && script.cover.pos) || script.heroPos || "center 35%", filter: "contrast(1.08) saturate(1.15)" }} />
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 45%, rgba(0,0,0,.35) 100%)" }} />
            <Scanlines strength={0.12} />
            <div style={{ position: "absolute", top: 40, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              {words.map((w, i) => (
                <span key={i} style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: c.oneLine ? 150 : words.length > 2 ? 150 : 190, lineHeight: 1, color: YELLOW, background: NAVY, padding: "6px 34px", boxShadow: "12px 12px 0 #000", letterSpacing: -3, transform: `rotate(${i % 2 ? 1.5 : -1.5}deg)` }}>
                  {w}
                </span>
              ))}
            </div>
            {c.sub && (
              <div style={{ position: "absolute", bottom: 50, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
                <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 64, color: "#000", background: "#fff", padding: "6px 26px", boxShadow: "8px 8px 0 #000" }}>{c.sub}</span>
              </div>
            )}
          </div>
        </Win>
      </div>
      <div style={{ position: "absolute", top: 1440, left: 60, right: 60, display: "flex", justifyContent: "center" }}>
        <span style={{ fontFamily: inter.fontFamily, fontWeight: 900, fontSize: 92, color: "#fff", textShadow: "8px 8px 0 #000", textAlign: "center", lineHeight: 1.05 }}>{script.subject}</span>
      </div>
      <div style={{ position: "absolute", bottom: 90, left: 0, right: 0, textAlign: "center", fontFamily: vt.fontFamily, fontSize: 40, color: "#fff" }}>Sourced. Dated. No invented numbers.</div>
    </AbsoluteFill>
  );
};
