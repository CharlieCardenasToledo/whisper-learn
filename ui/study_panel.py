import customtkinter as ctk
import threading
import json

class StudyPanel(ctk.CTkFrame):
    def __init__(self, parent, session_manager):
        super().__init__(parent, fg_color="#1a1a2e") # Dark modern background
        self.session_manager = session_manager
        self.current_class_id = None
        self.data = {}
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. NAVIGATION SIDEBAR (Fitts: Edge grouping, vertical list is scalable)
        self.nav_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#252535")
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.nav_frame, text="🎓 Study AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)
        
        # Nav Buttons (Hick: Group options logically)
        self.nav_buttons = []
        self.create_nav_btn("📊 Dashboard", self.show_dashboard, 1)
        self.create_nav_btn("📖 Vocabulario", self.show_vocab, 2)
        self.create_nav_btn("📝 Quiz", self.show_quiz, 3)
        self.create_nav_btn("🧠 Flashcards", self.show_flashcards, 4)
        self.create_nav_btn("🔍 Gramática", self.show_grammar, 5)
        
        # 2. CONTENT AREA (Norman: Focus area)
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # ... (Rest of init remains)

    # ... (Other methods)

    def show_grammar(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="🔍 Análisis Gramatical y Contextual", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        grammar_list = self.data.get('grammar', [])
        
        if not grammar_list:
            ctk.CTkLabel(scroll, text="No se encontró análisis gramatical avanzado.").pack(pady=20)
            return

        for g in grammar_list:
            card = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=10)
            card.pack(fill="x", pady=10)
            
            # Header: Concept + Tone Badge
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=15, pady=(15, 5))
            
            ctk.CTkLabel(header, text=g['concept'], font=ctk.CTkFont(size=18, weight="bold"), text_color="#ce93d8").pack(side="left")
            
            if g.get('tone_learning'):
                ctk.CTkLabel(header, text=f"🎭 {g['tone_learning']}", font=ctk.CTkFont(size=12), text_color="#00e5ff").pack(side="right")
            
            # Content grid
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="x", padx=15, pady=(0, 15))
            
            # Quote
            ctk.CTkLabel(content, text="🗣️ Cita original:", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(5,0))
            ctk.CTkLabel(content, text=f'"{g["example_in_text"]}"', font=ctk.CTkFont(size=14, slant="italic")).pack(anchor="w", padx=10)
            
            # Explanation (The "Why")
            ctk.CTkLabel(content, text="💡 Análisis Contextual:", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(10,0))
            ctk.CTkLabel(content, text=g['explanation'], font=ctk.CTkFont(size=14), wraplength=600).pack(anchor="w", padx=10)
            
            # Rule (The Theory)
            rule_frame = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=5)
            rule_frame.pack(fill="x", pady=(10, 0))
            ctk.CTkLabel(rule_frame, text=f"📚 Regla: {g['rule']}", font=ctk.CTkFont(size=12), text_color="#aaa").pack(padx=10, pady=5, anchor="w")



    def create_nav_btn(self, text, command, row):
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
        self.nav_buttons.append(btn)
        
    def select_nav(self, selected_btn, command):
        # Visual feedback for selection
        for btn in self.nav_buttons:
            btn.configure(fg_color="transparent")
        selected_btn.configure(fg_color="#5a189a") # Active color
        command()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_loading(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="⏳ Esperando datos...", font=ctk.CTkFont(size=20)).pack(expand=True)

    def load_data(self, class_id):
        self.current_class_id = class_id
        # Show loading indicator (Norman: System status visibility)
        self.select_nav(self.nav_buttons[0], self.show_dashboard) # Default to dashboard
        self.show_loading_animation()
        threading.Thread(target=self._fetch_data, args=(class_id,)).start()
        
    def show_loading_animation(self):
        self.clear_content()
        
        # Centered Loading Container
        self.loading_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.loading_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Brain Animation (using Label for now)
        ctk.CTkLabel(self.loading_frame, text="🧠", font=ctk.CTkFont(size=80)).pack(pady=(50, 20))
        
        # Main Status
        self.status_lbl = ctk.CTkLabel(self.loading_frame, text="Iniciando motor AI...", font=ctk.CTkFont(size=24, weight="bold"))
        self.status_lbl.pack(pady=10)
        
        # Progress Bar (System Visibility)
        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, width=400, height=15, progress_color="#5a189a")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=20)
        
        # Details & Time Estimate
        self.percent_lbl = ctk.CTkLabel(self.loading_frame, text="0%", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ce93d8")
        self.percent_lbl.pack()
        
        self.time_lbl = ctk.CTkLabel(self.loading_frame, text="Tiempo estimado: ~30 segundos", text_color="gray")
        self.time_lbl.pack(pady=5)

    def update_progress(self, msg, percent):
        """Called by app_gui callback to update StudyPanel loading state"""
        if hasattr(self, 'status_lbl') and self.status_lbl.winfo_exists():
            self.status_lbl.configure(text=msg)
            self.progress_bar.set(percent)
            self.percent_lbl.configure(text=f"{int(percent*100)}%")
            
            # Simple time estimation logic
            remaining_steps = 4 - (percent * 4)
            est_seconds = int(remaining_steps * 8) # ~8s per step
            if est_seconds > 0:
                self.time_lbl.configure(text=f"Tiempo estimado: ~{est_seconds} segundos")
            else:
                self.time_lbl.configure(text="Finalizando...")

    def _fetch_data(self, class_id):
        # Poll for completion (when summary is ready)
        # Note: Progress updates come via `update_progress` called from main thread callback
        import time
        max_retries = 60 # Check for 60s
        
        for _ in range(max_retries):
            self.data = self.session_manager.get_class_data(class_id)
            # Check if we have data populated (e.g. flashcards, which is last step)
            if self.data.get('flashcards') and len(self.data.get('flashcards')) > 0:
                 break
            time.sleep(1)
            
        self.after(0, lambda: self.select_nav(self.nav_buttons[0], self.show_dashboard))

    # ================= VIEWS =================

    def show_dashboard(self):
        self.clear_content()
        info = self.data.get('info', {})
        
        # Header
        ctk.CTkLabel(self.content_frame, text="Resumen de Clase", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        if not info.get('summary'):
            ctk.CTkLabel(self.content_frame, text="Generando análisis...").pack()
            return

        # Level Badge (Visual hierarchy)
        level_frame = ctk.CTkFrame(self.content_frame, fg_color="#00a67d", corner_radius=20)
        level_frame.pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(level_frame, text=f"Nivel Estimado: {info.get('level', '?')}", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(padx=20, pady=10)
        
        # Summary Text
        text_box = ctk.CTkTextbox(self.content_frame, font=ctk.CTkFont(size=16), height=300, fg_color="#2b2b3b", corner_radius=10)
        text_box.pack(fill="x", pady=10)
        text_box.insert("1.0", info.get('summary', ''))
        text_box.configure(state="disabled")

    def show_vocab(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="📖 Vocabulario Clave", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        vocab_list = self.data.get('vocabulary', [])
        
        if not vocab_list:
             ctk.CTkLabel(scroll, text="No se encontró vocabulario específico.").pack(pady=20)
             return

        # Card layout for vocab (Better scanning)
        for v in vocab_list:
            card = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=10)
            card.pack(fill="x", pady=8)
            
            # Left: Word & Type
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(left, text=v['word'], font=ctk.CTkFont(size=18, weight="bold"), text_color="#ce93d8").pack(anchor="w")
            ctk.CTkLabel(left, text=v['type'].replace("_", " ").title(), font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
            
            # Right: Definition & Example
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(right, text=v['definition'], font=ctk.CTkFont(size=14), wraplength=400).pack(anchor="w")
            ctk.CTkLabel(right, text=f"💡 \"{v['example']}\"", font=ctk.CTkFont(size=13, slant="italic"), text_color="#aaa").pack(anchor="w", pady=(5,0))

    def show_quiz(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="📝 Quiz de Comprensión", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        questions = self.data.get('questions', [])
        
        for i, q in enumerate(questions):
            q_frame = ctk.CTkFrame(scroll, fg_color="#2b2b3b", corner_radius=15)
            q_frame.pack(fill="x", pady=15)
            
            # Question Header
            ctk.CTkLabel(q_frame, text=f"Q{i+1}: {q['question']}", font=ctk.CTkFont(size=16, weight="bold"), wraplength=500).pack(anchor="w", padx=20, pady=15)
            
            # Options area
            opts_frame = ctk.CTkFrame(q_frame, fg_color="transparent")
            opts_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            try:
                options = json.loads(q['options_json'])
                for opt in options:
                    # Clean look for options
                    btn = ctk.CTkRadioButton(opts_frame, text=opt, font=ctk.CTkFont(size=14), hover_color="#5a189a", fg_color="#7b2cbf")
                    btn.pack(anchor="w", pady=5)
            except: pass
            
            # Reveal Answer (Feedback on demand)
            ans_frame = ctk.CTkFrame(q_frame, fg_color="#1a1a2e", height=40)
            # Hidden by default logic handled by button
            
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
        
        if not flashcards:
            ctk.CTkLabel(self.content_frame, text="No hay flashcards disponibles.").pack()
            return
            
        # Interactive Flashcard Container
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
        
        # Controls (Fitts: Large Nav Buttons)
        ctrl_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctrl_frame.pack(pady=20)
        
        ctk.CTkButton(ctrl_frame, text="⬅️ Anterior", width=150, height=40, command=self.prev_card).pack(side="left", padx=10)
        self.counter_lbl = ctk.CTkLabel(ctrl_frame, text=f"1 / {len(flashcards)}", font=ctk.CTkFont(size=16))
        self.counter_lbl.pack(side="left", padx=20)
        ctk.CTkButton(ctrl_frame, text="Siguiente ➡️", width=150, height=40, command=self.next_card).pack(side="left", padx=10)

    def flip_card(self):
        card = self.flashcards[self.card_index]
        if self.card_showing_front:
            self.card_display.configure(text=card['back'], fg_color="#00a67d", hover_color="#008f6b") # Green for back/success
            self.card_showing_front = False
        else:
            self.card_display.configure(text=card['front'], fg_color="#5a189a", hover_color="#7b2cbf") # Purple for front
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
