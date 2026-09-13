# 🖼️ Procesador de Imágenes por Lotes (CLI)

Herramienta de línea de comandos escrita en **Python puro** + **Pillow** que automatiza tareas repetitivas sobre carpetas llenas de fotografías: redimensionado masivo, reducción básica de ruido y renombrado secuencial.

Pensada para ahorrar horas de trabajo manual al preparar lotes de fotos (35mm escaneadas, archivos RAW exportados, etc.) antes de importarlas a un programa de edición más exigente.

## ✨ Funcionalidades

- **`resize`** — Redimensiona todas las imágenes de una carpeta a un tamaño fijo, con opción de mantener la proporción original.
- **`denoise`** — Aplica un filtro de suavizado (reducción básica de ruido) a todas las imágenes.
- **`rename`** — Renombra todas las imágenes de forma secuencial (`foto_0001.jpg`, `foto_0002.jpg`, ...).
- **`pipeline`** — Ejecuta los tres pasos anteriores en un único comando.

## 📦 Requisitos

- Python 3.9 o superior
- La librería [Pillow](https://pypi.org/project/Pillow/)

## 🚀 Instalación

```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
pip install -r requirements.txt
```

## 🛠️ Uso

### Redimensionar
```bash
python batch_processor.py resize --input fotos --output salida --width 1920 --height 1080
```
Añade `--keep-aspect` si no quieres deformar las fotos:
```bash
python batch_processor.py resize --input fotos --output salida --width 1920 --height 1080 --keep-aspect
```

### Reducir ruido
```bash
python batch_processor.py denoise --input fotos --output salida --strength 1
```

### Renombrar en secuencia
```bash
python batch_processor.py rename --input fotos --output salida --prefix vacaciones --start 1 --digits 4
```
Esto genera archivos como `vacaciones_0001.jpg`, `vacaciones_0002.jpg`, etc.

### Pipeline completo (todo en un paso)
```bash
python batch_processor.py pipeline --input fotos --output salida --width 1920 --height 1080 --prefix boda --strength 1
```

## 📁 Formatos soportados

`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`

## 🧱 Estructura del proyecto

```
procesador-lotes/
├── batch_processor.py   # Script principal de la CLI
├── requirements.txt     # Dependencias (Pillow)
├── .gitignore
└── README.md
```

## 💡 Por qué existe esta herramienta

Procesar a mano decenas o cientos de fotografías pesadas (redimensionar, limpiar ruido, renombrar) es un trabajo mecánico y propenso a errores. Esta CLI automatiza ese flujo con un único comando, dejando las imágenes listas para importarlas a Lightroom, Photoshop o cualquier otro editor.
