import React, { useMemo } from "react";
import { AbsoluteFill, Easing, interpolate, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { Caption, createTikTokStyleCaptions } from "@remotion/captions";
import { SEGURA, T } from "../tema";

/**
 * Subtítulos cinematográficos: máx. 2 líneas, blanco de alto contraste, palabras clave en dorado,
 * aparición suave sin rebotes, dentro de la zona segura de TikTok / Reels / Shorts.
 */
export const Subtitulos: React.FC<{ captions: Caption[]; claves?: RegExp; msPorPagina?: number; fondo?: boolean }> = ({ captions, claves = /^$/, msPorPagina = 1500, fondo = true }) => {
  const { fps } = useVideoConfig();
  const { pages } = useMemo(() => createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: msPorPagina }), [captions, msPorPagina]);
  return (
    <AbsoluteFill>
      {pages.map((pg, i) => {
        const desde = Math.round((pg.startMs / 1000) * fps);
        const sig = pages[i + 1];
        const hasta = sig ? Math.round((sig.startMs / 1000) * fps) : desde + Math.round(2.5 * fps);
        if (hasta <= desde) return null;
        return (
          <Sequence key={i} from={desde} durationInFrames={hasta - desde} layout="none">
            <Pagina tokens={pg.tokens} inicioMs={pg.startMs} claves={claves} fondo={fondo} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const Pagina: React.FC<{ tokens: { text: string; fromMs: number; toMs: number }[]; inicioMs: number; claves: RegExp; fondo: boolean }> = ({ tokens, inicioMs, claves, fondo }) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const ahoraMs = inicioMs + (f / fps) * 1000;
  const entra = interpolate(f, [0, 6], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <div style={{
      position: "absolute", left: SEGURA.izq, right: SEGURA.der, bottom: SEGURA.abajo, display: "flex", justifyContent: "center",
      opacity: entra, transform: `translateY(${(1 - entra) * 18}px)`,
    }}>
      <div style={{
        maxWidth: width - SEGURA.izq - SEGURA.der, textAlign: "center", fontFamily: T.fuente, fontWeight: 800,
        fontSize: Math.round(height * 0.032), lineHeight: 1.22, color: T.marfil, padding: fondo ? "14px 26px" : 0,
        borderRadius: 18, background: fondo ? "rgba(10,14,24,0.55)" : "transparent",
        display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
        textShadow: "0 3px 14px rgba(0,0,0,0.85)",
      }}>
        {tokens.map((t, i) => {
          const dicha = ahoraMs >= t.fromMs;
          const limpio = t.text.trim().replace(/[.,;:¿?¡!«»"]/g, "");
          const clave = /\d/.test(limpio) || claves.test(limpio);
          return (
            <span key={i} style={{ color: dicha ? (clave ? T.dorado : "#FFFFFF") : "rgba(238,232,218,0.45)", whiteSpace: "pre" }}>{t.text}</span>
          );
        })}
      </div>
    </div>
  );
};
