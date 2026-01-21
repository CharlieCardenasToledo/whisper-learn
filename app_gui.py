"""
Live Transcription + Translation Desktop App
Modern UI with CustomTkinter + Faster-Whisper + Argos Translate

UX Principles Applied:
- Don Norman "Don't Make Me Think": Single window, tabs for clear modes
- Hick's Law: Reduced cognitive load by separating phases (Transcribe vs Identify)
- Fitts' Law: Large targets, optimized layout
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
from utils.logger_config import setup_logging
setup_logging()

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

# AI Learning Assistant
from learning_assistant.session_manager import SessionManager
from learning_assistant.prompts import SUBJECT_CONFIGS, DEFAULT_SUBJECT
from ui.study_panel import StudyPanel

SAMPLE_RATE = 16000
CHUNK_DURATION = 3.0
BUFFER_DURATION = 0.5


class TranscriptionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window config
        self.title("Transcriptor y Asistente AI - UIDE")
        self.geometry("1000x800")
        self.minsize(800, 600)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # State
        self.is_running = False
        self.audio_thread = None
        self.text_queue = queue.Queue()
        self.whisper_model = None
        self.translate_func = None
        
        # Settings
        self.selected_model = "medium"
        self.use_microphone = False
        self.translate_enabled = False
        self.settings_visible = False
        self.selected_subject = DEFAULT_SUBJECT
        
        self.session_manager = SessionManager()
        
        # UI Setup
        self._create_ui()
        self._check_queue()
        
        if TRANSLATION_AVAILABLE:
            threading.Thread(target=self._init_translation, daemon=True).start()
    
    def _create_ui(self):
        """Create single-window UI with tabs (Transcribe / Study)"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main TabView (Fitts: Large navigation targets)
        self.tabview = ctk.CTkTabview(self, corner_radius=15, fg_color="#1a1a2e")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Define Tabs
        self.tab_transcribe = self.tabview.add("🎤 Transcripción")
        self.tab_study = self.tabview.add("🧠 Estudio AI")
        
        # Build UI for each tab
        self._create_transcription_ui(self.tab_transcribe)
        self._create_study_ui(self.tab_study)
    
    def _create_transcription_ui(self, parent):
        """UI for Transcription Tab"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # ===== ACTIONS HEADER =====
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 15))
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        
        # Main Button (Fitts: Large)
        self.main_btn = ctk.CTkButton(
            action_frame,
            text="🎙️  Iniciar Transcripción",
            command=self._toggle_transcription,
            font=ctk.CTkFont(size=20, weight="bold"),
            height=60,
            corner_radius=30,
            fg_color="#00a67d",
            hover_color="#008f6b"
        )
        self.main_btn.grid(row=0, column=0, sticky="ew", padx=10)
        
        # Upload Button
        self.upload_btn = ctk.CTkButton(
            action_frame,
            text="📂 Cargar Audio",
            command=self._upload_audio_file,
            font=ctk.CTkFont(size=16),
            height=60,
            corner_radius=30,
            fg_color="#3a3a4c",
            hover_color="#4a4a5c"
        )
        self.upload_btn.grid(row=0, column=1, sticky="ew", padx=10)
        
        # Status Bar
        self.status_bar = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=10, height=35)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.status_dot = ctk.CTkLabel(self.status_bar, text="●", font=ctk.CTkFont(size=14), text_color="#666")
        self.status_dot.pack(side="left", padx=(15, 8), pady=8)
        
        self.status_text = ctk.CTkLabel(self.status_bar, text="Listo para transcribir", font=ctk.CTkFont(size=13), text_color="#999")
        self.status_text.pack(side="left")
        
        # Settings Button
        self.settings_btn = ctk.CTkButton(
            self.status_bar, text="⚙️", width=35, height=25, fg_color="transparent", 
            hover_color="#333", command=self._toggle_settings
        )
        self.settings_btn.pack(side="right", padx=10)
        
        # ===== SETTINGS PANEL =====
        self.settings_frame = ctk.CTkFrame(parent, fg_color="#1a1a2a", corner_radius=10)
        # Hidden by default
        
        settings_inner = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        settings_inner.pack(fill="x", padx=10, pady=10)
        
        # Source
        ctk.CTkLabel(settings_inner, text="Fuente:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.source_switch = ctk.CTkSegmentedButton(settings_inner, values=["🔊 Altavoz", "🎤 Mic"], command=self._on_source_change)
        self.source_switch.set("🔊 Altavoz")
        self.source_switch.pack(side="left", padx=5)
        
        # Model
        ctk.CTkLabel(settings_inner, text="Precisión:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(15, 5))
        self.model_switch = ctk.CTkSegmentedButton(settings_inner, values=["Rápido", "Balanceado", "Preciso"], command=self._on_model_change)
        self.model_switch.set("Balanceado")
        self.model_switch.pack(side="left", padx=5)
        
        # ===== CONTENT AREA =====
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(2, weight=1)
        
        # Transcription Box
        self.original_text = ctk.CTkTextbox(content_frame, font=ctk.CTkFont(size=15), wrap="word", fg_color="#252535", corner_radius=10)
        self.original_text.grid(row=0, column=0, sticky="nsew", pady=5)
        
        # Live Preview Bar
        self.live_bar = ctk.CTkFrame(content_frame, fg_color="#2b2b3b", height=40, corner_radius=8)
        self.live_bar.grid(row=1, column=0, sticky="ew", pady=5)
        self.live_bar.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.live_bar, text="🎧", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10)
        self.live_text = ctk.CTkLabel(self.live_bar, text="", font=ctk.CTkFont(size=13), text_color="#aaa", anchor="w")
        self.live_text.grid(row=0, column=1, sticky="ew")
        
        # Translation Box (Auto-hide)
        self.trans_label = ctk.CTkLabel(content_frame, text="Traducción", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888")
        self.translated_text = ctk.CTkTextbox(content_frame, font=ctk.CTkFont(size=15), wrap="word", fg_color="#252535", corner_radius=10)
        # Hidden until enabled
        
        # ===== SUBJECT & ANALYZE BAR =====
        bottom_frame = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=15, height=140)
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 15))
        
        ctk.CTkLabel(bottom_frame, text="🎓 Asignatura para análisis AI", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888").pack(pady=(10, 5))
        
        # Subject Icons
        subjects_container = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        subjects_container.pack(fill="x", padx=15, pady=5)
        
        self.subject_buttons = {}
        row = 0
        col = 0
        for i, (key, config) in enumerate(SUBJECT_CONFIGS.items()):
            btn = ctk.CTkButton(
                subjects_container,
                text=f"{config['icon']} {config['name']}",
                width=110,
                height=35,
                font=ctk.CTkFont(size=11),
                fg_color="#3a3a4c" if key != self.selected_subject else "#5a189a",
                hover_color="#4a4a5c",
                command=lambda k=key: self._select_subject(k)
            )
            # Layout grid logic (4 per row)
            if i > 0 and i % 4 == 0:
                row += 1
                col = 0
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1
            self.subject_buttons[key] = btn
            
            # Make columns equal width
            subjects_container.grid_columnconfigure(i % 4, weight=1)

        # Analyze Button
        self.analyze_btn = ctk.CTkButton(
            bottom_frame,
            text="🚀 Analizar con IA >",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#5a189a",
            hover_color="#7b2cbf",
            height=45,
            command=self._start_analysis_flow
        )
        self.analyze_btn.pack(fill="x", padx=20, pady=10)

    def _create_study_ui(self, parent):
        """UI for Study Tab (Embedded Panel)"""
        self.study_panel = StudyPanel(parent, self.session_manager)
        self.study_panel.pack(fill="both", expand=True)

    # ===== LOGIC METHODS =====

    def _toggle_settings(self):
        if self.settings_visible:
            self.settings_frame.grid_forget()
            self.settings_visible = False
        else:
            self.settings_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10)) # Adjust row
            self.settings_visible = True

    def _select_subject(self, subject_key):
        self.selected_subject = subject_key
        for key, btn in self.subject_buttons.items():
            btn.configure(fg_color="#5a189a" if key == subject_key else "#3a3a4c")
        
        config = SUBJECT_CONFIGS[subject_key]
        self.status_text.configure(text=f"Modo seleccionado: {config['name']}")

    def _start_analysis_flow(self):
        """Switch tab and start analysis"""
        text = self.original_text.get("1.0", "end").strip()
        if not text:
            self.status_text.configure(text="⚠️ Transcribe algo primero")
            return
        
        # Switch to Study Tab
        self.tabview.set("🧠 Estudio AI")
        self.study_panel.set_loading_state(True) # LOCK UI
        
        # Config status
        config = SUBJECT_CONFIGS[self.selected_subject]
        
        # Callback wrapper to update study panel progress
        def on_progress_wrapper(msg, percent, current_step, total_steps, data_type=None):
            print(f"[DEBUG] on_progress_wrapper: msg={msg}, percent={percent}, step={current_step}/{total_steps}, data_type={data_type}")
            
            # Update step tracking for mini progress bar
            self.study_panel.current_step = current_step
            self.study_panel.total_steps = total_steps
            
            self.after(0, lambda: self.study_panel.update_progress(msg, percent, current_step, total_steps))
            self.after(0, lambda: self.status_text.configure(text=f"🤖 {msg}"))
            
            # Mark data type as ready and refresh (Progressive Disclosure)
            if data_type:
                def on_data():
                    print(f"[DEBUG] on_data: Marking {data_type} as ready")
                    # Track which types are complete
                    self.study_panel.mark_data_ready(data_type)
                    # Just unlock navigation buttons, NOT the analysis_in_progress flag
                    for btn, _ in self.study_panel.nav_buttons:
                        btn.configure(state="normal")
                    # Lightweight refresh - just reload current view with fresh DB data
                    self.study_panel.refresh_current_view()
                self.after(0, on_data)
            
            # Full unlock when complete
            if percent >= 1.0 or "completado" in msg.lower():
                def on_complete():
                    print(f"[DEBUG] on_complete: Analysis finished!")
                    self.study_panel.analysis_in_progress = False
                    self.study_panel.set_loading_state(False)
                    self.study_panel.refresh_current_view()
                self.after(0, on_complete)

        # History Logic: Use existing session if available (e.g. from live transcription)
        class_id = getattr(self.study_panel, 'current_class_id', None)
        
        if not class_id:
            class_id = self.session_manager.create_draft_session(
                text, 
                duration=0, 
                subject=self.selected_subject
            )
            self.study_panel.current_class_id = class_id

        if class_id:
            self.session_manager.start_analysis(class_id, progress_callback=on_progress_wrapper)
            self.study_panel.load_data(class_id, keep_view=True) # Load immediately (draft state)

    # ... (Keep existing transcription/upload logic below) ...
    # (Simplified for brevity, copying core methods from previous version)

    def _on_source_change(self, value):
        self.use_microphone = "Mic" in value
        self.status_text.configure(text=f"Fuente: {'Micrófono' if self.use_microphone else 'Altavoz'}")

    def _on_model_change(self, value):
        model_map = {"Rápido": "small", "Balanceado": "medium", "Preciso": "large-v3"}
        self.selected_model = model_map.get(value, "medium")
        self.whisper_model = None

    def _on_translate_toggle(self):
        # Implementation for translation toggle (optional in this simplified view)
        pass

    def _toggle_transcription(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.is_running = True
        self.main_btn.configure(text="⏹  Detener", fg_color="#e63946", hover_color="#c53030")
        self.status_dot.configure(text_color="#ffaa00")
        self.status_text.configure(text="Preparando transcriptor...")
        self.audio_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.audio_thread.start()

    def _stop(self):
        self.is_running = False
        self.main_btn.configure(text="🎙️  Iniciar Transcripción", fg_color="#00a67d", hover_color="#008f6b")
        self.status_dot.configure(text_color="#666")
        self.status_text.configure(text="Listo")
        self.live_text.configure(text="")

    def _init_translation(self):
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
            stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate,
                            frames_per_buffer=buffer_frames, input=True,
                            input_device_index=device["index"])
            self.text_queue.put(("ready", "Escuchando..."))
            audio_buffer = np.array([], dtype=np.float32)
            last_text = ""
            while self.is_running:
                data = stream.read(buffer_frames, exception_on_overflow=False)
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                if channels == 2: audio = audio.reshape(-1, 2).mean(axis=1)
                if rate != SAMPLE_RATE:
                    new_len = int(len(audio) * SAMPLE_RATE / rate)
                    audio = np.interp(np.linspace(0, len(audio)-1, new_len), np.arange(len(audio)), audio).astype(np.float32)
                audio_buffer = np.concatenate([audio_buffer, audio])
                if len(audio_buffer) >= chunk_frames:
                    # Language logic (User feedback: Force Spanish for non-English subjects)
                    lang = "en" if self.selected_subject == "english" else "es"
                    segments, _ = self.whisper_model.transcribe(
                        audio_buffer[:chunk_frames], language=lang, beam_size=5,
                        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
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
        try:
            while True:
                msg_type, text = self.text_queue.get_nowait()
                if msg_type == "partial": self.live_text.configure(text=text[:80])
                elif msg_type == "status": self.status_text.configure(text=text)
                elif msg_type == "ready": 
                    self.status_dot.configure(text_color="#00ff00")
                    self.status_text.configure(text=text)
                elif msg_type == "final":
                    ts = datetime.now().strftime("%H:%M:%S")
                    self.original_text.insert("end", f"[{ts}] {text}\n")
                    self.original_text.see("end")
                    self.live_text.configure(text="")
                elif msg_type == "fragment":
                    self.original_text.insert("end", text + " ")
                    self.original_text.see("end")
                elif msg_type == "clear":
                    self.original_text.delete("1.0", "end")
                elif msg_type == "error": self.original_text.insert("end", f"⚠️ {text}\n")
        except queue.Empty: pass
        self.after(100, self._check_queue)

    def _upload_audio_file(self):
        from tkinter import filedialog
        filetypes = [("Audio", "*.mp3 *.wav *.flac *.ogg *.m4a *.wma *.aac *.opus"), ("All", "*.*")]
        filepath = filedialog.askopenfilename(title="Seleccionar archivo de audio", filetypes=filetypes)
        if not filepath: return
        self.status_dot.configure(text_color="#ffaa00")
        self.status_text.configure(text=f"📂 Cargando: {filepath.split('/')[-1]}...")
        self.upload_btn.configure(state="disabled", text="⏳ Procesando...")
        self.main_btn.configure(state="disabled")
        threading.Thread(target=self._transcribe_audio_file, args=(filepath,), daemon=True).start()

    def _transcribe_audio_file(self, filepath):
        try:
            if self.whisper_model is None:
                self.text_queue.put(("status", "Cargando modelo..."))
                try:
                    import ctranslate2
                    device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
                    compute = "float16" if device == "cuda" else "int8"
                except: device, compute = "cpu", "int8"
                self.whisper_model = WhisperModel(self.selected_model, device=device, compute_type=compute)
            self.text_queue.put(("status", "Transcribiendo..."))
            
            # Language logic (User feedback: Force Spanish for non-English subjects)
            lang = "en" if self.selected_subject == "english" else "es"
            
            # Streaming (Generator Pattern)
            segments, info = self.whisper_model.transcribe(filepath, language=lang, beam_size=5, vad_filter=True)
            
            full_text = []
            self.text_queue.put(("clear", "")) # Prepare UI
            
            for segment in segments:
                text = segment.text.strip()
                if text:
                    self.text_queue.put(("fragment", text)) # Stream to UI
                    full_text.append(text)
            
            final_text = " ".join(full_text)
            
            if final_text: 
                # Auto-save draft
                self.after(0, lambda: self._on_file_transcribed(final_text, filepath, info.duration))
            else: 
                self.text_queue.put(("status", "⚠️ No se detectó audio"))
                self.after(0, self._reset_btns)
        except Exception as e:
            self.text_queue.put(("error", str(e)))
            self.after(0, self._reset_btns)

    def _on_file_transcribed(self, text, filepath, duration=0):
        import os
        filename = os.path.basename(filepath)
        
        # Save Draft Session immediately
        try:
            class_id = self.session_manager.create_draft_session(
                text, 
                title=f"🎙️ {filename} ({datetime.now().strftime('%H:%M')})",
                duration=int(duration),
                subject=self.selected_subject,
                source=filepath
            )
            self.study_panel.current_class_id = class_id # Track current session
        except Exception as e:
            print(f"Error saving draft: {e}")

        # UI Updates
        # self.original_text.delete("1.0", "end") # Already streamed
        # self.original_text.insert("1.0", f"[📂 {filename}]\n\n{text}\n") # Optional: Header
        self.status_dot.configure(text_color="#00ff00")
        self.status_text.configure(text="Transcripción guardada en historial")
        self._reset_btns()

    def _reset_btns(self):
        self.upload_btn.configure(state="normal", text="📂 Cargar Audio")
        self.main_btn.configure(state="normal")
        self.status_dot.configure(text_color="#666")
    
    def _clear_text(self):
        self.original_text.delete("1.0", "end")

    def _export_text(self):
        pass # Simplified for brevity

if __name__ == "__main__":
    TranscriptionApp().mainloop()
