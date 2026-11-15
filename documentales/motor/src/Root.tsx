import React from "react";
import { Composition } from "remotion";
import { DURACION_PRUEBA, Prueba15s } from "./documentales/sosua/Prueba15s";

// Todas las composiciones son verticales 1080×1920 a 30 fps.
// Vista previa a 540×960:  npx remotion render src/index.ts <Id> salida.mp4 --scale=0.5
export const Root: React.FC = () => (
  <>
    <Composition id="SosuaPrueba15s" component={Prueba15s} durationInFrames={DURACION_PRUEBA} fps={30} width={1080} height={1920} />
  </>
);
