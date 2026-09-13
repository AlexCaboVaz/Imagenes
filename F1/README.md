# 🏎️ Analizador de Telemetría de F1

Script de terminal en **Python** (Pandas + Requests) que consume la API pública y gratuita de **[OpenF1](https://openf1.org)** para comparar el ritmo de carrera y los tiempos por vuelta entre escuderías (por ejemplo, Williams contra Ferrari) o analizar el rendimiento de pilotos específicos (por ejemplo, Carlos Sainz).

No hace falta ninguna API key: los datos históricos de OpenF1 (desde 2023) son de acceso libre.

## ✨ Funcionalidades

- **`sesiones`** — Lista todas las sesiones (carreras, clasificaciones, etc.) de una temporada, con su `session_key`.
- **`pilotos`** — Lista los pilotos y escuderías que participaron en una sesión concreta.
- **`comparar-equipos`** — Compara el ritmo de vuelta (media, mediana, mejor vuelta) entre dos escuderías.
- **`comparar-pilotos`** — Compara el ritmo de vuelta entre dos pilotos concretos.
- **`piloto`** — Muestra el detalle vuelta a vuelta de un piloto, con resumen de mejor/media/peor vuelta.

Todos los comandos de comparación admiten `--csv ruta.csv` para exportar los datos completos.

## 📦 Requisitos

- Python 3.10 o superior
- Las librerías `pandas` y `requests`

## 🚀 Instalación

```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
pip install -r requirements.txt
```

## 🛠️ Uso

### 1. Encontrar el `session_key` de la carrera que te interesa
```bash
python f1_telemetry_analyzer.py sesiones --year 2024
```
Esto imprime una tabla con todas las carreras de 2024 y su `session_key` (necesario para el resto de comandos). Puedes filtrar por otro tipo de sesión con `--tipo "Qualifying"`.

### 2. Ver qué pilotos y escuderías corrieron esa sesión
```bash
python f1_telemetry_analyzer.py pilotos --session-key 9161
```

### 3. Comparar dos escuderías
```bash
python f1_telemetry_analyzer.py comparar-equipos --session-key 9161 --equipo1 Williams --equipo2 Ferrari
```
Salida: resumen de vueltas, media, mediana y mejor vuelta, tanto por escudería como por piloto individual.

### 4. Comparar dos pilotos
```bash
python f1_telemetry_analyzer.py comparar-pilotos --session-key 9161 --piloto1 Sainz --piloto2 Verstappen
```
Puedes usar el apellido (`Sainz`) o el acrónimo oficial de tres letras (`SAI`).

### 5. Analizar a un piloto en detalle, vuelta a vuelta
```bash
python f1_telemetry_analyzer.py piloto --session-key 9161 --piloto Sainz --csv vueltas_sainz.csv
```

## 🧱 Estructura del proyecto

```
analizador-telemetria-f1/
├── f1_telemetry_analyzer.py   # Script principal de la CLI
├── requirements.txt           # Dependencias (pandas, requests)
├── .gitignore
└── README.md
```

## 💡 Por qué existe esta herramienta

Demuestra capacidad para consumir APIs externas en tiempo real, manejar estructuras de datos complejas en memoria con Pandas y extraer métricas clave (ritmo de carrera, comparativas de rendimiento) sin necesidad de mantener una base de datos propia.

## ⚠️ Nota

OpenF1 es un proyecto no oficial y no está afiliado a Formula 1. Los nombres de `session_name` y `team_name` deben coincidir (aunque sea parcialmente) con los que devuelve la propia API para esa temporada concreta.
