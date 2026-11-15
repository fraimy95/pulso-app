import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";

/** Fotograma clave de cámara: escala (zoom), desplazamiento en px y rotación en grados. */
export type ClaveCamara = { f: number; escala?: number; x?: number; y?: number; rot?: number };

const suave = Easing.bezier(0.45, 0, 0.2, 1);

function valor(claves: ClaveCamara[], frame: number, k: keyof Omit<ClaveCamara, "f">, porDefecto: number) {
  const pts = claves.filter((c) => c[k] !== undefined);
  if (pts.length === 0) return porDefecto;
  if (pts.length === 1) return pts[0][k] as number;
  return interpolate(frame, pts.map((p) => p.f), pts.map((p) => p[k] as number), {
    easing: suave, extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
}

/**
 * Cámara virtual reutilizable: Slow Push-In, Pull-Out, Pan y Tracking se expresan con fotogramas clave.
 * Ej.: push-in lento  [{f:0, escala:1}, {f:240, escala:1.12}]
 *      pan lateral    [{f:0, x:0}, {f:150, x:-200}]
 */
export const Camara: React.FC<{ claves: ClaveCamara[]; origen?: string; children: React.ReactNode }> = ({ claves, origen = "50% 50%", children }) => {
  const f = useCurrentFrame();
  const s = valor(claves, f, "escala", 1), x = valor(claves, f, "x", 0), y = valor(claves, f, "y", 0), r = valor(claves, f, "rot", 0);
  return (
    <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px) scale(${s}) rotate(${r}deg)`, transformOrigin: origen }}>
      {children}
    </AbsoluteFill>
  );
};

/** Rack focus simulado: desenfoca una capa entre dos instantes. */
export const Enfoque: React.FC<{ desde: number; hasta: number; maxBlur?: number; invertir?: boolean; children: React.ReactNode }> = ({ desde, hasta, maxBlur = 10, invertir, children }) => {
  const f = useCurrentFrame();
  let p = interpolate(f, [desde, hasta], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: suave });
  if (invertir) p = 1 - p;
  return <AbsoluteFill style={{ filter: `blur(${p * maxBlur}px)` }}>{children}</AbsoluteFill>;
};
