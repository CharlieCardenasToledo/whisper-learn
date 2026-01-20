"""
Download and extract Vosk model for English transcription.
Run this script once before using live_transcribe_teams.py
"""
import os
import urllib.request
import zipfile
import shutil

# Vosk small English model (approx 40MB)
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_ZIP = "vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "model"


def download_model():
    if os.path.exists(MODEL_DIR):
        print(f"El directorio '{MODEL_DIR}' ya existe. Modelo ya descargado.")
        return

    print(f"Descargando modelo de Vosk desde:\n{MODEL_URL}")
    print("Esto puede tardar unos minutos...")

    # Download with progress
    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size)
        print(f"\rProgreso: {percent}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="", flush=True)

    urllib.request.urlretrieve(MODEL_URL, MODEL_ZIP, reporthook)
    print("\n\nDescarga completada. Extrayendo...")

    # Extract
    with zipfile.ZipFile(MODEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(".")

    # Rename extracted folder to "model"
    extracted_name = MODEL_ZIP.replace(".zip", "")
    if os.path.exists(extracted_name):
        shutil.move(extracted_name, MODEL_DIR)
        print(f"Modelo extraído a '{MODEL_DIR}/'")

    # Clean up zip file
    os.remove(MODEL_ZIP)
    print("Archivo ZIP eliminado.")
    print("\n¡Listo! Ahora puedes ejecutar: python live_transcribe_teams.py")


if __name__ == "__main__":
    download_model()
