import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Caption } from "@remotion/captions";
import { Camara } from "../../componentes/Camara";
import { Globo } from "../../componentes/Globo";
import { Subtitulos } from "../../componentes/Subtitulos";
import { Acabado, Nota, TituloCine } from "../../componentes/Acabado";
import { T } from "../../tema";

// Coordenadas verificadas (WGS84)
const BERLIN: [number, number] = [13.405, 52.52];
const VIENA: [number, number] = [16.3738, 48.2082];
const SOSUA: [number, number] = [-70.517, 19.752]; // Sosúa, Puerto Plata

export const DURACION_PRUEBA = 495; // 16,5 s a 30 fps (narración Kokoro)

export type PropsPrueba = { voz: string; subtitulos: Caption[]; inicioEscena2: number; fin: number };

/** Reescala los fotogramas diseñados para la narración de referencia (escena 2 en 251, fin en 495)
 *  a los tiempos reales de otra narración: así la misma escena sirve para cualquier voz. */
const reescala = (p: PropsPrueba) => (f: number) => f <= 251 ? (f * p.inicioEscena2) / 251 : p.inicioEscena2 + ((f - 251) * (p.fin - p.inicioEscena2)) / (495 - 251);

export const Prueba15s: React.FC<PropsPrueba> = (props) => { const m = reescala(props); return (
  <AbsoluteFill style={{ background: T.azul }}>
    <Audio src={staticFile(props.voz)} />
    <Camara claves={[{ f: m(0), escala: 1 }, { f: m(240), escala: 1.06 }, { f: m(275), escala: 1 }, { f: m(495), escala: 1.04 }]}>
      <Globo
        claves={[
          { f: m(0), lon: 12, lat: 50, radio: 1700 },     // Europa 1938
          { f: m(240), lon: 12.5, lat: 51, radio: 2300 }, // slow push-in hacia Alemania
          { f: m(300), lon: -22, lat: 38, radio: 520 },   // pull-out: el globo, el Atlántico
          { f: m(390), lon: -64, lat: 22, radio: 950 },   // tracking hacia el Caribe
          { f: m(455), lon: -70.4, lat: 19.2, radio: 6200 }, // zoom geográfico a La Española
        ]}
        tierra={["#2B3140", "#3A3427", m(330), m(420)]}
        resaltes={[
          { id: "276", color: T.rojo, desde: m(30) },  // Alemania
          { id: "040", color: "#7A3036", desde: m(95) }, // Austria (anexionada en marzo de 1938)
          { id: "214", color: "#D9B676", desde: m(360) }, // República Dominicana
        ]}
        marcadores={[
          { lon: BERLIN[0], lat: BERLIN[1], texto: "BERLÍN", aparece: m(40) },
          { lon: VIENA[0], lat: VIENA[1], texto: "VIENA", aparece: m(100) },
          { lon: SOSUA[0], lat: SOSUA[1], texto: "SOSÚA", aparece: m(425) },
        ]}
        rutas={[
          // desplazamientos ilustrativos dentro de Europa (esquemáticos)
          { puntos: [BERLIN, [4.9, 52.37]], desde: m(95), hasta: m(150), color: T.marfil, discontinua: true },
          { puntos: [BERLIN, [2.35, 48.86]], desde: m(110), hasta: m(170), color: T.marfil, discontinua: true },
          { puntos: [VIENA, [8.54, 47.37]], desde: m(125), hasta: m(180), color: T.marfil, discontinua: true },
          // travesía esquemática Europa → Atlántico → Sosúa (no es un itinerario documentado)
          { puntos: [BERLIN, [-28, 40], SOSUA], desde: m(268), hasta: m(425), color: T.dorado },
        ]}
      />
    </Camara>
    <TituloCine texto="EUROPA · 1938" desde={m(6)} hasta={m(235)} y={0.13} tam={0.05} />
    <TituloCine texto="SOSÚA" sub="Puerto Plata · Rep. Dominicana" desde={m(432)} hasta={m(495)} y={0.13} tam={0.075} color={T.dorado} serif />
    <Nota texto="Ruta esquemática" desde={m(270)} hasta={m(425)} />
    <Acabado grano={0.07} vineta={0.6} />
    <Subtitulos captions={props.subtitulos} claves={/^(Europa|judíos|nazi|Atlántico|Caribe|República|Dominicana)$/i} />
  </AbsoluteFill>
); };
