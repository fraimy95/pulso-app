# Narrador documental en español (Qwen3-TTS + MLX-Audio)

Genera narraciones en español **en tu Mac con Apple Silicon**, gratis y sin internet una vez descargados los modelos. Exporta WAV, subtítulos SRT y un JSON con los tiempos de cada frase.

## Instalación (una sola vez)

Requisitos:
- Mac M1 o posterior. 16 GB de RAM recomendados; con 8 GB usa `--rapido`.
- Python 3.10 o superior.
- Unos 10 GB libres.

Desde la carpeta del proyecto:

```bash
bash setup.sh
```

El instalador crea `.venv`, instala las dependencias y descarga los modelos:

| Modelo | Tamaño |
|---|---|
| VoiceDesign 1.7B, 8 bits | 3,1 GB |
| Base 1.7B, 8 bits | 3,1 GB |
| Whisper turbo | 1,6 GB |

## Uso rápido

Activa el entorno:

```bash
source .venv/bin/activate
```

Abre la interfaz en el navegador (http://127.0.0.1:7860):

```bash
python app.py
```

O usa la línea de comandos:

```bash
python narrar.py --listar
```

```bash
python narrar.py --disenar --voz narradora_documental --semilla 7
```

```bash
python narrar.py guion.txt -o salida/episodio1.wav --voz narradora_documental --semilla 7 --expresividad sobria
```

```bash
python probar_pronunciacion.py --voz narradora_documental --semilla 7
```

- `--listar` muestra las voces disponibles.
- `--disenar` crea una muestra de la voz para escucharla.
- `narrar.py guion.txt` narra el guion completo.
- `probar_pronunciacion.py` genera `pruebas/informe.html`, donde puedes escuchar cada frase y ver qué entendió Whisper.

## Cómo consigue una voz consistente

Las 9 voces predefinidas de Qwen3-TTS son nativas en chino, inglés, japonés o coreano. **Ninguna es nativa en español** y pueden sonar con acento. Por eso el modo recomendado es otro:

1. **Diseñar la voz una vez.** El modelo *VoiceDesign* crea una muestra de unos 10 s a partir de una descripción: «narrador de 45 años, barítono cálido, español latinoamericano neutro, ritmo pausado». La muestra se guarda en `voces/`.
2. **Clonar esa muestra en cada segmento.** El modelo *Base* lee cada párrafo imitando la misma muestra, así todo el documental suena a la misma persona.
3. **Fijar la semilla.** La misma semilla da la misma voz. Si no te convence, cambia `--semilla` y vuelve a probar; cuando encuentres una que te guste, anótala.

El script además:
- divide el texto en párrafos y luego en grupos de frases de hasta 280 caracteres;
- comprueba la duración de cada segmento y lo **regenera** si salió anómalo (repeticiones o cortes);
- recorta los silencios, añade pausas (0,3 s entre frases y 0,8 s entre párrafos) y normaliza el volumen a **-16 LUFS**, el estándar para YouTube y redes.

## Voces

| Clave | Género | Estilo |
|---|---|---|
| `narrador_documental` | Masculina | Grave, pausado, con autoridad |
| `narrador_cercano` | Masculina | Claro, joven, divulgativo |
| `narradora_documental` | Femenina | Cálida, serena |
| `narradora_periodistica` | Femenina | Clara, dinámica |
| Predefinidas (`--modo predefinida`) | Masc.: Ryan, Aiden, Uncle_Fu, Dylan, Eric · Fem.: Serena, Vivian, Sohee, Ono_Anna | Acento extranjero probable |
| `--modo clonar --ref mi_voz.wav --ref-texto "…"` | La tuya | 5–15 s limpios, sin música |

Para crear voces nuevas, edita `VOCES_DISENADAS` en `narrador/motor.py`. Las descripciones van en inglés porque el modelo las sigue mejor; el idioma de la narración lo marcan el texto y `language="spanish"`.

**Expresividad:** `sobria`, `natural`, `expresiva` o un número entre 0 y 1. Controla la temperatura de muestreo y el estilo con que se diseña la voz.
- Para documentales: `sobria` o `natural`.
- `expresiva` da más vida, pero también más riesgo de errores.

## Pronunciación

- **Cifras.** Se convierten a palabras con concordancia de género: «4.217 muertes» se lee «cuatro mil doscientas diecisiete muertes». También se leen bien porcentajes, años, decimales («1,5») y «US$ 880 millones».
- **Siglas y nombres extranjeros.** Se escriben como deben sonar en `lexico.json` (BINUH → «Binú», Croix-des-Bouquets → «Cruá de Buqué»). Puedes editarlo desde la interfaz.
- **Marcas del guion.** Se eliminan automáticamente referencias como `[12]` y marcas como `[VERIFICAR]`.
- **Ver la lectura.** El botón «Ver lectura» de la interfaz muestra el texto exacto que recibe el modelo.

## Rendimiento orientativo

En un M2 o M3 con el modelo 1.7B de 8 bits, la generación va aproximadamente al ritmo de la reproducción: un guion de 7 minutos tarda unos 5–10 minutos. Con `--rapido` (0.6B) es más rápido, pero algo menos natural. Son cifras estimadas: mide en tu Mac.

## Limitaciones conocidas

- `speed` no está implementado en Qwen3-TTS: el ritmo se controla con la descripción de la voz y la expresividad.
- La clonación con el modelo Base **no admite instrucciones de estilo**. Para cambiar la emoción, diseña otra referencia con otra expresividad.
- Whisper transcribe mal los nombres propios. Por eso esas frases se marcan como «revisar a oído».

## Licencias

Todo el sistema es de uso libre y comercial. El detalle y las precauciones (clonación de voces, aviso de voz sintética) están en [LICENCIAS.md](LICENCIAS.md).
