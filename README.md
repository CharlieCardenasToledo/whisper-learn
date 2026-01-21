# 🎙️ Learning Assistant - Transcripción en Vivo con IA

Aplicación de escritorio moderna para transcribir audio en vivo y generar contenido educativo automáticamente usando inteligencia artificial local.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![AI](https://img.shields.io/badge/AI-Ollama-purple.svg)

## 🎯 Objetivo

Transformar cualquier clase, conferencia o reunión en material de estudio estructurado:
- **Transcripción en tiempo real** del audio del sistema
- **Análisis automático con IA** que genera resúmenes, vocabulario, quizzes y flashcards
- **Interfaz reactiva** que muestra el progreso del análisis en tiempo real

## ✨ Características Principales

### 📝 Transcripción
- 🎤 **Captura de audio del sistema** - Transcribe lo que suena en tus parlantes (WASAPI loopback)
- 🎧 **Soporte para micrófono** - También puede transcribir desde el micrófono
- 🔊 **Modo en vivo** - Texto parcial actualizado en tiempo real como subtítulos
- 📁 **Carga de archivos** - Procesa archivos de audio/video existentes

### 🧠 Asistente de Aprendizaje con IA
- 📊 **Resumen automático** - Genera un resumen conciso de la clase
- 📖 **Extracción de vocabulario** - Identifica términos clave con definiciones y ejemplos
- 📝 **Generación de quiz** - Crea preguntas de opción múltiple para autoevaluación
- 🧠 **Flashcards** - Genera tarjetas de estudio para repaso espaciado
- 📚 **Análisis de gramática** - Para clases de inglés, analiza estructuras gramaticales

### 🎨 Experiencia de Usuario
- 🌙 **UI moderna** - Interfaz oscura con CustomTkinter
- ⚡ **Progreso en tiempo real** - Muestra el avance del análisis de IA con streaming
- 🔄 **Actualización incremental** - Los datos aparecen conforme se generan
- 📊 **Dashboard interactivo** - Estadísticas y navegación intuitiva

### 🔒 Privacidad
- � **100% local** - Toda la IA corre en tu máquina
- 🚫 **Sin nube** - Tus datos nunca salen de tu computadora
- 🔐 **Offline** - Funciona sin conexión a internet

## 📸 Capturas de Pantalla

### Panel de Transcripción
```
┌──────────────────────────────────────────────────────────────┐
│  🎙️ Learning Assistant                      ● Escuchando... │
├──────────────────────────────────────────────────────────────┤
│  [▶ Iniciar] [� Cargar Audio] [� Exportar]                 │
│  Fuente: [Altavoz ▼]  Modelo: [Balanceado ▼]                │
├──────────────────────────────────────────────────────────────┤
│  📝 Transcripción en Vivo                                    │
│  ─────────────────────────                                   │
│  [10:30:15] Hello everyone, welcome to the class...         │
│  [10:30:18] Today we will cover REST APIs and...            │
├──────────────────────────────────────────────────────────────┤
│  🔊 En vivo: the meeting will begin shortly                  │
└──────────────────────────────────────────────────────────────┘
```

### Panel de Estudio AI
```
┌──────────────────────────────────────────────────────────────┐
│  🧠 Estudio AI                                               │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌───────────────────────────────────────────┐  │
│  │📊 Dash  │ │  💻 Resumen de Clase                      │  │
│  │📖 Vocab │ │  ───────────────────────                  │  │
│  │📝 Quiz  │ │  Esta clase cubre el desarrollo de       │  │
│  │🧠 Flash │ │  APIs REST con Node.js y Fastify...      │  │
│  │💬 Chat  │ │                                           │  │
│  │📚 Hist  │ │  📖 Vocabulario: ✅ 12                    │  │
│  └─────────┘ │  📝 Quiz: ✅ 5  🧠 Flashcards: ✅ 9       │  │
│              └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Instalación

### Requisitos Previos
- **Python 3.10+**
- **Ollama** - Para la IA local (https://ollama.ai)
- **Windows 10/11** - Para captura WASAPI loopback

### 1. Clonar e instalar dependencias

```powershell
git clone https://github.com/tu-usuario/live-transcribe-teams.git
cd live-transcribe-teams
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Instalar modelo de Whisper

La primera ejecución descargará automáticamente el modelo de transcripción.

### 3. Configurar Ollama

```powershell
# Instalar Ollama desde https://ollama.ai
# Luego descargar el modelo recomendado:
ollama pull qwen2.5:7b
```

## 🎮 Uso

### Iniciar la aplicación

```powershell
python app_gui.py
```

### Flujo de trabajo típico

1. **Iniciar transcripción**: Click en "▶ Iniciar" para capturar audio
2. **Detener**: Click en "⏹ Detener" cuando termine la clase
3. **Analizar**: La IA procesará automáticamente la transcripción
4. **Estudiar**: Navega por vocabulario, quiz y flashcards en el panel de estudio

### Cargar audio existente

1. Click en "📁 Cargar Audio"
2. Selecciona un archivo .mp3, .wav, .m4a, .mp4, etc.
3. La transcripción y análisis comenzarán automáticamente

## 📦 Dependencias Principales

| Librería | Propósito |
|----------|-----------|
| `faster-whisper` | Transcripción de voz (modelo OpenAI Whisper) |
| `ollama` | Cliente para IA local |
| `customtkinter` | UI moderna |
| `pyaudiowpatch` | Captura WASAPI loopback (Windows) |
| `argostranslate` | Traducción offline EN→ES |
| `pydub` | Procesamiento de audio |

## 📁 Estructura del Proyecto

```
live-transcribe-teams/
├── app_gui.py              # Aplicación principal con UI
├── learning_assistant/     # Módulo de IA
│   ├── agent.py           # Agente LLM para análisis
│   ├── session_manager.py # Gestión de sesiones y datos
│   ├── prompts.py         # Prompts para cada tipo de análisis
│   └── database.py        # Almacenamiento SQLite
├── ui/
│   └── study_panel.py     # Panel de estudio interactivo
├── transcription/         # Módulo de transcripción
│   └── transcriber.py     # Interfaz con Whisper
├── requirements.txt       # Dependencias
└── README.md
```

## 🔧 Solución de Problemas

### El audio no se detecta
1. Verifica que el audio salga por los parlantes (no Bluetooth)
2. Asegúrate de que el dispositivo de audio esté configurado correctamente

### La IA no responde
1. Verifica que Ollama esté corriendo: `ollama list`
2. Descarga el modelo si no existe: `ollama pull qwen2.5:7b`

### Error "WASAPI no disponible"
Asegúrate de estar en Windows 10/11. WASAPI loopback no funciona en versiones anteriores.

## � Materias Soportadas

La IA se adapta automáticamente según el tema detectado:

| Materia | Vocabulario | Características Especiales |
|---------|-------------|---------------------------|
| 🇬🇧 Inglés | Phrasal verbs, idioms | Nivel CEFR, análisis gramática |
| 💻 Programación | APIs, frameworks | Snippets de código |
| 📊 Bases de Datos | SQL, NoSQL, índices | Ejemplos de queries |
| 🔒 Seguridad | Vulnerabilidades, protocolos | CVEs, mitigaciones |
| 📐 Matemáticas | Teoremas, fórmulas | Notación matemática |
| 🌍 General | Términos clave | Definiciones contextuales |

## ⚠️ Nota Legal

Usa esta herramienta de manera responsable. Asegúrate de tener permiso de todos los participantes antes de transcribir reuniones o clases.

## 📄 Licencia

MIT License - Usa libremente para proyectos personales o comerciales.
