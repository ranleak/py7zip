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
