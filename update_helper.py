import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

def wait_for_process(pid):
    SYNCHRONIZE = 0x00100000
    INFINITE = 0xFFFFFFFF
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
    if handle:
        try:
            kernel32.WaitForSingleObject(handle, INFINITE)
        finally:
            kernel32.CloseHandle(handle)
    else:
        # Fallback for process handles unavailable due permissions.
        time.sleep(3)

def main():
    if len(sys.argv) < 4:
        return 2
    current_exe = Path(sys.argv[1]).resolve()
    new_exe = Path(sys.argv[2]).resolve()
    pid = int(sys.argv[3])
    wait_for_process(pid)
    if not new_exe.exists() or not current_exe.parent.exists():
        return 3
    staged = current_exe.with_name(current_exe.name + ".new")
    for attempt in range(12):
        try:
            shutil.copy2(new_exe, staged)
            os.replace(staged, current_exe)
            subprocess.Popen([str(current_exe)], cwd=str(current_exe.parent), close_fds=True)
            return 0
        except Exception:
            time.sleep(1)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0,
            "The update could not replace the application. Close any remaining RapPad processes and try again.",
            "The Ultimate RapPad Updater", 0x10)
    except Exception:
        pass
    return 4

if __name__ == "__main__":
    raise SystemExit(main())
