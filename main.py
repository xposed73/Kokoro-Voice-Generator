"""
Launcher to ensure model files exist, download them if missing, then run the Streamlit app.
Run: python main.py
"""

import os
import sys
import urllib.request
import shutil
import time

import streamlit.web.cli as stcli


MODEL_DIR = "model"
FILES = [
    (
        "kokoro-v1.0.onnx",
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    ),
    (
        "voices-v1.0.bin",
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    ),
]


def ensure_model_files() -> None:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    model_dir = os.path.join(base_dir, MODEL_DIR)
    os.makedirs(model_dir, exist_ok=True)

    for filename, url in FILES:
        dest_path = os.path.join(model_dir, filename)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            print(f"✔ Found {os.path.join(MODEL_DIR, filename)}")
            continue
        download_with_progress(url, dest_path)


def download_with_progress(url: str, dest_path: str) -> None:
    tmp_path = dest_path + ".part"
    print(f"⬇️  Downloading {os.path.basename(dest_path)}...")
    with urllib.request.urlopen(url) as response, open(tmp_path, "wb") as out_file:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 1024 * 256  # 256KB
        start = time.time()
        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            out_file.write(buffer)
            downloaded += len(buffer)
            if total:
                percent = downloaded * 100 // total
                speed = downloaded / max(1, (time.time() - start)) / (1024 * 1024)
                print(f"  {percent:3d}% ({downloaded//(1024*1024)} MB / {total//(1024*1024)} MB) @ {speed:.1f} MB/s",
                      end="\r",
                      flush=True)
    print()
    shutil.move(tmp_path, dest_path)
    print(f"✔ Saved to {dest_path}")


def run_streamlit() -> None:
    app_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless",
        "true",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    ensure_model_files()
    run_streamlit()