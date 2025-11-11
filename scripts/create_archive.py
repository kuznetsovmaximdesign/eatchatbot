"""Utility to build a nutrition_bot.zip archive from the source tree."""
from __future__ import annotations

import argparse
import os
import pathlib
import zipfile

DEFAULT_ARCHIVE = "nutrition_bot.zip"
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv"}
EXCLUDE_FILES = {"nutrition_bot.zip"}


def should_skip(path: pathlib.Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    return path.name in EXCLUDE_FILES


def build_archive(target: pathlib.Path, project_root: pathlib.Path) -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_root.rglob("*"):
            if file_path.is_dir():
                continue
            rel_path = file_path.relative_to(project_root)
            if should_skip(rel_path):
                continue
            zf.write(file_path, rel_path.as_posix())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=DEFAULT_ARCHIVE,
        help="Путь к результирующему архиву (по умолчанию nutrition_bot.zip)",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Корень проекта. Если не указан, берётся каталог, где лежит скрипт",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = (
        pathlib.Path(args.root).resolve()
        if args.root is not None
        else pathlib.Path(__file__).resolve().parent.parent
    )
    output_path = pathlib.Path(args.output).resolve()

    if not project_root.exists():
        raise SystemExit(f"Не найден каталог проекта: {project_root}")

    os.makedirs(output_path.parent, exist_ok=True)

    build_archive(output_path, project_root)
    print(f"Собран архив {output_path} из {project_root}")


if __name__ == "__main__":
    main()
