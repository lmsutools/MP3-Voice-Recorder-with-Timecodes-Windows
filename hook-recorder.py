# hook file for pyinstaller
#command:
# pyinstaller --onefile --additional-hooks-dir=. --add-data "lib/ffmpeg.exe;lib" voice-recorder.py

from PyInstaller.utils.hooks import collect_binaries

binaries = collect_binaries("recorder")
