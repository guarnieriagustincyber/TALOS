#!/usr/bin/env python3
"""Download pre-quantized SOTA Multilingual Neural Reranker (BGE-Reranker-Base INT8 ONNX)."""

import os
import sys
import urllib.request
from pathlib import Path

TARGET_DIR = Path("models/reranker")
FILES = {
    "model.onnx": "https://huggingface.co/onnx-community/bge-reranker-base-ONNX/resolve/main/onnx/model_int8.onnx",
    "tokenizer.json": "https://huggingface.co/onnx-community/bge-reranker-base-ONNX/resolve/main/tokenizer.json",
}

def download_file(url: str, dest_path: Path) -> None:
    if dest_path.exists() and dest_path.stat().st_size > 1000:
        print(f"✅ {dest_path.name} ya existe ({dest_path.stat().st_size / (1024*1024):.1f} MB). Saltando.")
        return

    print(f"📥 Descargando {dest_path.name} desde Hugging Face...")
    temp_path = dest_path.with_suffix(".tmp")
    req = urllib.request.Request(url, headers={"User-Agent": "TALOS-Downloader/1.0"})
    
    with urllib.request.urlopen(req) as resp, open(temp_path, "wb") as out_f:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB
        last_pct = -1
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = int((downloaded / total) * 100)
                if pct != last_pct and pct % 10 == 0:
                    print(f"   [{dest_path.name}] {pct}% ({downloaded / (1024*1024):.1f}/{total / (1024*1024):.1f} MB)")
                    last_pct = pct

    temp_path.rename(dest_path)
    print(f"✅ {dest_path.name} descargado correctamente ({dest_path.stat().st_size / (1024*1024):.1f} MB).")

def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Iniciando descarga de Neural Cross-Encoder Reranker en {TARGET_DIR.resolve()}...")
    for filename, url in FILES.items():
        download_file(url, TARGET_DIR / filename)
    print("🎉 Reranker Neural local instalado y listo para usar en TALOS.")

if __name__ == "__main__":
    main()
