# Licencias y uso comercial

Revisado el 15 de noviembre de 2026 contra las fichas oficiales en Hugging Face y PyPI.
Esto es una revisión técnica, **no asesoría legal**: si vas a vender el contenido a un cliente o a una televisora, confírmalo con un abogado.

## Modelos

| Componente | Licencia | ¿Uso comercial? | Fuente |
|---|---|---|---|
| Qwen3-TTS 1.7B VoiceDesign / Base / CustomVoice, 0.6B Base / CustomVoice | Apache-2.0 | ✅ Sí | `huggingface.co/Qwen/Qwen3-TTS-12Hz-*` |
| Qwen3-TTS-Tokenizer-12Hz | Apache-2.0 | ✅ Sí | `huggingface.co/Qwen/Qwen3-TTS-Tokenizer-12Hz` |
| Conversiones MLX (`mlx-community/Qwen3-TTS-*`) | Apache-2.0 (heredada) | ✅ Sí | `huggingface.co/mlx-community` |
| Whisper large-v3-turbo (solo para las pruebas) | MIT | ✅ Sí | `huggingface.co/openai/whisper-large-v3-turbo` |

Apache-2.0 permite uso comercial, modificación y redistribución. Si **redistribuyes los modelos** (no el audio), debes incluir la licencia y los avisos. **El audio que generas no queda sujeto a la licencia del modelo.**

## Software

| Paquete | Licencia | Notas |
|---|---|---|
| mlx, mlx-audio | MIT | — |
| gradio | Apache-2.0 | Solo interfaz local |
| numpy, soundfile | BSD-3 | soundfile usa libsndfile (LGPL), enlazada dinámicamente |
| pyloudnorm | MIT | — |
| jiwer | Apache-2.0 | — |
| num2words | LGPL-2.1 | Se usa como librería sin modificar: compatible con uso comercial |
| ffmpeg (opcional, Homebrew) | LGPL/GPL según la compilación | Usarlo como herramienta no afecta a tu audio |

## Lo que sí te puede limitar

1. **Clonar voces.** Clona solo tu propia voz o la de alguien que te dé **consentimiento por escrito**. No clones voces de ElevenLabs ni de otros servicios (sus términos lo restringen), ni de locutores o personajes públicos.
2. **Avisar que es una voz sintética.**
   - **YouTube** pide marcar el contenido "alterado o sintético" cuando es realista y puede confundirse con una persona o un hecho real. Una voz de narrador ficticia en un video explicativo normalmente no lo requiere, pero revisa la política vigente.
   - **Unión Europea:** el Reglamento de IA (art. 50) exige transparencia sobre el audio generado por IA en ciertos casos, con obligaciones aplicables desde agosto de 2026.
   - **Recomendación:** pon en la descripción "Narración generada con IA (voz sintética)". No cuesta nada y evita problemas.
3. **La voz diseñada no es de nadie**, pero un modelo puede parecerse por casualidad a una voz conocida. Si una voz te recuerda a alguien famoso, genera otra con una semilla distinta.
