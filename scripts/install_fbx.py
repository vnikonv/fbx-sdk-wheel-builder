from pathlib import Path
import platform
import subprocess
import urllib.request
import tarfile
import shutil

FBX_VERSION = "2020.3.9"

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
CACHE_DIR = ROOT_DIR / "cache"
SDK_CACHE = CACHE_DIR / "fbxsdk"
BIND_CACHE = CACHE_DIR / "fbxbind"

SDK_CACHE.mkdir(parents=True, exist_ok=True)
BIND_CACHE.mkdir(parents=True, exist_ok=True)

SYSTEM = platform.system()

if SYSTEM == "Windows":
    SDK_NAME = "fbxsdk.exe"
    PYTHON_NAME = "fbxpython.exe"
    SDK_URL = "https://damassets.autodesk.net/content/dam/autodesk/www/files/fbx202039_fbxsdk_vs2022_win.exe"
    PYTHON_URL = "https://damassets.autodesk.net/content/dam/autodesk/www/files/fbx202039_fbxpythonbindings_win.exe"

elif SYSTEM == "Linux":
    SDK_NAME = "fbxsdk.tar.gz"
    PYTHON_NAME = "fbxpython.tar.gz"
    SDK_URL = "https://damassets.autodesk.net/content/dam/autodesk/www/files/fbx202039_fbxsdk_gcc_linux.tar.gz"
    PYTHON_URL = "https://damassets.autodesk.net/content/dam/autodesk/www/files/fbx202039_fbxpythonbindings_linux.tar.gz"

elif SYSTEM == "Darwin":
    SDK_NAME = "fbxsdk.tar.gz"
    PYTHON_NAME = "fbxpython.tar.gz"
    SDK_URL = "https://damassets.autodesk.net/content/dam/autodesk/www/files/fbx202039_fbxsdk_clang_mac.pkg.tgz"
    PYTHON_URL = "https://damassets.autodesk.net/content/dam/autodesk/www/files/fbx202039_fbxpythonbindings_mac.pkg.tgz"

else:
    raise RuntimeError(f"Unsupported platform: {SYSTEM}")

SDK_INSTALLER = SDK_CACHE / SDK_NAME
PYTHON_INSTALLER = BIND_CACHE / PYTHON_NAME


def download(url: str, destination: Path) -> None:
    """Download a file if not already cached."""
    if destination.exists():
        print(f"Using cached {destination.name}")
        return

    print(f"Downloading {destination.name}")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"Successfully downloaded {destination.name}")
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")


def extract_tar_gz(archive_path: Path, extract_to: Path) -> None:
    """Extract .tar.gz file using tarfile."""
    print(f"Extracting {archive_path.name}")
    extract_to.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive_path, "r:*") as tar:
            tar.extractall(path=extract_to)
        print(f"Successfully extracted to {extract_to}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract {archive_path}: {e}")


def ensure_7z_available() -> None:
    """Ensure 7z is available on Windows for extracting FBX installers."""
    if shutil.which("7z") is None:
        raise RuntimeError(
            "7z is required on Windows to extract the FBX installer. "
            "Use a runner with 7-Zip installed or install 7-Zip into PATH."
        )
    print(f"Found 7z at: {shutil.which('7z')}")


def extract_exe_with_7z(archive_path: Path, extract_to: Path) -> None:
    """Extract a Windows self-extracting installer using 7z."""
    print(f"Extracting {archive_path.name} with 7z")
    extract_to.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["7z", "x", str(archive_path), f"-o{extract_to}", "-y"], check=True)
        print(f"Successfully extracted {archive_path.name} to {extract_to}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"7z failed to extract {archive_path}: {e}")


def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """Extract archive based on file type."""
    archive_path = Path(archive_path)
    
    if archive_path.name.endswith(".tar.gz") or archive_path.name.endswith(".tgz"):
        extract_tar_gz(archive_path, extract_to)
    elif archive_path.suffix == ".exe":
        extract_exe_with_7z(archive_path, extract_to)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")


def verify_sdk_structure(sdk_path: Path) -> bool:
    """Verify that the SDK has the expected structure."""
    required_dirs = ["include", "lib"]
    for dir_name in required_dirs:
        if not (sdk_path / dir_name).exists():
            print(f"ERROR: Missing SDK directory: {sdk_path / dir_name}")
            return False
    print("SDK structure verified")
    return True


def verify_bindings_structure(bindings_path: Path) -> bool:
    """Verify that the bindings have the expected structure."""
    if not (bindings_path / "sip").exists():
        print(f"ERROR: Missing bindings sip/ directory: {bindings_path / 'sip'}")
        return False
    print("Bindings structure verified")
    return True


def install_sdk_and_bindings():
    """Extract and verify SDK and bindings."""
    print(f"Installing FBX SDK {FBX_VERSION} on {SYSTEM}\n")

    if SYSTEM == "Windows":
        ensure_7z_available()
    
    print("--- Extracting FBX SDK ---")
    extract_archive(SDK_INSTALLER, SDK_CACHE)
    if not verify_sdk_structure(SDK_CACHE):
        raise RuntimeError("SDK verification failed")
    
    print("\n--- Extracting FBX Python Bindings ---")
    extract_archive(PYTHON_INSTALLER, BIND_CACHE)
    if not verify_bindings_structure(BIND_CACHE):
        raise RuntimeError("Bindings verification failed")

download(SDK_URL, SDK_INSTALLER)
download(PYTHON_URL, PYTHON_INSTALLER)

install_sdk_and_bindings()
