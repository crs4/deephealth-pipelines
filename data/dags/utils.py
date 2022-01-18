import logging
import shutil
import subprocess
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
    shutil.copytree(
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


def check_gpus_available(gpus):
    logger.info("checking availibility for gpus %s", gpus)
    if gpus:
        cmd = f"--pid=host --gpus={gpus} ubuntu:20.04 bash -c nvidia-smi | grep ' C ' | wc -l"
        gpu_processes = docker_run(cmd)
        if int(gpu_processes):
            raise RuntimeError(f"processes already running on gpu(s) {gpus}")


def _run(command, shell=False):
    logger.info(
        "command %s", " ".join(command) if isinstance(command, list) else command
    )
    res = subprocess.run(command, capture_output=True, shell=shell)
    if res.returncode:
        logger.error(res.stderr)
        res.check_returncode()

    out = res.stdout.decode()
    logger.info("out %s", out)
    return out


def docker_run(command, network: str = None):
    docker_cmd = ["docker", "run", "--rm"]
    if network:
        docker_cmd.append("--network")
        docker_cmd.append(network)
    command = (
        docker_cmd + command
        if isinstance(command, list)
        else " ".join(docker_cmd) + f" {command}"
    )
    return _run(command, shell=isinstance(command, str))
