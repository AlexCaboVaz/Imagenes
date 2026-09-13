#!/usr/bin/env python3
"""
Herramienta CLI de Procesamiento de Imágenes por Lotes
--------------------------------------------------------
Automatiza tareas repetitivas sobre carpetas llenas de fotografías:
  - Redimensionado masivo
  - Reducción básica de ruido (suavizado)
  - Renombrado secuencial de archivos
  - Pipeline completo (los tres pasos en uno)

Stack: Python 3 + Pillow
Uso rápido:
    python batch_processor.py resize  --input fotos --output salida --width 1920 --height 1080
    python batch_processor.py denoise --input fotos --output salida --strength 1
    python batch_processor.py rename  --input fotos --output salida --prefix vacaciones
    python batch_processor.py pipeline --input fotos --output salida --width 1920 --height 1080 --prefix boda
"""

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageFilter

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def obtener_imagenes(carpeta: Path) -> list[Path]:
    """Devuelve una lista ordenada con las rutas de todas las imágenes válidas de una carpeta."""
    if not carpeta.exists() or not carpeta.is_dir():
        print(f"❌ Error: la carpeta '{carpeta}' no existe o no es un directorio.")
        sys.exit(1)

    imagenes = sorted(
        [f for f in carpeta.iterdir() if f.suffix.lower() in EXTENSIONES_VALIDAS]
    )

    if not imagenes:
        print(f"⚠️  No se encontraron imágenes válidas en '{carpeta}'.")
        sys.exit(1)

    return imagenes


def preparar_carpeta_salida(carpeta_salida: Path) -> None:
    """Crea la carpeta de salida si no existe."""
    carpeta_salida.mkdir(parents=True, exist_ok=True)


def comando_resize(args):
    """Redimensiona en lote todas las imágenes de una carpeta."""
    entrada = Path(args.input)
    salida = Path(args.output)
    imagenes = obtener_imagenes(entrada)
    preparar_carpeta_salida(salida)

    ancho, alto = args.width, args.height
    total = len(imagenes)

    print(f"🖼️  Redimensionando {total} imagen(es) a {ancho}x{alto}px...\n")

    for i, ruta in enumerate(imagenes, start=1):
        try:
            with Image.open(ruta) as img:
                if args.keep_aspect:
                    img_copia = img.copy()
                    img_copia.thumbnail((ancho, alto), Image.LANCZOS)
                else:
                    img_copia = img.convert("RGB").resize((ancho, alto), Image.LANCZOS)

                destino = salida / ruta.name
                img_copia.save(destino)
                print(f"  [{i}/{total}] ✅ {ruta.name} -> {destino}")
        except Exception as e:
            print(f"  [{i}/{total}] ❌ Error con {ruta.name}: {e}")

    print(f"\n✔️  Proceso terminado. Imágenes guardadas en: {salida}")


def comando_denoise(args):
    """Aplica una reducción básica de ruido (suavizado) a todas las imágenes de una carpeta."""
    entrada = Path(args.input)
    salida = Path(args.output)
    imagenes = obtener_imagenes(entrada)
    preparar_carpeta_salida(salida)

    total = len(imagenes)
    intensidad = args.strength

    print(f"🧹 Reduciendo ruido de {total} imagen(es) (intensidad={intensidad})...\n")

    for i, ruta in enumerate(imagenes, start=1):
        try:
            with Image.open(ruta) as img:
                img_filtrada = img
                for _ in range(intensidad):
                    img_filtrada = img_filtrada.filter(ImageFilter.MedianFilter(size=3))

                destino = salida / ruta.name
                img_filtrada.save(destino)
                print(f"  [{i}/{total}] ✅ {ruta.name} -> {destino}")
        except Exception as e:
            print(f"  [{i}/{total}] ❌ Error con {ruta.name}: {e}")

    print(f"\n✔️  Proceso terminado. Imágenes guardadas en: {salida}")


def comando_rename(args):
    """Renombra secuencialmente todas las imágenes de una carpeta (copiándolas a la carpeta de salida)."""
    entrada = Path(args.input)
    salida = Path(args.output)
    imagenes = obtener_imagenes(entrada)
    preparar_carpeta_salida(salida)

    total = len(imagenes)
    prefijo = args.prefix
    inicio = args.start
    digitos = args.digits

    print(f"🔤 Renombrando {total} imagen(es) con el prefijo '{prefijo}'...\n")

    for i, ruta in enumerate(imagenes):
        numero = str(inicio + i).zfill(digitos)
        nuevo_nombre = f"{prefijo}_{numero}{ruta.suffix.lower()}"
        destino = salida / nuevo_nombre

        try:
            if entrada.resolve() == salida.resolve():
                ruta.rename(destino)
            else:
                shutil.copy2(ruta, destino)
            print(f"  [{i + 1}/{total}] ✅ {ruta.name} -> {nuevo_nombre}")
        except Exception as e:
            print(f"  [{i + 1}/{total}] ❌ Error con {ruta.name}: {e}")

    print(f"\n✔️  Proceso terminado. Imágenes guardadas en: {salida}")


def comando_pipeline(args):
    """Ejecuta resize -> denoise -> rename en un solo comando, usando carpetas temporales intermedias."""
    entrada = Path(args.input)
    salida_final = Path(args.output)
    temp1 = salida_final / "_temp_resize"
    temp2 = salida_final / "_temp_denoise"

    print("🚀 Ejecutando pipeline completo: resize -> denoise -> rename\n")

    class Args1:
        input = str(entrada)
        output = str(temp1)
        width = args.width
        height = args.height
        keep_aspect = args.keep_aspect

    comando_resize(Args1)

    class Args2:
        input = str(temp1)
        output = str(temp2)
        strength = args.strength

    comando_denoise(Args2)

    class Args3:
        input = str(temp2)
        output = str(salida_final)
        prefix = args.prefix
        start = args.start
        digits = args.digits

    comando_rename(Args3)

    shutil.rmtree(temp1, ignore_errors=True)
    shutil.rmtree(temp2, ignore_errors=True)

    print(f"\n🎉 Pipeline completo. Resultado final en: {salida_final}")


def construir_parser():
    parser = argparse.ArgumentParser(
        prog="batch_processor.py",
        description="Herramienta CLI de Procesamiento de Imágenes por Lotes (Python + Pillow)",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_resize = subparsers.add_parser("resize", help="Redimensiona en lote todas las imágenes de una carpeta")
    p_resize.add_argument("--input", required=True, help="Carpeta con las imágenes originales")
    p_resize.add_argument("--output", required=True, help="Carpeta donde se guardarán las imágenes procesadas")
    p_resize.add_argument("--width", type=int, required=True, help="Ancho deseado en píxeles")
    p_resize.add_argument("--height", type=int, required=True, help="Alto deseado en píxeles")
    p_resize.add_argument(
        "--keep-aspect",
        action="store_true",
        help="Mantiene la proporción original (no deforma la imagen) en vez de forzar el tamaño exacto",
    )
    p_resize.set_defaults(func=comando_resize)

    p_denoise = subparsers.add_parser(
        "denoise", help="Aplica una reducción básica de ruido a todas las imágenes de una carpeta"
    )
    p_denoise.add_argument("--input", required=True, help="Carpeta con las imágenes originales")
    p_denoise.add_argument("--output", required=True, help="Carpeta donde se guardarán las imágenes procesadas")
    p_denoise.add_argument(
        "--strength", type=int, default=1, help="Número de pasadas del filtro (1-3 recomendado, por defecto 1)"
    )
    p_denoise.set_defaults(func=comando_denoise)

    p_rename = subparsers.add_parser("rename", help="Renombra secuencialmente todas las imágenes de una carpeta")
    p_rename.add_argument("--input", required=True, help="Carpeta con las imágenes originales")
    p_rename.add_argument("--output", required=True, help="Carpeta donde se guardarán las imágenes renombradas")
    p_rename.add_argument("--prefix", default="foto", help="Prefijo del nuevo nombre (por defecto: 'foto')")
    p_rename.add_argument("--start", type=int, default=1, help="Número inicial de la secuencia (por defecto: 1)")
    p_rename.add_argument(
        "--digits", type=int, default=4, help="Cantidad de dígitos del número (por defecto: 4, ej: 0001)"
    )
    p_rename.set_defaults(func=comando_rename)

    p_pipeline = subparsers.add_parser("pipeline", help="Ejecuta resize + denoise + rename en un solo comando")
    p_pipeline.add_argument("--input", required=True)
    p_pipeline.add_argument("--output", required=True)
    p_pipeline.add_argument("--width", type=int, required=True)
    p_pipeline.add_argument("--height", type=int, required=True)
    p_pipeline.add_argument("--keep-aspect", action="store_true")
    p_pipeline.add_argument("--strength", type=int, default=1)
    p_pipeline.add_argument("--prefix", default="foto")
    p_pipeline.add_argument("--start", type=int, default=1)
    p_pipeline.add_argument("--digits", type=int, default=4)
    p_pipeline.set_defaults(func=comando_pipeline)

    return parser


def main():
    parser = construir_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
