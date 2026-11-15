// Shared engine for the Haiti reels: easing, scenes, captions, map, human figures, sound cues.
const $ = id => document.getElementById(id);
const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const pr = (t, a, b) => cl((t - a) / (b - a));
const eo = x => 1 - Math.pow(1 - x, 3);
const eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const eb = x => { const c = 1.70158, c3 = c + 1; return 1 + c3 * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const NS = "http://www.w3.org/2000/svg";
let REC = null; const rec = (a, n) => { if (REC && a > 0) REC.push([a, n]); };
function pop(el, t, a, d = .45, dy = 50) { rec(a, "pop"); if (typeof el === "string") el = $(el); const p = pr(t, a, a + d); el.style.opacity = eo(p); el.style.transform = `translateY(${(1 - eo(p)) * dy}px) scale(${.9 + .1 * eb(p)})`; return p; }
function slideX(el, t, a, dx = -120, d = .45) { rec(a, "pop"); if (typeof el === "string") el = $(el); const p = eo(pr(t, a, a + d)); el.style.opacity = p; el.style.transform = `translateX(${(1 - p) * dx}px)`; }
function slam(el, t, a, rot = -10) { rec(a, "thud"); if (REC) SHAKES.push([a, 10]); if (typeof el === "string") el = $(el); const p = pr(t, a, a + .28); el.style.opacity = p > 0 ? 1 : 0; el.style.transform = `rotate(${rot}deg) scale(${p > 0 ? 1 + 1.5 * (1 - eo(p)) : 2})`; }
function zoomIn(el, t, a, from = 1.8, d = .4) { rec(a, "thud"); if (typeof el === "string") el = $(el); const p = pr(t, a, a + d); el.style.opacity = p > 0 ? eo(p) : 0; el.style.transform = `scale(${1 + (from - 1) * (1 - eo(p))})`; }
function scene(id, t, a, b, f = .35) { rec(a - .05, "whoosh");
  const el = $(id); const vin = pr(t, a, a + f), vout = pr(t, b - f, b); const v = Math.min(vin, 1 - vout);
  el.style.opacity = v; el.style.display = v <= 0 ? "none" : "block";
  const drift = 1 + .025 * pr(t, a, b);
  el.style.transform = `translateY(${(1 - eo(vin)) * 60 - eo(vout) * 60}px) scale(${drift * (1 + .05 * (1 - eo(vin)))})`;
  el.style.filter = vout > 0 ? `blur(${vout * 10}px)` : "none"; return v;
}
function count(el, t, a, b, to, fmt) { if (REC) for (let k = a; k < b; k += .16) rec(k, "tick"); if (typeof el === "string") el = $(el); const v = to * eo(pr(t, a, b)); el.textContent = fmt ? fmt(v) : String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
const fmtN = (dec = 0) => v => v.toLocaleString("es-ES", { minimumFractionDigits: dec, maximumFractionDigits: dec });
const SHAKES = [];
function shakeAt(t) { for (const [a, amp] of SHAKES) { const p = pr(t, a, a + .35); if (p > 0 && p < 1) { const k = (1 - p) * amp; return `translate(${Math.sin(t * 90) * k}px,${Math.cos(t * 77) * k}px)`; } } return ""; }

// ---------- human figures (isotype pictograms), viewBox 0 0 40 100 ----------
const BODY = c => `<rect x="8" y="22" width="24" height="38" rx="5" fill="${c}"/><rect x="11" y="54" width="8.5" height="45" rx="4" fill="${c}"/><rect x="20.5" y="54" width="8.5" height="45" rx="4" fill="${c}"/>`;
const FIG = {
  man: c => `<circle cx="20" cy="11" r="9" fill="${c}"/>${BODY(c)}`,
  woman: c => `<circle cx="20" cy="11" r="9" fill="${c}"/><path d="M12 22h16q3 0 4 3l6 42q0 3-3 3H5q-3 0-3-3l6-42q1-3 4-3z" fill="${c}"/><rect x="12" y="66" width="7" height="33" rx="3.5" fill="${c}"/><rect x="21" y="66" width="7" height="33" rx="3.5" fill="${c}"/>`,
  child: c => `<g transform="translate(6 30) scale(.7)"><circle cx="20" cy="11" r="10" fill="${c}"/>${BODY(c)}</g>`,
  student: c => `<g transform="translate(6 30) scale(.7)"><rect x="0" y="26" width="10" height="26" rx="3" fill="${c}" opacity=".6"/><circle cx="20" cy="11" r="10" fill="${c}"/>${BODY(c)}</g>`,
  soldier: c => `<path d="M9 12a11 10 0 0 1 22 0v2H9z" fill="${c}"/><circle cx="20" cy="14" r="8" fill="${c}"/>${BODY(c)}<rect x="11" y="30" width="18" height="12" rx="2" fill="#0A0F1E" opacity=".35"/>`,
  walker: c => `<circle cx="22" cy="11" r="9" fill="${c}"/><path d="M14 23h12q4 0 4 4l1 28q0 3-3 3h-1l6 36q1 3-2 4l-2 0q-3 1-4-2l-6-30-6 30q-1 3-4 2h-2q-3-1-2-4l6-36h-1q-3 0-3-3l1-28q0-4 4-4z" fill="${c}"/><rect x="28" y="30" width="11" height="16" rx="3" fill="${c}" opacity=".7"/>`,
};
function fig(type, color, h = 100, extra = "") { const w = h * .4; return `<svg width="${w}" height="${h}" viewBox="0 0 40 100" ${extra}>${FIG[type](color)}</svg>`; }
// grid of n figures; returns html; each svg gets class "f"
function figRow(n, type, color, h, gap = 10) { let s = ""; for (let i = 0; i < n; i++) { const tp = Array.isArray(type) ? type[i % type.length] : type; s += `<div class="f" style="margin:0 ${gap / 2}px ${gap}px;opacity:0">${fig(tp, color, h)}</div>`; } return s; }
// animate figures in a container appearing one by one; optional color fn(i)
function figAnim(id, t, a, step, colorFn) {
  const els = $(id).querySelectorAll(".f");
  if (REC) { let last = -1; els.forEach((e, i) => { const k = a + i * step; if (k - last >= .12 && i < 14) { rec(k, "tick"); last = k; } }); }
  els.forEach((e, i) => { const p = pr(t, a + i * step, a + i * step + .3); e.style.opacity = eo(p); e.style.transform = `translateY(${(1 - eb(p)) * 30}px)`;
    if (colorFn) { const c = colorFn(i, t); if (c) e.querySelectorAll("path,circle,rect").forEach(x => x.setAttribute("fill", c)); } });
}

// ---------- map ----------
let CAM = { x0: 0, y0: 0, w: 1 };
function mapInit(opts = {}) {
  const g = $("mapC"), h = $("mapH");
  GEO.countries.forEach(c => { if (c.iso === "HTI") return; const p = document.createElementNS(NS, "path"); p.setAttribute("d", c.d); p.id = "c-" + c.iso;
    p.setAttribute("fill", c.iso === "DOM" ? "#2A3560" : "#1A2342"); p.setAttribute("stroke", "rgba(245,242,234,.25)"); p.setAttribute("stroke-width", "1"); p.setAttribute("vector-effect", "non-scaling-stroke"); g.appendChild(p); });
  GEO.hti.forEach(d => { const p = document.createElementNS(NS, "path"); p.setAttribute("d", d.d); p.id = "dep-" + d.name.replace(/[^A-Za-z]/g, "");
    p.setAttribute("fill", "#3A2530"); p.setAttribute("stroke", "#0A0F1E"); p.setAttribute("stroke-width", "1.5"); p.setAttribute("vector-effect", "non-scaling-stroke"); h.appendChild(p); });
}
const VW = window.VW || 1080, VH = window.VH || 1920;
function cam(cx, cy, w, fy = .5) { const hh = w * VH / VW; CAM = { x0: cx - w / 2, y0: cy - fy * hh, w }; $("map").setAttribute("viewBox", `${CAM.x0} ${CAM.y0} ${w} ${hh}`); }
function scr(x, y) { const s = VW / CAM.w; return [(x - CAM.x0) * s, (y - CAM.y0) * s]; }
function lonlat(lon, lat) { const C = Math.cos(19 * Math.PI / 180); return [(lon + 72.5) * C * 100, -(lat - 19) * 100]; }
const lerp = (a, b, p) => a + (b - a) * p;
const lerpLog = (a, b, p) => Math.exp(Math.log(a) + (Math.log(b) - Math.log(a)) * p);
function placeAt(id, x, y) { const [sx, sy] = scr(x, y); const e = $(id); e.style.left = sx + "px"; e.style.top = sy + "px"; }
function dep(name) { return $("dep-" + name.replace(/[^A-Za-z]/g, "")); }

// ---------- captions (word timings from Whisper) ----------
let CHUNKS = [];
function buildChunks(words, maxChars = 34) {
  const out = []; let cur = [];
  const flush = () => { if (cur.length) out.push({ s: cur[0].s, e: cur[cur.length - 1].e, words: cur }); cur = []; };
  words.forEach((w, i) => {
    const prev = cur[cur.length - 1];
    if (prev && (w.s - prev.e > .45)) flush();
    const len = cur.reduce((a, x) => a + x.w.length + 1, 0);
    if (cur.length && len + w.w.length > maxChars) flush();
    cur.push(w);
    if (/[.,:;?!—]$/.test(w.w) && cur.length >= 2) flush();
  });
  flush(); CHUNKS = out;
}
let capKey = null, KEYRE = /^$/;
function caption(t) {
  let cur = null;
  for (let i = 0; i < CHUNKS.length; i++) { const p = CHUNKS[i], nx = CHUNKS[i + 1]; if (t >= p.s - .08 && t < (nx ? Math.min(nx.s - .08, p.e + 1.0) : p.e + .6)) { cur = p; break; } }
  const cap = $("cap"); if (!cur) { cap.innerHTML = ""; capKey = null; return; }
  if (capKey !== cur) { cap.innerHTML = `<div>${cur.words.map(w => `<span>${w.w}</span>`).join("")}</div>`; capKey = cur; }
  const spans = cap.querySelectorAll("span"); const ap = eo(pr(t, cur.s - .08, cur.s + .15));
  cap.firstChild.style.opacity = ap; cap.firstChild.style.transform = `translateY(${(1 - ap) * 24}px)`;
  cur.words.forEach((w, i) => { const sp = spans[i]; const on = t >= w.s - .03; const bare = w.w.replace(/[,.:;¿?¡!—()"]/g, "");
    const isKey = /\d/.test(bare) || KEYRE.test(bare);
    sp.style.color = on ? (isKey ? "var(--gold)" : "var(--ink)") : "rgba(245,242,234,.35)";
    const k = pr(t, w.s, w.s + .15); sp.style.transform = `translateY(${on && k < 1 ? -6 * (1 - k) : 0}px)`; });
}
// ---------- frame chrome ----------
function chrome(t, audioEnd) {
  $("progIn").style.width = (cl(t / audioEnd) * 100) + "%";
  $("bgGlow").style.transform = `translate(${Math.sin(t * .25) * 60}px,${Math.cos(t * .2) * 50}px)`;
  $("stage").style.transform = shakeAt(t);
  const capOn = 1 - pr(t, audioEnd + .1, audioEnd + .4); $("cap").style.opacity = capOn; $("capBg").style.opacity = capOn;
  caption(t);
}
// ---------- page scaffold ----------
function chromeInit(topic, chipColor = "red") {
  const st = $("stage");
  st.insertAdjacentHTML("afterbegin", `<div id="bgGlow"></div><div id="grid"></div>
  <svg id="map" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice"><g id="mapC"></g><g id="mapH"></g><g id="mapX"></g></svg>
  <div id="flag" class="abs"><i style="background:var(--blue)"></i><i style="background:var(--red)"></i></div>
  <div id="top" class="abs"><span class="chip ${chipColor}">Haití 2026</span><span class="chip">${topic}</span></div>
  <div id="prog" class="abs"><div id="progIn"></div></div>`);
  st.insertAdjacentHTML("beforeend", `<div id="capBg" class="abs"></div><div id="cap" class="abs"></div>`);
  if (window.GEO) mapInit();
  if (window.WORDS) buildChunks(WORDS);
}

function buildCues(extra = []) {
  REC = []; SHAKES.length = 0; render(0); const list = REC.concat(extra).sort((x, y) => x[0] - y[0]); REC = null;
  const out = []; const lastBy = {};
  for (const [t, n] of list) { if (lastBy[n] !== undefined && t - lastBy[n] < .12) continue; if (n === "pop" && out.some(c => c[1] === "whoosh" && Math.abs(c[0] - t) < .15)) continue; out.push([+t.toFixed(3), n]); lastBy[n] = t; }
  window.CUES = out; render(0);
}
// ---------- icons (24x24 stroke) ----------
const IC = {
  coin: '<circle cx="12" cy="12" r="9"/><path d="M14.5 9.5c-.5-1-1.5-1.5-2.5-1.5-1.7 0-3 .9-3 2s1.3 1.7 3 2 3 .9 3 2-1.3 2-3 2c-1 0-2-.5-2.5-1.5M12 6.5v11"/>',
  block: '<rect x="2" y="8" width="20" height="6" rx="1"/><path d="M6 8l4 6M12 8l4 6M18 8l3 4.5M5 14v6M19 14v6"/>',
  route: '<circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/><path d="M8.5 19H16a3.5 3.5 0 0 0 0-7H8a3.5 3.5 0 0 1 0-7h7.5"/>',
  plane: '<path d="M10.5 21l1.5-6 6 3V15l-6-5V4.5a1.5 1.5 0 0 0-3 0V10L3 15v3l6-3 1.5 6"/>',
  school: '<path d="M3 21h18M5 21V10l7-5 7 5v11M9 21v-5h6v5"/><path d="M12 5V2h3"/>',
  hospital: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M12 8v8M8 12h8"/>',
  bowl: '<path d="M3 11h18a9 9 0 0 1-18 0zM8 20h8M14 3l-3 7"/>',
  house: '<path d="M3 11l9-7 9 7v10H3z"/><path d="M9 21v-6h6v6"/>',
  music: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
  book: '<path d="M4 4h6a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H4zM20 4h-6a3 3 0 0 0-3 3"/><path d="M20 4v15h-7"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
  heart: '<path d="M12 21s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6-8 11-8 11z"/>',
  ballot: '<rect x="3" y="10" width="18" height="11" rx="2"/><path d="M8 10V4h8v6M8 14h8"/>',
  shield: '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  rain: '<path d="M7 15a5 5 0 1 1 1.5-9.8A6 6 0 0 1 20 9a4 4 0 0 1-2 6z"/><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M5 5l14 14" stroke="#E2333F"/>',
  doc: '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h8M9 17h6"/>',
  tent: '<path d="M12 3L2 21h20zM12 3v18M8 21l4-7 4 7"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5"/><circle cx="17" cy="9" r="2.8"/><path d="M16 14.6c2.7.1 4.8 2 5.5 5"/>',
  drum: '<ellipse cx="12" cy="8" rx="8" ry="3"/><path d="M4 8v8c0 1.7 3.6 3 8 3s8-1.3 8-3V8M4 8l16 8M20 8L4 16"/>',
};
function icon(name, size = 48, color = "#F5F2EA", sw = 2) { return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${IC[name]}</svg>`; }

// ---------- anclas: tiempo de una frase dentro de WORDS (sincronía automática con el audio)
const _norm = w => w.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9ñ%]/g, "");
function at(frase, n = 1, desde = 0) {
  const obj = frase.split(/\s+/).map(_norm).filter(Boolean); let vistos = 0;
  for (let i = 0; i < WORDS.length; i++) {
    if (WORDS[i].s < desde) continue;
    let ok = true;
    for (let k = 0; k < obj.length; k++) { if (!WORDS[i + k] || _norm(WORDS[i + k].w) !== obj[k]) { ok = false; break; } }
    if (ok && ++vistos === n) return WORDS[i].s;
  }
  console.warn("ancla no encontrada:", frase); window.FALTAN = (window.FALTAN || []).concat(frase); return 1e9;
}
