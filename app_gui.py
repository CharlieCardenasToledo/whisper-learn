"""
Live Transcription + Translation Desktop App
Modern UI with CustomTkinter + Faster-Whisper + Argos Translate

UX Principles Applied:
- Don Norman "Don't Make Me Think": Single obvious action, clear states
- Hick's Law: Minimal visible options, smart defaults
- Fitts' Law: Large primary button, easy targets
"""
import os
import sys
import ctypes

# Add NVIDIA CUDA DLLs to PATH before importing ctranslate2/faster_whisper
def setup_cuda_paths():
    """Add CUDA library paths for Windows and load DLLs explicitly"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(script_dir)
        os.environ["PATH"] = script_dir + os.pathsep + os.environ.get("PATH", "")
        
        cuda_dlls = [
            "cudart64_12.dll", "cublas64_12.dll", "cublasLt64_12.dll",
            "cudnn64_9.dll", "cudnn_ops64_9.dll", "cudnn_cnn64_9.dll", "cudnn_graph64_9.dll",
        ]
        
        for dll_name in cuda_dlls:
            dll_path = os.path.join(script_dir, dll_name)
            if os.path.exists(dll_path):
                try:
                    ctypes.CDLL(dll_path)
                except: pass
        
        import site
        site_packages = site.getsitepackages()[0]
        for subdir in ["cublas", "cudnn", "cuda_runtime"]:
            cuda_path = os.path.join(site_packages, "nvidia", subdir, "bin")
            if os.path.exists(cuda_path):
                if hasattr(os, 'add_dll_directory'):
                    os.add_dll_directory(cuda_path)
                os.environ["PATH"] = cuda_path + os.pathsep + os.environ.get("PATH", "")
    except: pass

setup_cuda_paths()

import json
import threading
import queue
import time
from datetime import datetime
import customtkinter as ctk
import pyaudiowpatch as pyaudio
import numpy as np
from faster_whisper import WhisperModel

try:
    import argostranslate.package
    import argostranslate.translate
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

SAMPLE_RATE = 16000
CHUNK_DURATION = 3.0
BUFFER_DURATION = 0.5


class TranscriptionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window config
        self.title("Transcriptor en Vivo")
        self.geometry("800x650")
        self.minsize(600, 500)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # State
        self.is_running = False
        self.audio_thread = None
        self.text_queue = queue.Queue()
        self.whisper_model = None
        self.translate_func = None
        
        # Settings (Hick's Law: smart defaults, hide complexity)
        self.selected_model = "medium"  # Best balance
        self.use_microphone = False  # Default: speaker loopback
        self.translate_enabled = False
        self.settings_visible = False
        
        self._create_ui()
        self._check_queue()
        
        if TRANSLATION_AVAILABLE:
            threading.Thread(target=self._init_translation, daemon=True).start()
    
    def _create_ui(self):
        """Create simplified UI following UX principles"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ===== MAIN ACTION AREA (Fitts: Large target, center) =====
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 15))
        action_frame.grid_columnconfigure(0, weight=1)
        
        # Giant start button (Fitts' Law: large, obvious target)
        self.main_btn = ctk.CTkButton(
            action_frame,
            text="🎙️  Iniciar Transcripción",
            command=self._toggle_transcription,
            font=ctk.CTkFont(size=22, weight="bold"),
            height=70,
            corner_radius=35,
            fg_color="#00a67d",
            hover_color="#008f6b"
        )
        self.main_btn.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Status bar (Norman: clear feedback)
        self.status_bar = ctk.CTkFrame(action_frame, fg_color="#1e1e2e", corner_radius=10, height=40)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(1, weight=1)
        
        self.status_dot = ctk.CTkLabel(self.status_bar, text="●", font=ctk.CTkFont(size=14), text_color="#666")
        self.status_dot.grid(row=0, column=0, padx=(15, 8), pady=10)
        
        self.status_text = ctk.CTkLabel(
            self.status_bar, 
            text="Listo para transcribir",
            font=ctk.CTkFont(size=13),
            text_color="#999"
        )
        self.status_text.grid(row=0, column=1, sticky="w")
        
        # Settings toggle (Norman: progressive disclosure)
        self.settings_btn = ctk.CTkButton(
            self.status_bar,
            text="⚙️",
            width=35,
            height=30,
            fg_color="transparent",
            hover_color="#333",
            command=self._toggle_settings
        )
        self.settings_btn.grid(row=0, column=2, padx=10)
        
        # ===== COLLAPSIBLE SETTINGS (Hick: reduce visible options) =====
        self.settings_frame = ctk.CTkFrame(action_frame, fg_color="#1a1a2a", corner_radius=10)
        # Hidden by default
        
        # Settings content
        settings_inner = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        settings_inner.pack(fill="x", padx=15, pady=15)
        
        # Audio source toggle
        source_frame = ctk.CTkFrame(settings_inner, fg_color="transparent")
        source_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(source_frame, text="Fuente de audio:", font=ctk.CTkFont(size=13)).pack(side="left")
        
        self.source_switch = ctk.CTkSegmentedButton(
            source_frame,
            values=["🔊 Altavoz", "🎤 Mic"],
            command=self._on_source_change
        )
        self.source_switch.set("🔊 Altavoz")
        self.source_switch.pack(side="right")
        
        # Model selector (simplified: only 3 options)
        model_frame = ctk.CTkFrame(settings_inner, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(model_frame, text="Precisión:", font=ctk.CTkFont(size=13)).pack(side="left")
        
        self.model_switch = ctk.CTkSegmentedButton(
            model_frame,
            values=["Rápido", "Balanceado", "Preciso"],
            command=self._on_model_change
        )
        self.model_switch.set("Balanceado")
        self.model_switch.pack(side="right")
        
        # Translation toggle
        if TRANSLATION_AVAILABLE:
            trans_frame = ctk.CTkFrame(settings_inner, fg_color="transparent")
            trans_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(trans_frame, text="Traducir EN → ES:", font=ctk.CTkFont(size=13)).pack(side="left")
            
            self.trans_switch = ctk.CTkSwitch(
                trans_frame,
                text="",
                command=self._on_translate_toggle,
                width=50
            )
            self.trans_switch.pack(side="right")
        
        # ===== TRANSCRIPTION DISPLAY =====
        content_frame = ctk.CTkFrame(self, corner_radius=15)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_rowconfigure(3, weight=1)
        
        # Original text
        ctk.CTkLabel(
            content_frame, 
            text="Transcripción",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#888"
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        self.original_text = ctk.CTkTextbox(
            content_frame,
            font=ctk.CTkFont(size=15),
            wrap="word",
            fg_color="#1a1a2e",
            corner_radius=10
        )
        self.original_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        # Translation (only if available)
        self.trans_label = ctk.CTkLabel(
            content_frame,
            text="Traducción",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#888"
        )
        self.trans_label.grid(row=2, column=0, sticky="w", padx=15, pady=(10, 5))
        
        self.translated_text = ctk.CTkTextbox(
            content_frame,
            font=ctk.CTkFont(size=15),
            wrap="word",
            fg_color="#1a1a2e",
            corner_radius=10
        )
        self.translated_text.grid(row=3, column=0, sticky="nsew", padx=15, pady=(5, 15))
        
        # Initially hide translation if not enabled
        self._update_translation_visibility()
        
        # ===== LIVE CAPTION BAR =====
        self.live_bar = ctk.CTkFrame(self, fg_color="#252535", corner_radius=10, height=45)
        self.live_bar.grid(row=2, column=0, sticky="ew", padx=30, pady=(5, 15))
        self.live_bar.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.live_bar, text="🎧", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(15, 8), pady=12)
        
        self.live_text = ctk.CTkLabel(
            self.live_bar,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#aaa",
            anchor="w"
        )
        self.live_text.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Quick actions (Fitts: grouped, easy access)
        self.clear_btn = ctk.CTkButton(
            self.live_bar,
            text="Limpiar",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#3a3a4c",
            hover_color="#4a4a5c",
            command=self._clear_text
        )
        self.clear_btn.grid(row=0, column=2, padx=5)
        
        self.export_btn = ctk.CTkButton(
            self.live_bar,
            text="💾",
            width=35,
            height=30,
            fg_color="#3a3a4c",
            hover_color="#4a4a5c",
            command=self._export_text
        )
        self.export_btn.grid(row=0, column=3, padx=(0, 15))
    
    def _toggle_settings(self):
        """Toggle settings panel visibility (Norman: progressive disclosure)"""
        if self.settings_visible:
            self.settings_frame.grid_forget()
            self.settings_visible = False
        else:
            self.settings_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
            self.settings_visible = True
    
    def _on_source_change(self, value):
        """Handle audio source change"""
        self.use_microphone = "Mic" in value
        source_name = "micrófono" if self.use_microphone else "altavoz"
        self.status_text.configure(text=f"Fuente: {source_name}")
    
    def _on_model_change(self, value):
        """Map simplified names to actual models (Hick: reduce complexity)"""
        model_map = {"Rápido": "small", "Balanceado": "medium", "Preciso": "large-v3"}
        self.selected_model = model_map.get(value, "medium")
        self.whisper_model = None  # Force reload
    
    def _on_translate_toggle(self):
        """Toggle translation"""
        self.translate_enabled = self.trans_switch.get()
        self._update_translation_visibility()
    
    def _update_translation_visibility(self):
        """Show/hide translation panel"""
        if self.translate_enabled and TRANSLATION_AVAILABLE:
            self.trans_label.grid()
            self.translated_text.grid()
        else:
            self.trans_label.grid_remove()
            self.translated_text.grid_remove()
    
    def _toggle_transcription(self):
        """Start or stop transcription"""
        if self.is_running:
            self._stop()
        else:
            self._start()
    
    def _start(self):
        """Start transcription"""
        self.is_running = True
        
        # Visual feedback (Norman: clear state change)
        self.main_btn.configure(
            text="⏹  Detener",
            fg_color="#e63946",
            hover_color="#c53030"
        )
        self.status_dot.configure(text_color="#ffaa00")
        self.status_text.configure(text="Preparando...")
        
        self.audio_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.audio_thread.start()
    
    def _stop(self):
        """Stop transcription"""
        self.is_running = False
        
        self.main_btn.configure(
            text="🎙️  Iniciar Transcripción",
            fg_color="#00a67d",
            hover_color="#008f6b"
        )
        self.status_dot.configure(text_color="#666")
        self.status_text.configure(text="Listo para transcribir")
        self.live_text.configure(text="")
    
    def _init_translation(self):
        """Initialize translation in background"""
        try:
            argostranslate.package.update_package_index()
            packages = argostranslate.package.get_available_packages()
            pkg = next((p for p in packages if p.from_code == "en" and p.to_code == "es"), None)
            if pkg:
                installed = argostranslate.package.get_installed_packages()
                if not any(p.from_code == "en" and p.to_code == "es" for p in installed):
                    argostranslate.package.install_from_path(pkg.download())
                self.translate_func = lambda t: argostranslate.translate.translate(t, "en", "es")
        except: pass
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            self.text_queue.put(("status", f"Cargando modelo..."))
            
            try:
                import ctranslate2
                device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
                compute = "float16" if device == "cuda" else "int8"
            except:
                device, compute = "cpu", "int8"
            
            self.whisper_model = WhisperModel(self.selected_model, device=device, compute_type=compute)
            return True
        except Exception as e:
            self.text_queue.put(("error", str(e)))
            return False
    
    def _transcription_worker(self):
        """Background transcription"""
        try:
            if self.whisper_model is None and not self._load_model():
                self.after(0, self._stop)
                return
            
            p = pyaudio.PyAudio()
            wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            
            if self.use_microphone:
                device = p.get_device_info_by_index(wasapi["defaultInputDevice"])
            else:
                speakers = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
                device = speakers
                if not speakers.get("isLoopbackDevice"):
                    for lb in p.get_loopback_device_info_generator():
                        if speakers["name"] in lb["name"]:
                            device = lb
                            break
            
            rate = int(device["defaultSampleRate"])
            channels = device["maxInputChannels"]
            buffer_frames = int(rate * BUFFER_DURATION)
            chunk_frames = int(SAMPLE_RATE * CHUNK_DURATION)
            
            stream = p.open(
                format=pyaudio.paInt16, channels=channels, rate=rate,
                frames_per_buffer=buffer_frames, input=True,
                input_device_index=device["index"]
            )
            
            self.text_queue.put(("ready", "Escuchando..."))
            
            audio_buffer = np.array([], dtype=np.float32)
            last_text = ""
            
            while self.is_running:
                data = stream.read(buffer_frames, exception_on_overflow=False)
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                if channels == 2:
                    audio = audio.reshape(-1, 2).mean(axis=1)
                if rate != SAMPLE_RATE:
                    new_len = int(len(audio) * SAMPLE_RATE / rate)
                    audio = np.interp(np.linspace(0, len(audio)-1, new_len), np.arange(len(audio)), audio).astype(np.float32)
                
                audio_buffer = np.concatenate([audio_buffer, audio])
                
                if len(audio_buffer) >= chunk_frames:
                    segments, _ = self.whisper_model.transcribe(
                        audio_buffer[:chunk_frames], language="en", beam_size=5,
                        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500)
                    )
                    
                    text = " ".join(s.text.strip() for s in segments).strip()
                    if text and text != last_text:
                        self.text_queue.put(("final", text))
                        last_text = text
                    
                    audio_buffer = audio_buffer[chunk_frames - int(SAMPLE_RATE * 0.5):]
                
                secs = len(audio_buffer) / SAMPLE_RATE
                self.text_queue.put(("partial", f"Procesando... {secs:.1f}s"))
            
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            self.text_queue.put(("error", str(e)))
    
    def _check_queue(self):
        """Process UI updates from worker thread"""
        try:
            while True:
                msg_type, text = self.text_queue.get_nowait()
                
                if msg_type == "partial":
                    self.live_text.configure(text=text[:80])
                elif msg_type == "status":
                    self.status_text.configure(text=text)
                elif msg_type == "ready":
                    self.status_dot.configure(text_color="#00ff00")
                    self.status_text.configure(text=text)
                elif msg_type == "final":
                    ts = datetime.now().strftime("%H:%M:%S")
                    self.original_text.insert("end", f"[{ts}] {text}\n")
                    self.original_text.see("end")
                    
                    if self.translate_enabled and self.translate_func:
                        try:
                            trans = self.translate_func(text)
                            self.translated_text.insert("end", f"[{ts}] {trans}\n")
                            self.translated_text.see("end")
                        except: pass
                    
                    self.live_text.configure(text="")
                elif msg_type == "error":
                    self.original_text.insert("end", f"⚠️ {text}\n")
        except queue.Empty:
            pass
        self.after(100, self._check_queue)
    
    def _clear_text(self):
        self.original_text.delete("1.0", "end")
        self.translated_text.delete("1.0", "end")
    
    def _export_text(self):
        from tkinter import filedialog
        fn = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")],
            initialfile=f"transcripcion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if fn:
            with open(fn, "w", encoding="utf-8") as f:
                f.write("=== TRANSCRIPCIÓN ===\n\n")
                f.write(self.original_text.get("1.0", "end"))
                if self.translate_enabled:
                    f.write("\n\n=== TRADUCCIÓN ===\n\n")
                    f.write(self.translated_text.get("1.0", "end"))
            self.status_text.configure(text="Exportado ✓")
            self.after(2000, lambda: self.status_text.configure(text="Escuchando..." if self.is_running else "Listo"))


if __name__ == "__main__":
    TranscriptionApp().mainloop()
