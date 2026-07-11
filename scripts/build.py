from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
CACHE_DIR = ROOT / "cache"
SDK_CACHE = CACHE_DIR / "fbxsdk"
BIND_CACHE = CACHE_DIR / "fbxbind"

VCVARS_PATHS = [
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"),
    Path(r"C:\Global\VS_2022\VC\Auxiliary\Build\vcvarsall.bat"),
]

BUILD_TARGET = "x64"
VCVARS_VER = "14.44"


class BuildError(RuntimeError):
    pass


def resolve_root(path: Path, required_markers: tuple[str, ...]) -> Path | None:
    if not path.exists() or not path.is_dir():
        return None

    if all((path / marker).exists() for marker in required_markers):
        return path

    return None


def find_sdk_root() -> Path:
    candidates = []

    candidates.extend([SDK_CACHE, Path("C:/fbxsdk")])

    for candidate in candidates:
        root = resolve_root(candidate, ("include", "lib"))
        if root:
            return root

    raise BuildError(
        "Unable to locate the extracted FBX SDK root. "
        "Set FBXSDK_ROOT or place the extracted SDK under cache/fbxsdk. "
        "The SDK root should contain include/ and lib/ directories."
    )


def find_bindings_root() -> Path:
    candidates = []

    candidates.extend([BIND_CACHE, Path("C:/fbxpython")])

    for candidate in candidates:
        root = resolve_root(candidate, ("sip",))
        if root:
            return root

    raise BuildError(
        "Unable to locate the extracted FBX Python bindings root. "
        "Set FBX_PYTHON_BINDINGS_ROOT or place the extracted bindings under cache/fbxbind. "
        "The bindings root should contain a sip/ directory."
    )


def find_vcvarsall() -> Path:
    explicit = os.environ.get("VCVARSALL_PATH")
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path
        raise BuildError(f"VCVARSALL_PATH is set but the file does not exist: {path}")

    candidates = []
    vsinstall = os.environ.get("VSINSTALLDIR")
    if vsinstall:
        candidates.append(Path(vsinstall) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat")
    candidates.extend(VCVARS_PATHS)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise BuildError(
        "Could not locate vcvarsall.bat. "
        "Ensure Visual Studio Build Tools are installed or set VCVARSALL_PATH."
    )


def locate_sip_wheel() -> str:
    sip_wheel = shutil.which("sip-wheel")
    if sip_wheel:
        return sip_wheel
    raise BuildError(
        "sip-wheel was not found on PATH. "
        "Install SIP in the current Python environment before running build.py."
    )


def run_command(cmd, cwd: Path | None = None, env: dict | None = None, shell: bool = False) -> None:
    print(f"Running: {cmd}")
    subprocess.run(cmd, cwd=cwd, env=env, shell=shell, check=True)


def build_windows(sdk_root: Path, bindings_root: Path) -> None:
    vcvarsall = find_vcvarsall()
    sip_wheel = locate_sip_wheel()
    env = os.environ.copy()
    env["FBXSDK_ROOT"] = str(sdk_root)
    env["FBXSDK_COMPILER"] = env.get("FBXSDK_COMPILER", "vs2022")

    command = (
        f'call "{vcvarsall}" {BUILD_TARGET} -vcvars_ver={VCVARS_VER} '
        f'&& cd /d "{bindings_root}" '
        f'&& "{sip_wheel}" --verbose --pep484-pyi'
    )

    run_command(command, env=env, shell=True)


def build_unix(sdk_root: Path, bindings_root: Path, arch: str | None = None) -> None:
    sip_wheel = locate_sip_wheel()
    env = os.environ.copy()
    env["FBXSDK_ROOT"] = str(sdk_root)
    if platform.system() == "Linux":
        env["FBXSDK_COMPILER"] = env.get("FBXSDK_COMPILER", "gcc")
    elif platform.system() == "Darwin":
        env["FBXSDK_COMPILER"] = env.get("FBXSDK_COMPILER", "clang")
        if arch:
            if arch == "universal2":
                env["ARCHFLAGS"] = "-arch arm64 -arch x86_64"
            else:
                env["ARCHFLAGS"] = f"-arch {arch}"

    run_command([sip_wheel, "--verbose", "--pep484-pyi"], cwd=bindings_root, env=env)


def collect_wheels(bindings_root: Path) -> list[Path]:
    built_dist = bindings_root
    if not built_dist.exists():
        raise BuildError(f"Expected wheel output in {built_dist}, but the directory does not exist.")

    built_wheels = sorted(built_dist.glob("*.whl"))
    if not built_wheels:
        raise BuildError(f"No wheel files were found in {built_dist} after build.")

    DIST_DIR.mkdir(exist_ok=True)
    out = []
    for wheel_path in built_wheels:
        destination = DIST_DIR / wheel_path.name
        shutil.copy2(wheel_path, destination)
        out.append(destination)

    return out


def main() -> int:
    sdk_root = find_sdk_root()
    bindings_root = find_bindings_root()

    print(f"FBX SDK root: {sdk_root}")
    print(f"FBX Python bindings root: {bindings_root}")

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if platform.system() == "Windows":
        build_windows(sdk_root, bindings_root)
    else:
        arch = os.environ.get("FBX_ARCH")
        build_unix(sdk_root, bindings_root, arch)

    wheels = collect_wheels(bindings_root)
    print("Built wheels:")
    for path in wheels:
        print(f"  {path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
