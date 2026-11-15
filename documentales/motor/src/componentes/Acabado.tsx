import React from "react";
import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { T } from "../tema";

/** Grano de película + viñeta + gradación (fría/cálida). Va encima de todo salvo los subtítulos. */
export const Acabado: React.FC<{ grano?: number; vineta?: number; tinte?: string }> = ({ grano = 0.08, vineta = 0.65, tinte }) => {
  const f = useCurrentFrame();
  const sem = Math.floor(f / 2);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {tinte && <AbsoluteFill style={{ background: tinte, mixBlendMode: "soft-light" }} />}
      <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,${vineta}) 100%)` }} />
      <svg width="100%" height="100%" style={{ position: "absolute", opacity: grano, mixBlendMode: "overlay" }}>
        <filter id={`g${sem}`}><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={Math.floor(random(sem) * 1000)} /></filter>
        <rect width="100%" height="100%" filter={`url(#g${sem})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Título cinematográfico: entra con tracking de letras y desenfoque; sale con fundido. */
export const TituloCine: React.FC<{ texto: string; sub?: string; desde: number; hasta: number; y?: number; tam?: number; color?: string; serif?: boolean }> = ({ texto, sub, desde, hasta, y = 0.2, tam = 0.065, color = T.marfil, serif }) => {
  const f = useCurrentFrame();
  const { height } = useVideoConfig();
  const e = interpolate(f, [desde, desde + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.2, 0.7, 0.2, 1) });
  const s = interpolate(f, [hasta - 12, hasta], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (f < desde || f > hasta) return null;
  return (
    <div style={{ position: "absolute", top: height * y, left: 0, right: 0, textAlign: "center", opacity: e * s, filter: `blur(${(1 - e) * 12}px)` }}>
      <div style={{ fontFamily: serif ? T.serif : T.fuente, fontWeight: serif ? 700 : 900, fontSize: height * tam, color, letterSpacing: `${0.05 + (1 - e) * 0.4}em`, textShadow: "0 6px 30px rgba(0,0,0,0.7)" }}>{texto}</div>
      {sub && <div style={{ marginTop: 18, fontFamily: T.fuente, fontWeight: 700, fontSize: height * 0.018, color: T.dorado, letterSpacing: "0.4em", textTransform: "uppercase" }}>{sub}</div>}
    </div>
  );
};

/** Etiqueta honesta para recreaciones / rutas esquemáticas. */
export const Nota: React.FC<{ texto: string; desde: number; hasta: number }> = ({ texto, desde, hasta }) => {
  const f = useCurrentFrame();
  const { height } = useVideoConfig();
  const o = Math.min(interpolate(f, [desde, desde + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), interpolate(f, [hasta - 10, hasta], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return <div style={{ position: "absolute", top: height * 0.12, right: 160, opacity: o, fontFamily: T.fuente, fontSize: height * 0.0135, fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase", color: T.marfil, background: "rgba(10,14,24,0.6)", border: `1px solid ${T.dorado}`, padding: "8px 14px", borderRadius: 8 }}>{texto}</div>;
};
