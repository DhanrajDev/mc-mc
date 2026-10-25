"""Prepare this checkout's environment before starting the launcher."""
from pathlib import Path
import hashlib
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ENV = BASE / '.venv'
PYTHON = ENV / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=BASE, check=True)


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError('Install Python 3.10 or newer, including Tcl/Tk.')
    requirements = BASE / 'requirements.txt'
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = ENV / '.launcher-requirements'
    probe = [str(PYTHON), '-c', 'import sys; assert sys.version_info >= (3,10)']
    usable = PYTHON.exists() and subprocess.run(probe, capture_output=True).returncode == 0
    if not usable:
        print('Creating the local Python environment…', flush=True)
        run(sys.executable, '-m', 'venv', ENV)
    check = subprocess.run([str(PYTHON), '-c', 'import minecraft_launcher_lib, tkinter'], capture_output=True)
    installed = marker.exists() and marker.read_text().strip() == fingerprint
    if not installed or check.returncode:
        print('Installing launcher dependencies (internet required)…', flush=True)
        run(PYTHON, '-m', 'pip', 'install', '-r', requirements)
        run(PYTHON, '-c', 'import minecraft_launcher_lib, tkinter')
        marker.write_text(fingerprint, encoding='utf-8')
    if '--setup-only' in sys.argv[1:]:
        print('Setup complete. Run Launch.bat to play.', flush=True)
    else:
        run(PYTHON, BASE / 'launcher.py')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'Setup failed: {error}', file=sys.stderr)
        print('Check your connection and Python installation (include Tcl/Tk).', file=sys.stderr)
        sys.exit(1)
