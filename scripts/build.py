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

    candidates.append(BIND_CACHE)

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
    vswhere = shutil.which("vswhere")
    if not vswhere:
        raise BuildError(
            "vswhere.exe was not found on PATH. "
            "windows-latest should include vswhere by default."
        )

    try:
        result = subprocess.run(
            [
                vswhere,
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise BuildError(
            f"vswhere.exe failed to query Visual Studio installation: {exc.stderr.strip() or exc}"
        )

    install_path = result.stdout.strip()
    if not install_path:
        raise BuildError(
            "vswhere.exe did not return a Visual Studio installation path. "
            "Ensure the runner has Visual Studio Build Tools installed."
        )

    vcvars = Path(install_path) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    if not vcvars.exists():
        raise BuildError(
            f"vcvarsall.bat was not found at the path reported by vswhere: {vcvars}"
        )

    return vcvars


def build_windows(sdk_root: Path, bindings_root: Path) -> None:
    BUILD_TARGET = "x64"
    VCVARS_VER = "14.44"

    vcvarsall = find_vcvarsall()
    env = os.environ.copy()
    env["FBXSDK_ROOT"] = str(sdk_root)
    env["FBXSDK_COMPILER"] = env.get("FBXSDK_COMPILER", "vs2022")

    command = (
        f'call "{vcvarsall}" {BUILD_TARGET} -vcvars_ver={VCVARS_VER} '
        f'&& cd /d "{bindings_root}" '
        f"&& python -m sipbuild.tools.wheel --verbose --pep484-pyi"
    )

    subprocess.run(
        command,
        env=env,
        shell=True,
        check=True,
    )


def build_unix(sdk_root: Path, bindings_root: Path, arch: str | None = None) -> None:
    env = os.environ.copy()
    env["FBXSDK_ROOT"] = str(sdk_root)
    if platform.system() == "Linux":
        env["FBXSDK_COMPILER"] = env.get("FBXSDK_COMPILER", "gcc")
    elif platform.system() == "Darwin":
        env["FBXSDK_COMPILER"] = env.get("FBXSDK_COMPILER", "clang")
        env.pop("ARCHFLAGS", None)
        if arch:
            if arch == "universal2":
                env["ARCHFLAGS"] = "-arch arm64 -arch x86_64"
                env["MACOSX_DEPLOYMENT_TARGET"] = "10.15"
            else:
                env["ARCHFLAGS"] = f"-arch {arch}"
                if arch == "x86_64" and sys.version_info[:2] != (3, 7):
                    env["MACOSX_DEPLOYMENT_TARGET"] = "10.15"
                    env["_PYTHON_HOST_PLATFORM"] = "macosx-10.15-x86_64"
                elif arch == "arm64":
                    env["MACOSX_DEPLOYMENT_TARGET"] = "11.0"
                    env["_PYTHON_HOST_PLATFORM"] = "macosx-11.0-arm64"
                elif sys.version_info[:2] == (3, 7):
                    env["MACOSX_DEPLOYMENT_TARGET"] = "11.7"
                    env["_PYTHON_HOST_PLATFORM"] = "macosx-11.0-x86_64"

    cmd = [
        sys.executable,
        "-m",
        "sipbuild.tools.wheel",
        "--verbose",
        "--pep484-pyi",
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(
        cmd,
        cwd=bindings_root,
        env=env,
        check=True,
    )

    if platform.system() == "Darwin" and arch:
        wheels = sorted(bindings_root.glob("*.whl"))
        if not wheels:
            print("Warning: No wheels found to retag.")
            return

        built_wheel = max(wheels, key=os.path.getmtime)

        if arch == "arm64":
            target_platform = "macosx_11_0_arm64"
        elif arch == "x86_64":
            if sys.version_info[:2] == (3, 7):
                target_platform = "macosx_11_7_x86_64"
            else:
                target_platform = "macosx_10_15_x86_64"
        elif arch == "universal2":
            target_platform = "macosx_10_15_universal2"
        else:
            return

        retag_cmd = [
            sys.executable,
            "-m",
            "wheel",
            "tags",
            "--platform-tag", target_platform,
            "--remove",
            str(built_wheel),
        ]

        print(f"Retagging wheel: {' '.join(retag_cmd)}")
        subprocess.run(
            retag_cmd,
            cwd=bindings_root,
            check=True,
        )


def collect_wheel(bindings_root: Path) -> None:
    built_dist = bindings_root
    if not built_dist.exists():
        raise BuildError(
            f"Expected wheel output in {built_dist}, but the directory does not exist."
        )

    built_wheel = sorted(built_dist.glob("*.whl"))
    if not built_wheel:
        raise BuildError(f"No wheel files were found in {built_dist} after build.")

    print("Built wheel:")
    for wheel in built_wheel:
        print(wheel)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir()

    for wheel_path in built_wheel:
        destination = DIST_DIR / wheel_path.name
        shutil.copy2(wheel_path, destination)

    return


def main() -> int:
    sdk_root = find_sdk_root()
    bindings_root = find_bindings_root()

    print(f"FBX SDK root: {sdk_root}")
    print(f"FBX Python bindings root: {bindings_root}")

    if platform.system() == "Windows":
        build_windows(sdk_root, bindings_root)
    else:
        arch = os.environ.get("FBX_ARCH")
        build_unix(sdk_root, bindings_root, arch)

    collect_wheel(bindings_root)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
