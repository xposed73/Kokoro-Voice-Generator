Kokoro Voice Generator (Streamlit)

Overview

Generate high‑quality speech from text using the Kokoro ONNX model in a friendly Streamlit UI. On first run, the launcher downloads required model files into the model/ folder, then starts the app.

Screenshot

![App Screenshot](assets/screen_1_.png)

Key features

- Kokoro‑82M voice list grouped by language (English US/UK, Japanese, Mandarin, Spanish, French, Hindi, Italian, Portuguese BR)
- Single, Batch, and Preview modes
- Text templates and quick stats (chars/words/estimated duration)
- Download WAV, or ZIP for batch
- Presets for language/voice/speed
- Generation history with re‑play and downloads

Requirements

- Python 3.11+ (project targets Python >=3.13 in pyproject, but works with 3.11+)
- Windows/macOS/Linux

Install

Using uv:

```bash
uv sync
```

Note: This project uses uv for environment and dependency management.

Model files

This project expects model files in model/:

- model/kokoro-v1.0.onnx
- model/voices-v1.0.bin

You do not need to download these manually. The launcher (main.py) checks and downloads them automatically on first run. If you prefer manual setup, place both files in the model/ directory.

Run

Recommended: use the launcher so model files are ensured and the app starts automatically.

```bash
uv run main.py
```

Directly via Streamlit with uv (assumes model files already present):

```bash
uv run streamlit run app.py
```

Project layout

```text
kokovoice/
  app.py                # Streamlit UI
  main.py               # Launcher: ensures model files, then runs Streamlit
  model/
    kokoro-v1.0.onnx
    voices-v1.0.bin
  pyproject.toml        # Dependencies (kokoro-onnx, soundfile, streamlit)
  uv.lock               # uv lockfile
  README.md
```

Usage notes

- First launch may take time while downloading model files and loading the model.
- After selecting language and voice, adjust speed and enter your text, then click Generate.
- Batch mode: enter one line per item; you can download all outputs as a ZIP.

Troubleshooting

- Port already in use: Streamlit runs on 8501 by default. Close other Streamlit sessions, or run with:
  ```bash
  streamlit run app.py --server.port 8502
  ```
- Name collision: Do not name your app file streamlit.py; it will shadow the Streamlit package. Ensure the UI file is app.py.
- Slow or failed downloads: If the launcher cannot fetch model files (network restrictions), download them manually and place them in model/.

Credits

- Kokoro ONNX and voices: thewh1teagle/kokoro-onnx (see their repository and VOICES.md for details)


