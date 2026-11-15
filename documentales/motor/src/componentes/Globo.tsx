import React, { useMemo } from "react";
import { AbsoluteFill, Easing, interpolate, interpolateColors, useCurrentFrame, useVideoConfig } from "remotion";
import { geoGraticule10, geoOrthographic, geoPath, geoInterpolate, GeoPermissibleObjects } from "d3-geo";
import { feature } from "topojson-client";
import mundo50 from "world-atlas/countries-50m.json";
import { T } from "../tema";

// Natural Earth vía world-atlas (dominio público). Ids = ISO 3166-1 numérico.
const PAISES = (feature(mundo50 as any, (mundo50 as any).objects.countries) as any).features as any[];
const suave = Easing.bezier(0.45, 0, 0.2, 1);

/** Clave de cámara geográfica: centro [lon, lat] y radio del globo en px (zoom). */
export type ClaveGlobo = { f: number; lon: number; lat: number; radio: number };
export type Marcador = { lon: number; lat: number; texto: string; aparece: number; color?: string; lado?: "der" | "izq" };
export type Ruta = { puntos: [number, number][]; desde: number; hasta: number; color?: string; discontinua?: boolean; etiqueta?: string };
export type Resalte = { id: string; color: string; desde: number; hasta?: number };

function camaraGeo(claves: ClaveGlobo[], f: number) {
  const k = claves.map((c) => c.f), o = { easing: suave, extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  // el zoom se interpola en escala logarítmica para que se sienta constante
  const radio = Math.exp(interpolate(f, k, claves.map((c) => Math.log(c.radio)), o));
  return { lon: interpolate(f, k, claves.map((c) => c.lon), o), lat: interpolate(f, k, claves.map((c) => c.lat), o), radio };
}

/** Globo terráqueo / mapa ortográfico animado: zoom geográfico, rutas, marcadores y países resaltados. */
export const Globo: React.FC<{
  claves: ClaveGlobo[]; marcadores?: Marcador[]; rutas?: Ruta[]; resaltes?: Resalte[];
  tierra?: [string, string, number, number]; // color frío, color cálido, frame inicio/fin del viraje
  centroY?: number;
}> = ({ claves, marcadores = [], rutas = [], resaltes = [], tierra = ["#2B3140", "#4A3F2C", 0, 0], centroY = 0.46 }) => {
  const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const c = camaraGeo(claves, f);
  const proy = geoOrthographic().rotate([-c.lon, -c.lat]).scale(c.radio).translate([width / 2, height * centroY]).clipAngle(90).precision(0.3);
  const path = geoPath(proy);
  const grid = useMemo(() => geoGraticule10(), []);
  const colTierra = tierra[2] === tierra[3] ? tierra[0] : interpolateColors(f, [tierra[2], tierra[3]], [tierra[0], tierra[1]]);
  const brillo = Math.min(1, c.radio / 900);

  return (
    <AbsoluteFill>
      <svg width={width} height={height}>
        <defs>
          <radialGradient id="mar" cx="45%" cy="40%" r="65%"><stop offset="0%" stopColor="#1B2740" /><stop offset="100%" stopColor="#0A1020" /></radialGradient>
          <radialGradient id="halo" cx="50%" cy="50%" r="50%"><stop offset="85%" stopColor="rgba(198,164,106,0)" /><stop offset="100%" stopColor="rgba(198,164,106,0.25)" /></radialGradient>
        </defs>
        <path d={path({ type: "Sphere" } as GeoPermissibleObjects) || ""} fill="url(#mar)" />
        <path d={path(grid) || ""} fill="none" stroke="rgba(238,232,218,0.07)" strokeWidth={1} />
        {PAISES.map((p) => {
          const r = resaltes.find((x) => x.id === p.id && f >= x.desde && (x.hasta === undefined || f < x.hasta));
          const a = r ? interpolate(f, [r.desde, r.desde + 15], [0, 1], { extrapolateRight: "clamp" }) : 0;
          const fill = r ? interpolateColors(a, [0, 1], [colTierra, r.color]) : colTierra;
          return <path key={p.id + (p.properties?.name || "")} d={path(p) || ""} fill={fill} stroke="rgba(238,232,218,0.22)" strokeWidth={0.8} />;
        })}
        <path d={path({ type: "Sphere" } as GeoPermissibleObjects) || ""} fill="url(#halo)" opacity={1 - brillo * 0.6} />
        {rutas.map((ru, i) => {
          const p = interpolate(f, [ru.desde, ru.hasta], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: suave });
          if (p <= 0) return null;
          // densifica la ruta por círculos máximos y la recorta según el progreso (tracking)
          const densos: [number, number][] = [];
          for (let s = 0; s < ru.puntos.length - 1; s++) {
            const ip = geoInterpolate(ru.puntos[s], ru.puntos[s + 1]);
            for (let t = 0; t <= 1; t += 0.02) densos.push(ip(t) as [number, number]);
          }
          const n = Math.max(2, Math.floor(densos.length * p));
          const linea = { type: "LineString", coordinates: densos.slice(0, n) } as GeoPermissibleObjects;
          const punta = proy(densos[n - 1]);
          return (
            <g key={i}>
              <path d={path(linea) || ""} fill="none" stroke={ru.color || T.dorado} strokeWidth={6} strokeLinecap="round" strokeDasharray={ru.discontinua ? "2 16" : undefined} />
              {punta && p < 1 && <circle cx={punta[0]} cy={punta[1]} r={12} fill={ru.color || T.dorado} />}
            </g>
          );
        })}
        {marcadores.map((m, i) => {
          const xy = proy([m.lon, m.lat]);
          const visible = geoPath(proy)({ type: "Point", coordinates: [m.lon, m.lat] } as GeoPermissibleObjects);
          if (!xy || !visible) return null;
          const p = interpolate(f, [m.aparece, m.aparece + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.4)) });
          if (p <= 0) return null;
          const pulso = 1 + 0.25 * Math.sin((f - m.aparece) / 6);
          const der = m.lado !== "izq";
          return (
            <g key={i} opacity={Math.min(1, p * 1.5)} transform={`translate(${xy[0]} ${xy[1]})`}>
              <circle r={26 * pulso * p} fill="none" stroke={m.color || T.dorado} strokeWidth={3} opacity={0.6} />
              <circle r={11 * p} fill={m.color || T.dorado} />
              <text x={der ? 34 : -34} y={12} textAnchor={der ? "start" : "end"} fill={T.marfil} fontFamily={T.fuente} fontWeight={800} fontSize={40} letterSpacing={3}
                style={{ paintOrder: "stroke", stroke: "rgba(10,16,32,0.85)", strokeWidth: 10 }}>{m.texto}</text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
