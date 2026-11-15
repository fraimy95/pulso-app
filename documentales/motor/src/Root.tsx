import React from "react";
import { Composition } from "remotion";
import { Caption } from "@remotion/captions";
import { DURACION_PRUEBA, Prueba15s } from "./documentales/sosua/Prueba15s";
import subKokoro from "../public/sosua/prueba_15s_subtitulos.json";
import subQwen from "../public/sosua/prueba_15s_qwen_subtitulos.json";

// Todas las composiciones son verticales 1080×1920 a 30 fps.
// Vista previa a 540×960:  npx remotion render src/index.ts <Id> salida.mp4 --scale=0.5
export const Root: React.FC = () => (
  <>
    <Composition id="SosuaPrueba15s" component={Prueba15s} durationInFrames={DURACION_PRUEBA} fps={30} width={1080} height={1920}
      defaultProps={{ voz: "sosua/prueba_15s_voz.wav", subtitulos: subKokoro as Caption[], inicioEscena2: 251, fin: 495 }} />
    <Composition id="SosuaPrueba15sQwen" component={Prueba15s} durationInFrames={521} fps={30} width={1080} height={1920}
      defaultProps={{ voz: "sosua/prueba_15s_qwen_voz.wav", subtitulos: subQwen as Caption[], inicioEscena2: 271, fin: 521 }} />
  </>
);
