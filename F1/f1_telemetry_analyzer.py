#!/usr/bin/env python3
"""
Analizador de Telemetría de F1
--------------------------------
Script de terminal que consume la API pública y gratuita de OpenF1
(https://openf1.org) para comparar el ritmo de carrera y los tiempos
por vuelta entre escuderías (por ejemplo, Williams contra Ferrari) o
analizar el rendimiento de pilotos específicos (por ejemplo, Carlos Sainz).

Stack: Python 3 + Pandas + Requests
No necesita API key: los datos históricos (desde 2023) son de acceso libre.

Ejemplos de uso:
    python f1_telemetry_analyzer.py sesiones --year 2024
    python f1_telemetry_analyzer.py pilotos --session-key 9161
    python f1_telemetry_analyzer.py comparar-equipos --session-key 9161 --equipo1 Williams --equipo2 Ferrari
    python f1_telemetry_analyzer.py comparar-pilotos --session-key 9161 --piloto1 Sainz --piloto2 Verstappen
    python f1_telemetry_analyzer.py piloto --session-key 9161 --piloto Sainz --csv vueltas_sainz.csv
"""

import argparse
import sys

import pandas as pd
import requests

BASE_URL = "https://api.openf1.org/v1"
TIMEOUT = 15


def pedir_api(endpoint: str, params: dict) -> list:
    """Hace una petición GET a la API de OpenF1 y devuelve la respuesta como lista de dicts."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        respuesta = requests.get(url, params=params, timeout=TIMEOUT)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con la API ({url}): {e}")
        sys.exit(1)

    datos = respuesta.json()
    if not datos:
        print(f"⚠️  La API no devolvió datos para: {endpoint} con params {params}")
    return datos


def obtener_sesiones(year: int, tipo: str) -> pd.DataFrame:
    """Obtiene las sesiones (por ejemplo, todas las carreras) de una temporada."""
    datos = pedir_api("sessions", {"year": year, "session_name": tipo})
    if not datos:
        sys.exit(1)
    df = pd.DataFrame(datos)
    columnas = ["session_key", "country_name", "circuit_short_name", "session_name", "date_start"]
    columnas = [c for c in columnas if c in df.columns]
    return df[columnas].sort_values("date_start").reset_index(drop=True)


def obtener_pilotos(session_key: int) -> pd.DataFrame:
    """Obtiene la lista de pilotos y sus escuderías para una sesión concreta."""
    datos = pedir_api("drivers", {"session_key": session_key})
    if not datos:
        sys.exit(1)
    df = pd.DataFrame(datos)
    columnas = ["driver_number", "name_acronym", "full_name", "team_name"]
    columnas = [c for c in columnas if c in df.columns]
    return df[columnas].sort_values("driver_number").reset_index(drop=True)


def obtener_vueltas(session_key: int, driver_number: int | None = None) -> pd.DataFrame:
    """Obtiene todas las vueltas (lap_duration incluido) de una sesión, opcionalmente de un piloto."""
    params = {"session_key": session_key}
    if driver_number is not None:
        params["driver_number"] = driver_number

    datos = pedir_api("laps", params)
    if not datos:
        sys.exit(1)
    df = pd.DataFrame(datos)
    return df


def limpiar_vueltas(df: pd.DataFrame, incluir_invalidas: bool) -> pd.DataFrame:
    """Filtra vueltas sin tiempo registrado y, opcionalmente, las vueltas de entrada/salida de boxes."""
    df = df[df["lap_duration"].notna()].copy()
    if not incluir_invalidas and "is_pit_out_lap" in df.columns:
        df = df[df["is_pit_out_lap"] == False]  # noqa: E712
    return df


def resolver_piloto(df_pilotos: pd.DataFrame, consulta: str) -> pd.Series:
    """Busca un piloto por acrónimo exacto (ej. 'SAI') o por coincidencia parcial de nombre (ej. 'Sainz')."""
    consulta_lower = consulta.lower()

    coincidencia_acronimo = df_pilotos[df_pilotos["name_acronym"].str.lower() == consulta_lower]
    if not coincidencia_acronimo.empty:
        return coincidencia_acronimo.iloc[0]

    coincidencia_nombre = df_pilotos[df_pilotos["full_name"].str.lower().str.contains(consulta_lower)]
    if not coincidencia_nombre.empty:
        return coincidencia_nombre.iloc[0]

    print(f"❌ No se encontró ningún piloto que coincida con '{consulta}' en esta sesión.")
    sys.exit(1)


def resolver_equipo(df_pilotos: pd.DataFrame, consulta: str) -> str:
    """Devuelve el nombre exacto de la escudería (tal y como lo da la API) a partir de una coincidencia parcial."""
    consulta_lower = consulta.lower()
    coincidencias = df_pilotos[df_pilotos["team_name"].str.lower().str.contains(consulta_lower)]
    if coincidencias.empty:
        print(f"❌ No se encontró ninguna escudería que coincida con '{consulta}' en esta sesión.")
        sys.exit(1)
    return coincidencias.iloc[0]["team_name"]


def comando_sesiones(args):
    df = obtener_sesiones(args.year, args.tipo)
    print(f"\n📅 Sesiones de tipo '{args.tipo}' encontradas para {args.year}:\n")
    print(df.to_string(index=False))
    print("\n💡 Usa el valor de 'session_key' en los demás comandos.")


def comando_pilotos(args):
    df = obtener_pilotos(args.session_key)
    print(f"\n🏎️  Pilotos en la sesión {args.session_key}:\n")
    print(df.to_string(index=False))


def comando_comparar_equipos(args):
    df_pilotos = obtener_pilotos(args.session_key)
    equipo1 = resolver_equipo(df_pilotos, args.equipo1)
    equipo2 = resolver_equipo(df_pilotos, args.equipo2)

    pilotos_equipo1 = df_pilotos[df_pilotos["team_name"] == equipo1]
    pilotos_equipo2 = df_pilotos[df_pilotos["team_name"] == equipo2]
    numeros = pd.concat([pilotos_equipo1, pilotos_equipo2])["driver_number"].tolist()

    df_vueltas = obtener_vueltas(args.session_key)
    df_vueltas = df_vueltas[df_vueltas["driver_number"].isin(numeros)]
    df_vueltas = limpiar_vueltas(df_vueltas, args.incluir_invalidas)

    df_vueltas = df_vueltas.merge(
        df_pilotos[["driver_number", "full_name", "team_name"]], on="driver_number", how="left"
    )

    print(f"\n🏁 Comparativa de ritmo: {equipo1} vs {equipo2} (sesión {args.session_key})\n")

    resumen_equipo = (
        df_vueltas.groupby("team_name")["lap_duration"]
        .agg(vueltas="count", media="mean", mediana="median", mejor="min")
        .round(3)
    )
    print("--- Resumen por escudería ---")
    print(resumen_equipo.to_string())

    resumen_piloto = (
        df_vueltas.groupby(["team_name", "full_name"])["lap_duration"]
        .agg(vueltas="count", media="mean", mediana="median", mejor="min")
        .round(3)
    )
    print("\n--- Resumen por piloto ---")
    print(resumen_piloto.to_string())

    if args.csv:
        df_vueltas.to_csv(args.csv, index=False)
        print(f"\n💾 Datos completos exportados a: {args.csv}")


def comando_comparar_pilotos(args):
    df_pilotos = obtener_pilotos(args.session_key)
    piloto1 = resolver_piloto(df_pilotos, args.piloto1)
    piloto2 = resolver_piloto(df_pilotos, args.piloto2)

    numeros = [int(piloto1["driver_number"]), int(piloto2["driver_number"])]

    df_vueltas = obtener_vueltas(args.session_key)
    df_vueltas = df_vueltas[df_vueltas["driver_number"].isin(numeros)]
    df_vueltas = limpiar_vueltas(df_vueltas, args.incluir_invalidas)

    df_vueltas = df_vueltas.merge(
        df_pilotos[["driver_number", "full_name", "team_name"]], on="driver_number", how="left"
    )

    print(f"\n🏁 Comparativa de ritmo: {piloto1['full_name']} vs {piloto2['full_name']} (sesión {args.session_key})\n")

    resumen = (
        df_vueltas.groupby("full_name")["lap_duration"]
        .agg(vueltas="count", media="mean", mediana="median", mejor="min", peor="max")
        .round(3)
    )
    print(resumen.to_string())

    if args.csv:
        df_vueltas.to_csv(args.csv, index=False)
        print(f"\n💾 Datos completos exportados a: {args.csv}")


def comando_piloto(args):
    df_pilotos = obtener_pilotos(args.session_key)
    piloto = resolver_piloto(df_pilotos, args.piloto)
    numero = int(piloto["driver_number"])

    df_vueltas = obtener_vueltas(args.session_key, driver_number=numero)
    df_vueltas = limpiar_vueltas(df_vueltas, args.incluir_invalidas)
    df_vueltas = df_vueltas.sort_values("lap_number")

    print(f"\n🏎️  {piloto['full_name']} ({piloto['team_name']}) — sesión {args.session_key}\n")

    columnas = [c for c in ["lap_number", "lap_duration", "duration_sector_1", "duration_sector_2", "duration_sector_3"] if c in df_vueltas.columns]
    print(df_vueltas[columnas].to_string(index=False))

    print("\n--- Resumen ---")
    print(f"  Vueltas contabilizadas: {len(df_vueltas)}")
    print(f"  Mejor vuelta:  {df_vueltas['lap_duration'].min():.3f} s")
    print(f"  Vuelta media:  {df_vueltas['lap_duration'].mean():.3f} s")
    print(f"  Peor vuelta:   {df_vueltas['lap_duration'].max():.3f} s")

    if args.csv:
        df_vueltas.to_csv(args.csv, index=False)
        print(f"\n💾 Datos completos exportados a: {args.csv}")


def construir_parser():
    parser = argparse.ArgumentParser(
        prog="f1_telemetry_analyzer.py",
        description="Analizador de Telemetría de F1 (Python + Pandas + Requests, sobre la API de OpenF1)",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_sesiones = subparsers.add_parser("sesiones", help="Lista las sesiones (carreras, clasificación, etc.) de una temporada")
    p_sesiones.add_argument("--year", type=int, required=True, help="Año de la temporada, ej: 2024")
    p_sesiones.add_argument(
        "--tipo", default="Race", help="Tipo de sesión: Race, Qualifying, Practice 1, Sprint... (por defecto: Race)"
    )
    p_sesiones.set_defaults(func=comando_sesiones)

    p_pilotos = subparsers.add_parser("pilotos", help="Lista los pilotos y escuderías de una sesión concreta")
    p_pilotos.add_argument("--session-key", type=int, required=True, help="Identificador de sesión (obtenido con 'sesiones')")
    p_pilotos.set_defaults(func=comando_pilotos)

    p_comp_eq = subparsers.add_parser("comparar-equipos", help="Compara el ritmo de carrera entre dos escuderías")
    p_comp_eq.add_argument("--session-key", type=int, required=True)
    p_comp_eq.add_argument("--equipo1", required=True, help="Ej: Williams")
    p_comp_eq.add_argument("--equipo2", required=True, help="Ej: Ferrari")
    p_comp_eq.add_argument("--incluir-invalidas", action="store_true", help="Incluye vueltas de entrada/salida de boxes")
    p_comp_eq.add_argument("--csv", help="Ruta opcional para exportar los datos completos a CSV")
    p_comp_eq.set_defaults(func=comando_comparar_equipos)

    p_comp_pi = subparsers.add_parser("comparar-pilotos", help="Compara el ritmo de carrera entre dos pilotos")
    p_comp_pi.add_argument("--session-key", type=int, required=True)
    p_comp_pi.add_argument("--piloto1", required=True, help="Ej: Sainz o SAI")
    p_comp_pi.add_argument("--piloto2", required=True, help="Ej: Verstappen o VER")
    p_comp_pi.add_argument("--incluir-invalidas", action="store_true")
    p_comp_pi.add_argument("--csv", help="Ruta opcional para exportar los datos completos a CSV")
    p_comp_pi.set_defaults(func=comando_comparar_pilotos)

    p_piloto = subparsers.add_parser("piloto", help="Muestra el detalle vuelta a vuelta de un piloto concreto")
    p_piloto.add_argument("--session-key", type=int, required=True)
    p_piloto.add_argument("--piloto", required=True, help="Ej: Sainz o SAI")
    p_piloto.add_argument("--incluir-invalidas", action="store_true")
    p_piloto.add_argument("--csv", help="Ruta opcional para exportar las vueltas a CSV")
    p_piloto.set_defaults(func=comando_piloto)

    return parser


def main():
    parser = construir_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
