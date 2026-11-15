import { Config } from "@remotion/cli/config";
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(92);
Config.setConcurrency(2); // MacBook Intel 16 GB: 2 pestañas a la vez para no saturar la RAM
// Solo si se define (servidores sin acceso a remotion.media). En el Mac no hace falta.
if (process.env.REMOTION_BROWSER) Config.setBrowserExecutable(process.env.REMOTION_BROWSER);
