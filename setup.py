import os
import sys
import subprocess
import shutil
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py

REPO_URL = "https://github.com/ip7z/7zip.git"

class Build7ZipCommand(build_py):
    """Custom build command to clone, compile, and package 7-Zip."""
    
    def run(self):
        # Define paths
        root_dir = Path(__file__).parent.absolute()
        build_dir = root_dir / "build_7zip"
        pkg_dir = root_dir / "py7zip"
        bin_dir = pkg_dir / "bin"
        
        # Ensure package directories exist
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Clone the repository
        if not (build_dir / ".git").exists():
            print(f"[*] Cloning {REPO_URL} into {build_dir}...")
            subprocess.check_call(["git", "clone", REPO_URL, str(build_dir)])
        else:
            print("[*] Repository already cloned. Pulling latest changes...")
            subprocess.check_call(["git", "pull"], cwd=str(build_dir))
            
        # 2. Compile 7-Zip standalone (7zz)
        print("[*] Compiling 7-Zip source code...")
        # The Alone2 bundle creates the fully-featured standalone console tool
        make_dir = build_dir / "CPP" / "7zip" / "Bundles" / "Alone2"
        
        if sys.platform == "win32":
            # Windows compilation requires MSVC & nmake
            subprocess.check_call(["nmake", "NEW_COMPILER=1", "MY_STATIC_LINK=1"], cwd=str(make_dir))
            binary_name = "7zz.exe"
            compiled_bin = make_dir / "O" / binary_name
        else:
            # Linux/macOS compilation (requires make and g++)
            subprocess.check_call(["make", "-j4", "-f", "makefile.gcc"], cwd=str(make_dir))
            binary_name = "7zz"
            compiled_bin = make_dir / "_o" / binary_name
            
        if not compiled_bin.exists():
            raise FileNotFoundError(f"Compilation failed. Binary not found at {compiled_bin}")
            
        # 3. Copy compiled binary into the Python package structure
        print(f"[*] Copying compiled binary to {bin_dir}...")
        shutil.copy2(compiled_bin, bin_dir / binary_name)
        
        # 4. Generate the Python Wrapper (__init__.py) dynamically
        init_path = pkg_dir / "__init__.py"
        with open(init_path, "w", encoding="utf-8") as f:
            f.write(self.get_init_code())
            
        # Continue with the standard setuptools build process
        super().run()

    def get_init_code(self):
        return '''\
import os
import subprocess
from pathlib import Path

# Locate the bundled binary that was compiled during install
BIN_NAME = "7zz.exe" if os.name == "nt" else "7zz"
BIN_PATH = Path(__file__).parent / "bin" / BIN_NAME

class SevenZip:
    """Python interface for the locally compiled 7-Zip source."""
    
    def __init__(self, executable=BIN_PATH):
        self.executable = str(executable)
        if not os.path.exists(self.executable):
            raise FileNotFoundError(f"7-Zip binary not found at {self.executable}.")

    def extract(self, archive_path, output_dir):
        """Extract an archive to the specified output directory."""
        cmd = [self.executable, "x", str(archive_path), f"-o{output_dir}", "-y"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Extraction failed: {result.stderr or result.stdout}")
        return result.stdout

    def compress(self, archive_path, source_paths):
        """Compress files or directories into an archive."""
        if isinstance(source_paths, (str, Path)):
            source_paths = [source_paths]
        cmd = [self.executable, "a", str(archive_path)] + [str(p) for p in source_paths]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Compression failed: {result.stderr or result.stdout}")
        return result.stdout

# Expose global methods for rapid use
_default_instance = SevenZip()
extract = _default_instance.extract
compress = _default_instance.compress
'''

setup(
    name="py7zip",
    version="1.0.0",
    description="Python library bundled with natively compiled 7-Zip source",
    packages=["py7zip"],
    package_data={"py7zip": ["bin/*"]}, # Ensure the binary is included in the wheel
    cmdclass={
        "build_py": Build7ZipCommand,
    },
)