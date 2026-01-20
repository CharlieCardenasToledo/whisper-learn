# 🎙️ Live Transcription & Translation

Aplicación de escritorio moderna para transcribir en vivo audio del sistema (Teams, YouTube, etc.) y traducirlo automáticamente a español.

![Demo](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Características

- 🎤 **Captura de audio del sistema** - Transcribe lo que suena en tus parlantes (loopback WASAPI)
- 🔊 **Modo en vivo** - Texto parcial actualizado en tiempo real como subtítulos
- 🌐 **Traducción offline** - Inglés → Español usando Argos Translate (sin internet)
- 🌙 **UI moderna** - Interfaz oscura con CustomTkinter
- 💾 **Exportar** - Guarda la transcripción y traducción a archivo de texto
- 🔒 **100% local** - Todo funciona sin conexión a internet

## 📸 Screenshot

```
┌──────────────────────────────────────────────────────────────┐
│  🎙️ Live Transcription                     ● Escuchando...  │
├──────────────────────────────────────────────────────────────┤
│  [▶ Iniciar] [🗑️ Limpiar] [💾 Exportar]  [Traducir ○────]   │
├──────────────────────────────────────────────────────────────┤
│  📝 Transcripción Original    │  🌐 Traducción (Español)     │
│  ─────────────────────────    │  ───────────────────────     │
│  [10:30:15] Hello everyone    │  [10:30:15] Hola a todos     │
│  [10:30:18] Let's start...    │  [10:30:18] Empecemos...     │
├──────────────────────────────────────────────────────────────┤
│  🔊 En vivo: the meeting will begin shortly                  │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Instalación Rápida

### 1. Clonar y configurar entorno

```powershell
cd "d:\Proyectos Personales\live-transcribe-teams"
.\venv\Scripts\Activate.ps1
```

### 2. Descargar modelo de Vosk (si no lo tienes)

```powershell
python download_model.py
```

## 🎮 Uso

### Aplicación con interfaz gráfica (Recomendado)

```powershell
python app_gui.py
```

### Modo consola (sin UI)

```powershell
python live_transcribe_teams.py
```

## 📦 Dependencias

| Librería | Propósito |
|----------|-----------|
| `vosk` | Reconocimiento de voz offline |
| `pyaudiowpatch` | Captura WASAPI loopback (Windows) |
| `customtkinter` | UI moderna |
| `argostranslate` | Traducción offline EN→ES |
| `numpy`, `scipy` | Procesamiento de audio |

## 🔧 Solución de Problemas

### El audio no se detecta

1. Verifica que el audio salga por los parlantes (no Bluetooth)
2. Ejecuta `python -m pyaudiowpatch` para ver dispositivos disponibles

### La traducción no funciona

La primera vez que actives la traducción, se descargará el modelo EN→ES (~100MB).
Requiere conexión a internet solo para esta descarga inicial.

### Error "WASAPI no disponible"

Asegúrate de estar en Windows 10/11. WASAPI loopback no funciona en versiones anteriores.

## 📁 Estructura del Proyecto

```
live-transcribe-teams/
├── app_gui.py              # Aplicación con UI (CustomTkinter)
├── live_transcribe_teams.py # Versión consola
├── download_model.py       # Descarga modelo Vosk
├── model/                  # Modelo de Vosk (inglés)
├── requirements.txt        # Dependencias
├── venv/                   # Entorno virtual
└── README.md
```

## ⚠️ Nota Legal

Usa esta herramienta de manera responsable. Asegúrate de tener permiso de todos los participantes antes de transcribir reuniones o llamadas.

## 🤝 Contribuir

¡Pull requests son bienvenidos! Para cambios mayores, abre un issue primero.

## 📄 Licencia

MIT License - Usa libremente para proyectos personales o comerciales.
