import customtkinter as ctk
import threading
import json

# Import subject configs to adapt UI based on subject
from learning_assistant.prompts import SUBJECT_CONFIGS, DEFAULT_SUBJECT

class StudyPanel(ctk.CTkFrame):
    def __init__(self, parent, session_manager):
        super().__init__(parent, fg_color="#1a1a2e")  # Dark modern background
        self.session_manager = session_manager
        self.current_class_id = None
        self.data = {}
        self.current_subject = DEFAULT_SUBJECT  # Will be updated when data loads
        
        # Analysis state tracking (UX: show processing state)
        self.analysis_in_progress = False
        self.current_step = 0
        self.total_steps = 4
        self.completed_types = set()  # Track which data types are ready
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. NAVIGATION SIDEBAR (Fitts: Edge grouping)
        self.nav_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#252535")
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(6, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.nav_frame, text="🎓 Study AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)
        
        # Nav Buttons (Hick: Group options logically)
        self.nav_buttons = []
        self.nav_btn_keys = []  # Track button keys for dynamic hiding
        
        self.create_nav_btn("📊 Dashboard", self.show_dashboard, 1, "dashboard")
        self.create_nav_btn("📖 Vocabulario", self.show_vocab, 2, "vocabulary")
        self.create_nav_btn("📝 Quiz", self.show_quiz, 3, "quiz")
        self.create_nav_btn("🧠 Flashcards", self.show_flashcards, 4, "flashcards")
        self.create_nav_btn("🔍 Gramática", self.show_grammar, 5, "grammar")  # English only
        self.create_nav_btn("💬 Roleplay AI", self.show_chat, 6, "chat")
        self.create_nav_btn("📜 Historial", self.show_history, 7, "history")
        
        self.chat_history = []
        
        # 2. CONTENT AREA (Norman: Focus area)
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def create_nav_btn(self, text, command, row, key):
        """Create navigation button with key for dynamic visibility."""
        btn = ctk.CTkButton(
            self.nav_frame,
            text=text,
            command=lambda: self.select_nav(btn, command),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            height=50,
            font=ctk.CTkFont(size=15)
        )
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        self.nav_buttons.append((btn, key))
        self.nav_btn_keys.append(key)

    def update_nav_visibility(self):
        """Show/hide nav buttons based on subject features (Norman: show only relevant)."""
        config = SUBJECT_CONFIGS.get(self.current_subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
        show_grammar = config.get("show_grammar", False)
        
        for btn, key in self.nav_buttons:
            if key == "grammar" and not show_grammar:
                btn.grid_remove()
            else:
                btn.grid()

    def select_nav(self, selected_btn, command):
        """Visual feedback for selection."""
        for btn, _ in self.nav_buttons:
            btn.configure(fg_color="transparent")
        selected_btn.configure(fg_color="#5a189a")
        self.current_nav_cmd = command  # Track current view for refresh
        command()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _create_skeleton_loader(self, parent, count=3, height=60):
        """Create animated skeleton loaders (UX: perceived performance)."""
        skeleton_frame = ctk.CTkFrame(parent, fg_color="transparent")
        skeleton_frame.pack(fill="x", pady=10)
        
        for i in range(count):
            # Skeleton card with pulse effect simulation
            card = ctk.CTkFrame(skeleton_frame, fg_color="#2b2b3b", corner_radius=10, height=height)
            card.pack(fill="x", pady=5)
            card.pack_propagate(False)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=15, pady=12)
            
            # Skeleton lines with gradient effect
            bar1 = ctk.CTkFrame(inner, fg_color="#3a3a4c", corner_radius=4, height=14, width=120)
            bar1.pack(anchor="w")
            
            bar2 = ctk.CTkFrame(inner, fg_color="#333344", corner_radius=4, height=10, width=200 + i*30)
            bar2.pack(anchor="w", pady=(8, 0))
        
        # Processing indicator
        indicator = ctk.CTkFrame(skeleton_frame, fg_color="transparent")
        indicator.pack(fill="x", pady=(15, 5))
        ctk.CTkLabel(indicator, text="⏳ Procesando con IA...", text_color="#ce93d8", font=ctk.CTkFont(size=13)).pack()
        
        return skeleton_frame

    def show_loading(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="⏳ Esperando datos...", font=ctk.CTkFont(size=20)).pack(expand=True)

    def load_data(self, class_id, keep_view=False):
        """Load class data and update subject."""
        self.current_class_id = class_id
        if not keep_view: 
            self.show_loading_animation()
        threading.Thread(target=self._fetch_data, args=(class_id, keep_view)).start()

    def show_loading_animation(self):
        self.clear_content()
        
        # Centered Loading Container
        self.loading_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.loading_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        ctk.CTkLabel(self.loading_frame, text="🧠", font=ctk.CTkFont(size=80)).pack(pady=(50, 20))
        
        # Step indicator (Norman: clear system status)
        self.step_lbl = ctk.CTkLabel(self.loading_frame, text="Paso 0/4", font=ctk.CTkFont(size=18), text_color="#ce93d8")
        self.step_lbl.pack(pady=(0, 5))
        
        self.status_lbl = ctk.CTkLabel(self.loading_frame, text="Iniciando motor AI...", font=ctk.CTkFont(size=20, weight="bold"))
        self.status_lbl.pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, width=400, height=15, progress_color="#5a189a")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=20)
        
        self.percent_lbl = ctk.CTkLabel(self.loading_frame, text="0%", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ce93d8")
        self.percent_lbl.pack()
        
        self.time_lbl = ctk.CTkLabel(self.loading_frame, text="⏱️ Tiempo estimado: ~40 segundos", text_color="gray")
        self.time_lbl.pack(pady=5)

    def update_progress(self, msg, percent, current_step=0, total_steps=4):
        """Update loading state from callback with step numbers."""
        if hasattr(self, 'status_lbl') and self.status_lbl.winfo_exists():
            self.status_lbl.configure(text=msg)
            self.progress_bar.set(percent)
            self.percent_lbl.configure(text=f"{int(percent*100)}%")
            
            # Update step indicator
            if hasattr(self, 'step_lbl') and self.step_lbl.winfo_exists():
                self.step_lbl.configure(text=f"Paso {current_step}/{total_steps}")
            
            # Improved time estimation (~10s per step)
            remaining_steps = total_steps - current_step
            est_seconds = remaining_steps * 10  # ~10 seconds per step
            if est_seconds > 0:
                self.time_lbl.configure(text=f"⏱️ Tiempo restante: ~{est_seconds} segundos")
            else:
                self.time_lbl.configure(text="✨ Finalizando...")

    def _fetch_data(self, class_id, keep_view=False):
        """Fetch data and update subject from class info."""
        self.data = self.session_manager.get_class_data(class_id)
        
        # Get subject from class info
        info = self.data.get('info', {})
        self.current_subject = info.get('subject', DEFAULT_SUBJECT)
        
        # Update UI on main thread
        self.after(0, lambda: self._on_data_loaded(keep_view))

    def _on_data_loaded(self, keep_view=False):
        """Callback when data is fully loaded."""
        self.update_nav_visibility()
        # Select first nav button and show dashboard
        if not keep_view and self.nav_buttons:
            self.select_nav(self.nav_buttons[0][0], self.show_dashboard)
        elif keep_view and hasattr(self, 'current_nav_cmd'):
            self.current_nav_cmd()

    def refresh_current_view(self):
        """Lightweight refresh: Reload data and re-render current view without full reset."""
        if not self.current_class_id:
            return
        
        # Reload data from DB (fresh state)
        self.data = self.session_manager.get_class_data(self.current_class_id)
        
        # Get subject from class info
        info = self.data.get('info', {})
        self.current_subject = info.get('subject', DEFAULT_SUBJECT)
        
        # Re-render current view if we have one
        if hasattr(self, 'current_nav_cmd') and self.current_nav_cmd:
            self.current_nav_cmd()
            
    def set_loading_state(self, is_loading: bool):
        """Enable/Disable navigation buttons based on loading state."""
        self.analysis_in_progress = is_loading
        
        if is_loading:
            # Reset tracking on new analysis
            self.completed_types = set()
            self.current_step = 0
        
        state = "disabled" if is_loading else "normal"
        for btn, _ in self.nav_buttons:
            btn.configure(state=state)
            
        # If loading, ensure we are on dashboard (first tab)
        if is_loading and self.nav_buttons:
            self.select_nav(self.nav_buttons[0][0], self.show_dashboard)
    
    def mark_data_ready(self, data_type):
        """Mark a data type as ready (called from progress callback)."""
        self.completed_types.add(data_type)
        self.current_step = len(self.completed_types)

    # ================= VIEWS =================

    def show_dashboard(self):
        self.clear_content()
        info = self.data.get('info', {})
        config = SUBJECT_CONFIGS.get(self.current_subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
        
        # Header with subject badge
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text=f"{config['icon']} Resumen de Clase", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        # Subject badge
        subject_badge = ctk.CTkFrame(header, fg_color="#5a189a", corner_radius=15)
        subject_badge.pack(side="right")
        ctk.CTkLabel(subject_badge, text=config['name'], font=ctk.CTkFont(size=14), text_color="white").pack(padx=15, pady=5)
        
        # Mini Progress Bar (UX: persistent progress indicator during analysis)
        if self.analysis_in_progress:
            progress_frame = ctk.CTkFrame(self.content_frame, fg_color="#252535", corner_radius=8)
            progress_frame.pack(fill="x", pady=(0, 15))
            
            prog_inner = ctk.CTkFrame(progress_frame, fg_color="transparent")
            prog_inner.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(prog_inner, text="🧠 Análisis en progreso", font=ctk.CTkFont(size=13, weight="bold"), text_color="#ce93d8").pack(side="left")
            
            mini_progress = ctk.CTkProgressBar(prog_inner, width=150, height=8, progress_color="#7b2cbf")
            mini_progress.set(self.current_step / max(self.total_steps, 1))
            mini_progress.pack(side="right", padx=(10, 0))
            
            step_text = f"{self.current_step}/{self.total_steps}"
            ctk.CTkLabel(prog_inner, text=step_text, font=ctk.CTkFont(size=12), text_color="#888").pack(side="right", padx=5)
        
        # Level Badge (only for English)
        if config.get("show_level", False) and info.get('level'):
            level_frame = ctk.CTkFrame(self.content_frame, fg_color="#00a67d", corner_radius=20)
            level_frame.pack(anchor="w", pady=(0, 15))
            ctk.CTkLabel(level_frame, text=f"Nivel CEFR: {info.get('level', '?')}", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(padx=20, pady=10)
        
        # Summary Text - Show skeleton if pending
        if not info.get('summary'):
            pending_frame = ctk.CTkFrame(self.content_frame, fg_color="#2b2b3b", corner_radius=10)
            pending_frame.pack(fill="x", pady=10)
            pending_inner = ctk.CTkFrame(pending_frame, fg_color="transparent")
            pending_inner.pack(padx=20, pady=20)
            
            # Skeleton bars for summary
            for w in [280, 320, 200]:
                bar = ctk.CTkFrame(pending_inner, fg_color="#3a3a4c", corner_radius=4, height=12, width=w)
                bar.pack(anchor="w", pady=4)
            
            ctk.CTkLabel(pending_inner, text="📝 Generando resumen...", text_color="#888", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 0))
        else:
            text_box = ctk.CTkTextbox(self.content_frame, font=ctk.CTkFont(size=16), height=250, fg_color="#2b2b3b", corner_radius=10)
            text_box.pack(fill="x", pady=10)
            text_box.insert("1.0", info.get('summary', ''))
            text_box.configure(state="disabled")

        # Stats with processing indicators (UX: clear system status)
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="#252535", corner_radius=10)
        stats_frame.pack(fill="x", pady=15)
        
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(padx=15, pady=12)
        
        vocab_count = len(self.data.get('vocabulary', []))
        quiz_count = len(self.data.get('questions', []))
        flash_count = len(self.data.get('flashcards', []))
        
        # Helper for status text
        def stat_item(icon, label, count, data_type):
            frame = ctk.CTkFrame(stats_inner, fg_color="transparent")
            frame.pack(side="left", padx=12)
            
            if count > 0:
                # Ready state
                text = f"{icon} {label}: ✅ {count}"
                color = "#a6e3a1"  # Green
            elif data_type in self.completed_types:
                # Completed but empty
                text = f"{icon} {label}: 0"
                color = "#888"
            elif self.analysis_in_progress:
                # Still processing
                text = f"{icon} {label}: ⏳"
                color = "#f9e784"  # Yellow/amber
            else:
                text = f"{icon} {label}: 0"
                color = "#888"
            
            ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=14), text_color=color).pack()
        
        stat_item("📖", "Vocabulario", vocab_count, "vocabulary")
        stat_item("📝", "Quiz", quiz_count, "questions")
        stat_item("🧠", "Flashcards", flash_count, "flashcards")

    def show_vocab(self):
        self.clear_content()
        config = SUBJECT_CONFIGS.get(self.current_subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
        vocab_label = config.get("vocabulary_label", "Vocabulario")
        
        ctk.CTkLabel(self.content_frame, text=f"📖 {vocab_label}", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        vocab_list = self.data.get('vocabulary', [])
        
        # UX: Show skeleton loader if analysis in progress and data not ready
        if not vocab_list:
            if self.analysis_in_progress and 'vocabulary' not in self.completed_types:
                self._create_skeleton_loader(scroll, count=4, height=70)
            else:
                ctk.CTkLabel(scroll, text=f"No se encontró {vocab_label.lower()}.", text_color="#888").pack(pady=20)
            return

        for v in vocab_list:
            card = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=10)
            card.pack(fill="x", pady=8)
            
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(left, text=v['word'], font=ctk.CTkFont(size=18, weight="bold"), text_color="#ce93d8").pack(anchor="w")
            term_type = v.get('type', 'concept').replace("_", " ").title()
            ctk.CTkLabel(left, text=term_type, font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
            
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(right, text=v['definition'], font=ctk.CTkFont(size=14), wraplength=400).pack(anchor="w")
            if v.get('example'):
                ctk.CTkLabel(right, text=f"💡 \"{v['example']}\"", font=ctk.CTkFont(size=13, slant="italic"), text_color="#aaa").pack(anchor="w", pady=(5,0))
            
            if v.get('code'):
                code_frame = ctk.CTkFrame(right, fg_color="#1e1e2e", corner_radius=5)
                code_frame.pack(fill="x", pady=5, anchor="w")
                ctk.CTkLabel(code_frame, text=v['code'], font=ctk.CTkFont(family="Consolas", size=12), text_color="#a6e3a1", justify="left").pack(anchor="w", padx=10, pady=5)

    def show_quiz(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="📝 Quiz de Comprensión", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        questions = self.data.get('questions', [])
        
        # UX: Show skeleton loader if analysis in progress and data not ready
        if not questions:
            if self.analysis_in_progress and 'questions' not in self.completed_types:
                self._create_skeleton_loader(scroll, count=3, height=100)
            else:
                ctk.CTkLabel(scroll, text="No hay preguntas disponibles.", text_color="#888").pack(pady=20)
            return
        
        for i, q in enumerate(questions):
            q_frame = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=15)
            q_frame.pack(fill="x", pady=15)
            
            ctk.CTkLabel(q_frame, text=f"Q{i+1}: {q['question']}", font=ctk.CTkFont(size=16, weight="bold"), wraplength=500).pack(anchor="w", padx=20, pady=15)
            
            opts_frame = ctk.CTkFrame(q_frame, fg_color="transparent")
            opts_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            try:
                options = json.loads(q['options_json'])
                for opt in options:
                    btn = ctk.CTkRadioButton(opts_frame, text=opt, font=ctk.CTkFont(size=14), hover_color="#5a189a", fg_color="#7b2cbf")
                    btn.pack(anchor="w", pady=5)
            except: pass
            
            ans_frame = ctk.CTkFrame(q_frame, fg_color="#1a1a2e", height=40)
            ans_lbl = ctk.CTkLabel(ans_frame, text=f"✅ {q['correct_answer']}\nℹ️ {q.get('explanation','')}", 
                                  font=ctk.CTkFont(size=13), justify="left", wraplength=450)
            ans_lbl.pack(padx=10, pady=10)
            
            ctk.CTkButton(q_frame, text="👁️ Ver Respuesta", width=120, height=30, 
                         fg_color="#3a3a4c", hover_color="#4a4a5c",
                         command=lambda f=ans_frame: f.pack(fill="x", padx=20, pady=10)).pack(anchor="e", padx=20, pady=(0, 15))

    def show_flashcards(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="🧠 Flashcards (Repaso)", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        flashcards = self.data.get('flashcards', [])
        
        # UX: Show skeleton loader if analysis in progress and data not ready
        if not flashcards:
            if self.analysis_in_progress and 'flashcards' not in self.completed_types:
                # Show skeleton card
                skeleton_card = ctk.CTkFrame(self.content_frame, fg_color="#2b2b3b", corner_radius=20, width=500, height=250)
                skeleton_card.pack(pady=30)
                skeleton_card.pack_propagate(False)
                
                inner = ctk.CTkFrame(skeleton_card, fg_color="transparent")
                inner.pack(expand=True)
                
                for w in [200, 150, 100]:
                    bar = ctk.CTkFrame(inner, fg_color="#3a3a4c", corner_radius=4, height=16, width=w)
                    bar.pack(pady=6)
                
                ctk.CTkLabel(inner, text="⏳ Generando flashcards...", text_color="#ce93d8", font=ctk.CTkFont(size=13)).pack(pady=(15, 0))
            else:
                ctk.CTkLabel(self.content_frame, text="No hay flashcards disponibles.", text_color="#888").pack(pady=20)
            return
            
        self.card_index = 0
        self.flashcards = flashcards
        
        self.card_display = ctk.CTkButton(
            self.content_frame,
            text=flashcards[0]['front'],
            font=ctk.CTkFont(size=24, weight="bold"),
            fg_color="#5a189a",
            hover_color="#7b2cbf",
            corner_radius=20,
            width=500,
            height=300,
            command=self.flip_card
        )
        self.card_display.pack(pady=40)
        self.card_showing_front = True
        
        ctk.CTkLabel(self.content_frame, text="Clic en la tarjeta para girar", text_color="gray").pack()
        
        ctrl_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctrl_frame.pack(pady=20)
        
        ctk.CTkButton(ctrl_frame, text="⬅️ Anterior", width=150, height=40, command=self.prev_card).pack(side="left", padx=10)
        self.counter_lbl = ctk.CTkLabel(ctrl_frame, text=f"1 / {len(flashcards)}", font=ctk.CTkFont(size=16))
        self.counter_lbl.pack(side="left", padx=20)
        ctk.CTkButton(ctrl_frame, text="Siguiente ➡️", width=150, height=40, command=self.next_card).pack(side="left", padx=10)

    def flip_card(self):
        card = self.flashcards[self.card_index]
        if self.card_showing_front:
            self.card_display.configure(text=card['back'], fg_color="#00a67d", hover_color="#008f6b")
            self.card_showing_front = False
        else:
            self.card_display.configure(text=card['front'], fg_color="#5a189a", hover_color="#7b2cbf")
            self.card_showing_front = True

    def next_card(self):
        if self.card_index < len(self.flashcards) - 1:
            self.card_index += 1
            self.reset_card_view()

    def prev_card(self):
        if self.card_index > 0:
            self.card_index -= 1
            self.reset_card_view()

    def reset_card_view(self):
        self.card_showing_front = True
        self.card_display.configure(text=self.flashcards[self.card_index]['front'], fg_color="#5a189a", hover_color="#7b2cbf")
        self.counter_lbl.configure(text=f"{self.card_index + 1} / {len(self.flashcards)}")

    def show_grammar(self):
        """Show grammar analysis (English only)."""
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="🔍 Análisis Gramatical y Contextual", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Check if this subject supports grammar
        config = SUBJECT_CONFIGS.get(self.current_subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
        if not config.get("show_grammar", False):
            ctk.CTkLabel(self.content_frame, text="⚠️ El análisis gramatical solo está disponible para el modo English.", text_color="#888").pack(pady=20)
            return
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        grammar_list = self.data.get('grammar', [])
        
        if not grammar_list:
            ctk.CTkLabel(scroll, text="No se encontró análisis gramatical avanzado.").pack(pady=20)
            return

        for g in grammar_list:
            card = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=10)
            card.pack(fill="x", pady=10)
            
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=15, pady=(15, 5))
            
            ctk.CTkLabel(header, text=g['concept'], font=ctk.CTkFont(size=18, weight="bold"), text_color="#ce93d8").pack(side="left")
            
            if g.get('tone_learning'):
                ctk.CTkLabel(header, text=f"🎭 {g['tone_learning']}", font=ctk.CTkFont(size=12), text_color="#00e5ff").pack(side="right")
            
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="x", padx=15, pady=(0, 15))
            
            ctk.CTkLabel(content, text="🗣️ Cita original:", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(5,0))
            ctk.CTkLabel(content, text=f'"{g["example_in_text"]}"', font=ctk.CTkFont(size=14, slant="italic")).pack(anchor="w", padx=10)
            
            ctk.CTkLabel(content, text="💡 Análisis Contextual:", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(10,0))
            ctk.CTkLabel(content, text=g['explanation'], font=ctk.CTkFont(size=14), wraplength=600).pack(anchor="w", padx=10)
            
            rule_frame = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=5)
            rule_frame.pack(fill="x", pady=(10, 0))
            ctk.CTkLabel(rule_frame, text=f"📚 Regla: {g['rule']}", font=ctk.CTkFont(size=12), text_color="#aaa").pack(padx=10, pady=5, anchor="w")

    def show_chat(self):
        self.clear_content()
        config = SUBJECT_CONFIGS.get(self.current_subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
        ctk.CTkLabel(self.content_frame, text=f"💬 Simulador Roleplay - {config['icon']} {config['name']}", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        self.chat_display = ctk.CTkScrollableFrame(self.content_frame, fg_color="#2b2b3b", corner_radius=10)
        self.chat_display.pack(fill="both", expand=True, pady=(0, 20))
        
        input_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Escribe tu pregunta aquí...", font=ctk.CTkFont(size=14), height=40)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda e: self._send_chat())
        
        send_btn = ctk.CTkButton(input_frame, text="Enviar 🚀", width=100, height=40, command=self._send_chat, fg_color="#5a189a", hover_color="#7b2cbf")
        send_btn.pack(side="right")
        
        if not self.chat_history:
            greeting = f"¡Hola! Soy tu {config['name']} virtual. ¿Qué te gustaría preguntarme sobre el contenido de la clase?"
            self._display_message("assistant", greeting)
            self.chat_history.append({'role': 'assistant', 'content': greeting})
        else:
            for msg in self.chat_history:
                self._display_message(msg['role'], msg['content'])

    def _display_message(self, role, text):
        align = "e" if role == "user" else "w"
        color = "#4a4a5c" if role == "user" else "#1a1a2e"
        text_color = "white" if role == "user" else "#ce93d8"
        
        bubble = ctk.CTkFrame(self.chat_display, fg_color=color, corner_radius=15)
        bubble.pack(anchor=align, pady=5, padx=10, fill="x" if len(text) > 50 else "none")
        
        ctk.CTkLabel(bubble, text=text, font=ctk.CTkFont(size=14), wraplength=400, justify="left", text_color=text_color).pack(padx=15, pady=10)

    def _send_chat(self):
        msg = self.chat_entry.get().strip()
        if not msg: return
        
        self.chat_entry.delete(0, "end")
        self._display_message("user", msg)
        self.chat_history.append({'role': 'user', 'content': msg})
        
        threading.Thread(target=self._process_chat_response, args=(msg,)).start()
        
    def _process_chat_response(self, user_msg):
        response = self.session_manager.chat_with_class(self.current_class_id, user_msg, self.chat_history[:-1])
        self.after(0, lambda: self._complete_chat(response))

    def _complete_chat(self, response):
        self._display_message("assistant", response)
        self.chat_history.append({'role': 'assistant', 'content': response})

    def show_history(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="📜 Historial de Sesiones", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        try:
            # Lazy loading: fetch list only
            sessions = self.session_manager.db.get_recent_classes(limit=20)
        except Exception as e:
            print(f"Error fetching history: {e}")
            sessions = []
        
        if not sessions:
            ctk.CTkLabel(scroll, text="No hay historial disponible.").pack(pady=20)
            return
            
        for s in sessions:
            card = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=10)
            card.pack(fill="x", pady=5)
            
            # Layout
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=10, fill="x", expand=True)
            
            title = s.get('title', 'Sin Título')
            date_str = s.get('timestamp', '').split('T')[0]
            if 'source' in s and s['source']:
                source_label = s['source'].split('/')[-1]
            else:
                source_label = "Desconocido"
                
            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"📅 {date_str} | 📂 {source_label}", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")

            # Button to load
            btn = ctk.CTkButton(card, text="Abrir >", width=80, 
                                command=lambda sid=s['id']: self.load_data(sid))
            btn.pack(side="right", padx=15)
