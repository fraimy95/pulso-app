#!/usr/bin/env python3
"""Interfaz local sencilla (se abre en el navegador, sin internet tras descargar los modelos).

  python app.py      ->  http://127.0.0.1:7860
"""
import json
import time
from pathlib import Path

import gradio as gr

from narrador.motor import (EXPRESIVIDAD, VOCES_DISENADAS, VOCES_PREDEFINIDAS, Narrador, Opciones)
from narrador.texto import LEXICO_POR_DEFECTO, cargar_lexico, dividir, normalizar

SALIDA = Path(__file__).resolve().parent / "salida"
SALIDA.mkdir(exist_ok=True)
_cache: dict[tuple, Narrador] = {}


def _voces(modo, genero):
    if modo == "Voz predefinida":
        return VOCES_PREDEFINIDAS["masculina" if genero == "Masculina" else "femenina"]
    g = "masculina" if genero == "Masculina" else "femenina"
    return [v["etiqueta"] for v in VOCES_DISENADAS.values() if v["genero"] == g]


def _clave_voz(modo, etiqueta):
    if modo == "Voz predefinida":
        return etiqueta
    return next(k for k, v in VOCES_DISENADAS.items() if v["etiqueta"] == etiqueta)


def _narrador(modo, genero, voz, expresividad, semilla, rapido, ref, ref_txt):
    modo_int = {"Voz diseñada (recomendado)": "disenada", "Voz predefinida": "predefinida", "Clonar mi voz": "clonar"}[modo]
    op = Opciones(modo=modo_int, voz=_clave_voz(modo, voz) if modo_int != "clonar" else "propia",
                  expresividad=float(expresividad), semilla=int(semilla), tam_base="0.6B" if rapido else "1.7B",
                  ref_audio=ref, ref_texto=ref_txt or None)
    clave = (op.modo, op.tam_base)
    n = _cache.get(clave) or Narrador(op)
    n.op = op
    _cache[clave] = n
    return n


def actualizar_voces(modo, genero):
    vs = _voces(modo, genero)
    visible_ref = modo == "Clonar mi voz"
    return (gr.update(choices=vs, value=vs[0], visible=not visible_ref),
            gr.update(visible=visible_ref), gr.update(visible=visible_ref))


def escuchar_voz(modo, genero, voz, expresividad, semilla, rapido, ref, ref_txt):
    n = _narrador(modo, genero, voz, expresividad, semilla, rapido, ref, ref_txt)
    if n.op.modo == "disenada":
        return str(n.disenar_referencia(forzar=True)), "Muestra de la voz. ¿No te convence? Cambia la semilla y vuelve a probar."
    ruta = SALIDA / f"muestra_{int(time.time())}.wav"
    n.narrar("Bienvenidos. En este documental recorreremos la historia de un país del Caribe.", ruta)
    return str(ruta), "Muestra generada."


def vista_previa(texto, *args):
    segs = dividir(texto)
    if not segs:
        return None, "Escribe o pega un texto."
    n = _narrador(*args)
    ruta = SALIDA / f"previa_{int(time.time())}.wav"
    n.narrar(segs[0].texto, ruta)
    return str(ruta), f"Vista previa del primer segmento ({len(segs)} en total)."


def narrar_todo(texto, *args, progress=gr.Progress()):
    if not texto.strip():
        return None, None, "Escribe o pega un texto."
    n = _narrador(*args)
    ruta = SALIDA / f"narracion_{time.strftime('%Y%m%d_%H%M%S')}.wav"
    meta = n.narrar(texto, ruta, progreso=lambda i, tot, t: progress((i, tot), desc=f"Segmento {i + 1}/{tot}"))
    dudosos = [m["n"] for m in meta["segmentos"] if not m["ok"]]
    nota = f"Listo: {meta['duracion_s']} s de audio en {meta['tiempo_generacion_s']} s."
    if dudosos:
        nota += f" Revisa los segmentos {dudosos}: su duración salió anómala (están en la carpeta _segmentos)."
    return str(ruta), str(ruta.with_suffix(".srt")), nota


def ver_lectura(texto):
    lex = cargar_lexico()
    return "\n\n".join(f"[{i + 1}] {normalizar(s.texto, lex)}" for i, s in enumerate(dividir(texto)))


def guardar_lexico(txt):
    try:
        datos = json.loads(txt)
    except json.JSONDecodeError as e:
        return f"JSON no válido: {e}"
    LEXICO_POR_DEFECTO.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Guardado ({len(datos)} entradas)."


with gr.Blocks(title="Narrador documental") as demo:
    gr.Markdown("## 🎙️ Narrador documental en español\nQwen3-TTS + MLX-Audio, 100 % local en tu Mac.")
    with gr.Row():
        with gr.Column(scale=1):
            modo = gr.Radio(["Voz diseñada (recomendado)", "Voz predefinida", "Clonar mi voz"],
                            value="Voz diseñada (recomendado)", label="Tipo de voz")
            genero = gr.Radio(["Masculina", "Femenina"], value="Masculina", label="Género")
            voz = gr.Dropdown(_voces("Voz diseñada (recomendado)", "Masculina"),
                              value=_voces("Voz diseñada (recomendado)", "Masculina")[0], label="Voz")
            ref = gr.Audio(type="filepath", label="Tu grabación (5–15 s, sin música)", visible=False)
            ref_txt = gr.Textbox(label="Transcripción exacta de tu grabación", visible=False)
            expresividad = gr.Slider(0, 1, value=0.5, step=0.05, label="Expresividad (sobria → expresiva)")
            semilla = gr.Number(value=1234, precision=0, label="Semilla (misma semilla = misma voz)")
            rapido = gr.Checkbox(False, label="Modo rápido (modelo 0.6B)")
            b_voz = gr.Button("🔊 Escuchar la voz")
            audio_voz = gr.Audio(label="Muestra de voz", interactive=False)
        with gr.Column(scale=2):
            texto = gr.Textbox(lines=16, label="Guion (separa los párrafos con una línea en blanco)")
            with gr.Row():
                b_prev = gr.Button("▶️ Vista previa (1.er segmento)")
                b_todo = gr.Button("🎬 Narrar todo y exportar WAV", variant="primary")
            estado = gr.Markdown()
            audio_out = gr.Audio(label="Resultado", interactive=False)
            srt_out = gr.File(label="Subtítulos (.srt)")
            with gr.Accordion("Cómo se leerá el texto (cifras y siglas expandidas)", open=False):
                b_lect = gr.Button("Ver lectura")
                lectura = gr.Textbox(lines=10, label="Texto que recibe el modelo")
            with gr.Accordion("Léxico de pronunciación", open=False):
                lex = gr.Code(value=LEXICO_POR_DEFECTO.read_text(encoding="utf-8"), language="json", label="lexico.json")
                b_lex = gr.Button("Guardar léxico"); lex_estado = gr.Markdown()

    entradas = [modo, genero, voz, expresividad, semilla, rapido, ref, ref_txt]
    modo.change(actualizar_voces, [modo, genero], [voz, ref, ref_txt])
    genero.change(actualizar_voces, [modo, genero], [voz, ref, ref_txt])
    b_voz.click(escuchar_voz, entradas, [audio_voz, estado])
    b_prev.click(vista_previa, [texto] + entradas, [audio_out, estado])
    b_todo.click(narrar_todo, [texto] + entradas, [audio_out, srt_out, estado])
    b_lect.click(ver_lectura, texto, lectura)
    b_lex.click(guardar_lexico, lex, lex_estado)

if __name__ == "__main__":
    demo.queue().launch(server_name="127.0.0.1", inbrowser=True, theme=gr.themes.Soft())
