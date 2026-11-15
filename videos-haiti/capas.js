// Capas extra para videos 16:9: cámara, cortinillas de capítulo, banderas, rótulos,
// insignias de organizaciones, minimapas, partículas, grano y viñeta.
// Banderas simplificadas (dominio público). Insignias = texto, NO logotipos oficiales.
const FLAGS = {
  SV: '<rect width="60" height="40" fill="#0F47AF"/><rect y="13.3" width="60" height="13.4" fill="#fff"/><circle cx="30" cy="20" r="4.2" fill="#E5B22B"/>',
  HT: '<rect width="60" height="20" fill="#00209F"/><rect y="20" width="60" height="20" fill="#D21034"/><rect x="24" y="15" width="12" height="10" fill="#fff"/>',
  US: Array.from({ length: 13 }, (_, i) => `<rect y="${i * 40 / 13}" width="60" height="${40 / 13}" fill="${i % 2 ? "#fff" : "#B22234"}"/>`).join("") + '<rect width="26" height="21.5" fill="#3C3B6E"/>' +
      Array.from({ length: 20 }, (_, i) => `<circle cx="${3 + (i % 5) * 5}" cy="${3 + Math.floor(i / 5) * 5}" r="1" fill="#fff"/>`).join(""),
  DO: '<rect width="60" height="40" fill="#fff"/><rect width="26" height="17" fill="#002D62"/><rect x="34" width="26" height="17" fill="#CE1126"/><rect y="23" width="26" height="17" fill="#CE1126"/><rect x="34" y="23" width="26" height="17" fill="#002D62"/><circle cx="30" cy="20" r="3" fill="#0B6E3B"/>',
  KE: '<rect width="60" height="12" fill="#111"/><rect y="12" width="60" height="16" fill="#fff"/><rect y="14" width="60" height="12" fill="#BB0000"/><rect y="28" width="60" height="12" fill="#006600"/><ellipse cx="30" cy="20" rx="5.5" ry="11" fill="#BB0000" stroke="#111" stroke-width="1.5"/>',
};
function flag(c, w = 60) { return `<svg width="${w}" height="${w * 2 / 3}" viewBox="0 0 60 40" style="border-radius:4px;box-shadow:0 2px 10px rgba(0,0,0,.4);flex:none">${FLAGS[c]}</svg>`; }
const BADGES = { ONU: ["#5B92E5", "ONU"], GSF: ["#2B3F8C", "GSF"], AI: ["#E8C400", "AI"], MSF: ["#D9232E", "MSF"], ACLED: ["#6B7390", "ACLED"] };
function badge(k, s = 56) { const [c, t] = BADGES[k]; return `<span style="display:inline-flex;align-items:center;justify-content:center;width:${s}px;height:${s}px;border-radius:50%;background:${c};color:${k === "AI" ? "#111" : "#fff"};font-weight:900;font-size:${t.length > 3 ? s * .26 : s * .34}px;letter-spacing:.02em;flex:none;box-shadow:0 0 0 3px rgba(255,255,255,.15)">${t}</span>`; }

// ---- minimapa de Puerto Príncipe con chinchetas
function miniMap(id, w, h, centro, ancho, pins) {
  const alto = ancho * h / w, x0 = centro[0] - ancho / 2, y0 = centro[1] - alto / 2;
  let s = `<svg width="${w}" height="${h}" viewBox="${x0} ${y0} ${ancho} ${alto}" style="border-radius:20px;background:#0D1428">`;
  GEO.countries.filter(c => c.iso === "DOM").forEach(c => s += `<path d="${c.d}" fill="#22305A" stroke="rgba(255,255,255,.2)" stroke-width="${ancho / 400}"/>`);
  GEO.hti.forEach(d => s += `<path d="${d.d}" fill="${d.name === "Ouest" ? "#4A2130" : "#2A1F2E"}" stroke="rgba(255,255,255,.25)" stroke-width="${ancho / 500}"/>`);
  pins.forEach((p, i) => { const [x, y] = lonlat(p.lon, p.lat);
    s += `<g id="${id}_p${i}" opacity="0"><circle cx="${x}" cy="${y}" r="${ancho / 45}" fill="${p.c}" stroke="#fff" stroke-width="${ancho / 300}"/>` +
         `<text x="${x + ancho / 30}" y="${y + ancho / 110}" fill="#F5F2EA" font-size="${ancho / 20}" font-weight="800" font-family="Inter">${p.t}</text></g>`; });
  return s + "</svg>";
}

// ---- cámara
const CAMPUNCH = []; // [t, zoom, xPct, yPct, dur]
function camara(t) {
  let z = 1, ox = 50, oy = 45;
  for (const [a, zz, x, y, d] of CAMPUNCH) {
    if (REC) rec(a, "tick");
    const k = eio(pr(t, a, a + .6)) * (1 - eio(pr(t, a + d - .6, a + d)));
    if (k > 0) { z = 1 + (zz - 1) * k; ox = x; oy = y; }
  }
  const dz = 1 + .012 * Math.sin(t * .35), dx = Math.sin(t * .23) * 10, dy = Math.cos(t * .19) * 6;
  const w = $("world"); w.style.transformOrigin = `${ox}% ${oy}%`;
  w.style.transform = `translate(${dx}px,${dy}px) scale(${z * dz})`;
  $("bgGlow").style.transform += ` scale(${1 + (z - 1) * .4})`;
}

// ---- cortinillas de capítulo
const CAPS = []; // [t, num, titulo, color]
function cortinilla(t) {
  const el = $("chap"); let vis = false;
  for (const [a, n, tit, col] of CAPS) {
    const p = pr(t, a - .35, a + .95);
    if (REC) rec(a - .35, "whoosh");
    if (p > 0 && p < 1) {
      vis = true;
      $("chapBar").style.background = col;
      const entra = eio(pr(p, 0, .3)), sale = eio(pr(p, .7, 1));
      $("chapBar").style.transform = `translateX(${(-1 + entra + sale) * 110}%) skewX(-12deg)`;
      $("chapTxt").style.opacity = pr(p, .22, .32) * (1 - pr(p, .68, .78));
      $("chapNum").textContent = n; $("chapTit").textContent = tit;
      $("chapTxt").style.transform = `translateX(${(1 - eo(pr(p, .2, .45))) * 60}px)`;
    }
  }
  el.style.display = vis ? "block" : "none";
}

// ---- rótulos de personas
const ROTULOS = []; // [t, dur, nombre, cargo, bandera]
function rotulos(t) {
  if (REC) ROTULOS.forEach(r => rec(r[0], "pop"));
  let cur = null; for (const r of ROTULOS) if (t >= r[0] && t < r[0] + r[1]) cur = r;
  const el = $("lt");
  if (!cur) { el.style.opacity = 0; return; }
  const [a, d, n, c, f] = cur; const k = eo(pr(t, a, a + .4)) * (1 - eo(pr(t, a + d - .4, a + d)));
  if (el.dataset.k !== n) { el.innerHTML = `${flag(f, 66)}<div><div style="font-size:34px;font-weight:900">${n}</div><div style="font-size:22px;font-weight:700;color:var(--gold);letter-spacing:.08em;text-transform:uppercase">${c}</div></div>`; el.dataset.k = n; }
  el.style.opacity = k; el.style.transform = `translateX(${(1 - k) * -60}px)`;
}

// ---- primer plano: partículas, grano, viñeta
function capasInit() {
  const st = $("stage");
  st.insertAdjacentHTML("beforeend", `
  <div id="parts" class="abs" style="inset:0;pointer-events:none;z-index:3"></div>
  <div id="vign" class="abs" style="inset:0;pointer-events:none;z-index:3;background:radial-gradient(ellipse at 50% 50%,transparent 55%,rgba(0,0,0,.55) 100%)"></div>
  <div id="grain" class="abs" style="inset:0;pointer-events:none;z-index:6;opacity:.07;mix-blend-mode:overlay"></div>
  <div id="lt" class="abs" style="left:100px;top:742px;z-index:5;display:flex;align-items:center;gap:20px;padding:16px 28px 16px 18px;border-radius:18px;background:rgba(10,15,30,.88);border-left:8px solid var(--gold);opacity:0"></div>
  <div id="chap" class="abs" style="inset:0;z-index:7;display:none;overflow:hidden">
    <div id="chapBar" class="abs" style="left:-10%;top:0;width:120%;height:100%"></div>
    <div id="chapTxt" class="abs" style="left:0;width:1920px;top:430px;text-align:center;color:#0A0F1E">
      <div id="chapNum" style="font-size:40px;font-weight:900;letter-spacing:.2em"></div>
      <div id="chapTit" style="font-size:96px;font-weight:900;letter-spacing:-.02em"></div></div></div>`);
  // grano precalculado
  const c = document.createElement("canvas"); c.width = c.height = 256; const g = c.getContext("2d"); const im = g.createImageData(256, 256);
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < im.data.length; i += 4) { const v = rnd() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0); $("grain").style.backgroundImage = `url(${c.toDataURL()})`;
  $("parts").innerHTML = Array.from({ length: 28 }, (_, i) => `<div class="pt abs" style="width:${2 + (i % 3) * 2}px;height:${2 + (i % 3) * 2}px;border-radius:50%;background:rgba(255,210,90,${.15 + (i % 4) * .08})"></div>`).join("");
}
function capas(t) {
  const f = Math.floor(t * 24); $("grain").style.backgroundPosition = `${(f * 73) % 256}px ${(f * 151) % 256}px`;
  document.querySelectorAll(".pt").forEach((e, i) => { const sp = 8 + (i % 5) * 6; const x = (i * 211 + t * sp) % 2000 - 40; const y = 1080 - ((i * 97 + t * sp * .6) % 1160);
    e.style.left = x + "px"; e.style.top = y + "px"; });
  camara(t); cortinilla(t); rotulos(t);
}
