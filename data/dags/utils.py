import logging
import shutil
from pathlib import Path


logger = logging.getLogger("local-importer")

_copy_registry = {}
_move_registry = {}


def copy_slide(slide_path: str, dest: str):
    slide_path = Path(slide_path)
    dest = Path(dest)
    return _copy_registry.get(slide_path.suffix[1:], _copy_file)(
        slide_path,
        dest,
    )


def move_slide(slide_path: str, dest: str):
    slide_path = Path(slide_path)
    dest = Path(dest)
    _move_registry.get(slide_path.suffix[1:], _move_file)(
        slide_path,
        dest,
    )


def _copy_file(slide_path: Path, dest_dir: Path):
    dest_path = Path(dest_dir, slide_path.name)
    shutil.copy(
        slide_path.absolute().as_posix(),
        dest_path.absolute().as_posix(),
    )


def _copy_mrxs(slide_path: Path, dest_dir: Path):
    dir_dest_path = Path(dest_dir, slide_path.stem)
    shutil.copy(
        Path(slide_path.parent.absolute(), slide_path.stem).absolute().as_posix(),
        dir_dest_path.absolute().as_posix(),
    )
    _copy_file(slide_path, dest_dir)


def _move_file(slide_path: Path, dest_dir: Path):
    dest_path = Path(dest_dir, slide_path.name)
    shutil.move(
        slide_path.absolute().as_posix(),
        dest_path.absolute().as_posix(),
    )


def _move_mrxs(slide_path: Path, dest_dir: Path):
    dir_dest_path = Path(dest_dir, slide_path.stem)

    shutil.move(
        Path(slide_path.parent.absolute(), slide_path.stem).absolute().as_posix(),
        dir_dest_path.absolute().as_posix(),
    )
    _move_file(slide_path, dest_dir)


_copy_registry["mrxs"] = _copy_mrxs
_move_registry["mrxs"] = _move_mrxs
