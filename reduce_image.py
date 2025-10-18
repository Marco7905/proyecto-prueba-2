"""Herramientas para reducir imágenes individuales o lotes completos.

El módulo ofrece una utilidad de línea de comandos y funciones reutilizables
para otros scripts. Acepta como entrada una imagen suelta o una carpeta que
contenga más carpetas con imágenes en distintos formatos. Cada imagen se
redimensiona manteniendo su formato original y se sobreescribe en el mismo
lugar, dejando intactos los demás archivos. Cuando se indican dimensiones
concretas, estas se consideran límites máximos para evitar ampliar las
imágenes más allá de su tamaño original.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class ResizeOptions:
    """Opciones que controlan el redimensionado de las imágenes."""

    scale: float | None = None
    width: int | None = None
    height: int | None = None

    def validate(self) -> None:
        """Valida que las opciones proporcionadas tengan sentido."""

        if self.scale is None and self.width is None and self.height is None:
            raise ValueError("Debes indicar --scale, --width o --height para reducir la imagen.")

        if self.scale is not None and not (0 < self.scale <= 1):
            raise ValueError("--scale debe ser un número mayor que 0 y menor o igual a 1.")

        for field_name, value in ("width", self.width), ("height", self.height):
            if value is not None and value <= 0:
                raise ValueError(f"--{field_name} debe ser un número entero positivo.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reduce imágenes individuales o carpetas completas manteniendo el formato original."
        )
    )
    parser.add_argument(
        "target_path",
        type=Path,
        help=(
            "Ruta a la imagen o carpeta que se desea redimensionar."
            " Se recorren las subcarpetas de forma recursiva."
        ),
    )
    parser.add_argument(
        "--width",
        type=int,
        help=(
            "Ancho máximo en píxeles. Si sólo se indica este valor, se mantiene la proporción"
            " sin ampliar imágenes más grandes."
        ),
    )
    parser.add_argument(
        "--height",
        type=int,
        help=(
            "Altura máxima en píxeles. Si sólo se indica este valor, se mantiene la proporción"
            " sin ampliar imágenes más grandes."
        ),
    )
    parser.add_argument(
        "--scale",
        type=float,
        help="Factor de escala (0 < escala <= 1) para reducir proporcionalmente la imagen.",
    )

    args = parser.parse_args()

    if not args.target_path.exists():
        parser.error(f"No se encontró la ruta: {args.target_path}")

    try:
        ResizeOptions(scale=args.scale, width=args.width, height=args.height).validate()
    except ValueError as exc:  # pragma: no cover - validación del CLI
        parser.error(str(exc))

    return args


def _calculate_new_size(image: Image.Image, options: ResizeOptions) -> tuple[int, int]:
    original_width, original_height = image.size

    if options.scale is not None:
        width = max(1, min(original_width, int(round(original_width * options.scale))))
        height = max(1, min(original_height, int(round(original_height * options.scale))))
        return width, height

    requested_width = options.width
    requested_height = options.height

    if requested_width is not None:
        requested_width = max(1, min(requested_width, original_width))

    if requested_height is not None:
        requested_height = max(1, min(requested_height, original_height))

    if requested_width and requested_height:
        width_ratio = requested_width / original_width
        height_ratio = requested_height / original_height
        scale = min(width_ratio, height_ratio, 1)
        width = max(1, int(round(original_width * scale)))
        height = max(1, int(round(original_height * scale)))
        return width, height

    if requested_width:
        scale = requested_width / original_width
        height = max(1, min(original_height, int(round(original_height * scale))))
        return requested_width, height

    if requested_height:
        scale = requested_height / original_height
        width = max(1, min(original_width, int(round(original_width * scale))))
        return width, requested_height

    raise ValueError("No se proporcionaron parámetros válidos para redimensionar la imagen.")


def _iter_image_files(target_path: Path) -> Iterator[Path]:
    if target_path.is_file():
        yield target_path
        return

    for path in sorted(target_path.rglob("*")):
        if path.is_file():
            yield path


def _save_with_original_metadata(
    resized: Image.Image, original: Image.Image, destination: Path
) -> None:
    save_kwargs: dict[str, object] = {}

    exif = original.info.get("exif")
    if exif:
        save_kwargs["exif"] = exif

    icc_profile = original.info.get("icc_profile")
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile

    resized.save(destination, format=original.format, **save_kwargs)


def reduce_image_in_place(image_path: Path, options: ResizeOptions) -> bool:
    """Redimensiona una única imagen en su lugar.

    Devuelve ``True`` si la imagen fue modificada, ``False`` en caso contrario.
    """

    with Image.open(image_path) as image:
        new_size = _calculate_new_size(image, options)
        if new_size == image.size:
            return False

        resized = image.resize(new_size, Image.LANCZOS)
        _save_with_original_metadata(resized, image, image_path)
        return True


def discover_images(target_path: Path) -> list[Path]:
    """Devuelve las rutas de las imágenes encontradas de forma recursiva."""

    images: list[Path] = []
    for candidate in _iter_image_files(target_path):
        try:
            with Image.open(candidate):
                images.append(candidate)
        except (UnidentifiedImageError, OSError):
            continue
    return images


def reduce(target_path: Path, options: ResizeOptions) -> list[Path]:
    """Redimensiona imágenes en la ruta dada.

    Si ``target_path`` es una carpeta, se procesan todas las imágenes dentro de
    ella de forma recursiva. Se devuelve la lista de archivos modificados.
    """

    options.validate()
    processed: list[Path] = []
    for candidate in discover_images(target_path):
        if reduce_image_in_place(candidate, options):
            processed.append(candidate)
    return processed


def main() -> None:
    args = _parse_args()
    options = ResizeOptions(scale=args.scale, width=args.width, height=args.height)
    processed = reduce(args.target_path, options)

    if processed:
        print("Se redimensionaron los siguientes archivos:")
        for path in processed:
            print(f" - {path}")
    else:
        print("No se encontraron imágenes para redimensionar o ya tenían el tamaño indicado.")


if __name__ == "__main__":
    main()
