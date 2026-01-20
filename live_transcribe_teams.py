"""
Live Transcription for Teams/Audio Loopback
Transcribe in real-time what you hear on your speakers using Vosk + PyAudioWPatch.

Based on:
- https://github.com/s0d3s/PyAudioWPatch (WASAPI loopback)
- https://alphacephei.com/vosk/ (offline speech recognition)
"""
import json
import time
import pyaudiowpatch as pyaudio
from vosk import Model, KaldiRecognizer

# Vosk works best at 16kHz
VOSK_SAMPLE_RATE = 16000
CHUNK_SIZE = 4000  # ~250ms at 16kHz


def resample_audio(data: bytes, orig_rate: int, target_rate: int, channels: int) -> bytes:
    """Resample audio from orig_rate to target_rate using simple linear interpolation"""
    import numpy as np
    
    # Convert bytes to numpy array (int16)
    audio = np.frombuffer(data, dtype=np.int16)
    
    # If stereo, convert to mono by averaging channels
    if channels == 2:
        audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
    
    # Resample if needed
    if orig_rate != target_rate:
        # Calculate new length
        new_length = int(len(audio) * target_rate / orig_rate)
        # Use linear interpolation for resampling
        indices = np.linspace(0, len(audio) - 1, new_length)
        audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.int16)
    
    return audio.tobytes()


def main():
    print("=" * 60)
    print("  LIVE TRANSCRIPTION - Teams/System Audio")
    print("=" * 60)
    
    # Initialize PyAudio with WASAPI support
    print("\n[1/3] Inicializando audio...")
    
    with pyaudio.PyAudio() as p:
        # Get WASAPI host API
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("ERROR: WASAPI no disponible en este sistema.")
            return
        
        # Get default speakers
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        # Find loopback device for default speakers
        if not default_speakers.get("isLoopbackDevice"):
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                print("ERROR: No se encontró dispositivo loopback.")
                print("Ejecuta: python -m pyaudiowpatch")
                return
        
        device_rate = int(default_speakers["defaultSampleRate"])
        device_channels = default_speakers["maxInputChannels"]
        
        print(f"    Dispositivo: {default_speakers['name']}")
        print(f"    Sample Rate: {device_rate} Hz")
        print(f"    Canales: {device_channels}")
        
        # Load Vosk model
        print("\n[2/3] Cargando modelo Vosk...")
        model = Model("model")
        recognizer = KaldiRecognizer(model, VOSK_SAMPLE_RATE)
        recognizer.SetWords(True)
        print("    Modelo cargado correctamente")
        
        # Calculate chunk size for device rate
        device_chunk = int(CHUNK_SIZE * device_rate / VOSK_SAMPLE_RATE)
        
        print("\n[3/3] Iniciando transcripción...")
        print("-" * 60)
        print("Escuchando... (Ctrl+C para salir)")
        print("-" * 60 + "\n")
        
        partial_last = ""
        
        # Open audio stream
        with p.open(
            format=pyaudio.paInt16,
            channels=device_channels,
            rate=device_rate,
            frames_per_buffer=device_chunk,
            input=True,
            input_device_index=default_speakers["index"]
        ) as stream:
            
            while True:
                try:
                    # Read audio data
                    data = stream.read(device_chunk, exception_on_overflow=False)
                    
                    # Resample to 16kHz mono for Vosk
                    audio_16k = resample_audio(data, device_rate, VOSK_SAMPLE_RATE, device_channels)
                    
                    # Process with Vosk
                    if recognizer.AcceptWaveform(audio_16k):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            # Clear partial and print final result
                            print(f"\r{' ' * 80}\r", end="")
                            print(f"► {text}")
                        partial_last = ""
                    else:
                        # Show partial result (live captions style)
                        partial = json.loads(recognizer.PartialResult()).get("partial", "").strip()
                        if partial and partial != partial_last:
                            print(f"\r  {partial}{' ' * 20}", end="", flush=True)
                            partial_last = partial
                    
                    time.sleep(0.01)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\nError: {e}")
                    time.sleep(0.5)
    
    print("\n\nTranscripción finalizada.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTranscripción finalizada.")
    except Exception as e:
        print(f"\nError fatal: {e}")
        import traceback
        traceback.print_exc()
