"""Diferencias entre macOS y Windows: evitar la suspension, avisos y herramientas externas."""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


@contextlib.contextmanager
def keep_awake():
    """Mantiene el ordenador despierto mientras dure el bloque 'with'."""
    if sys.platform == "darwin":
        proc = None
        with contextlib.suppress(OSError):
            proc = subprocess.Popen(["caffeinate", "-i", "-s", "-w", str(os.getpid())])
        try:
            yield
        finally:
            if proc:
                proc.terminate()
    elif sys.platform == "win32":
        import ctypes

        es_continuous, es_system_required = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | es_system_required)
        try:
            yield
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(es_continuous)
    else:
        yield


def notify_desktop(title: str, message: str) -> None:
    """Aviso del sistema operativo. Nunca lanza excepciones."""
    try:
        if sys.platform == "darwin":
            script = f'display notification "{_q(message)}" with title "{_q(title)}"'
            subprocess.run(["osascript", "-e", script], check=False, timeout=5)
        elif sys.platform == "win32":
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$n=New-Object System.Windows.Forms.NotifyIcon;"
                "$n.Icon=[System.Drawing.SystemIcons]::Information;$n.Visible=$true;"
                f"$n.ShowBalloonTip(8000,'{_ps(title)}','{_ps(message)}','Info');Start-Sleep 9;$n.Dispose()"
            )
            subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps])
        elif shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message], check=False, timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass


def notify_ntfy(topic: str, title: str, message: str, server: str = "https://ntfy.sh") -> bool:
    """Aviso al movil con ntfy (app gratuita). Devuelve False si no se pudo enviar."""
    if not topic:
        return False
    request = urllib.request.Request(
        f"{server.rstrip('/')}/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title.encode("ascii", "replace").decode()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            return True
    except OSError:
        return False


def _q(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _ps(text: str) -> str:
    return text.replace("'", "''")


def find_avrdude() -> tuple[Path, Path | None] | None:
    """Busca avrdude (PATH o la instalacion de PlatformIO). Devuelve (ejecutable, avrdude.conf)."""
    exe = shutil.which("avrdude")
    if exe:
        return Path(exe), None
    tool = Path.home() / ".platformio" / "packages" / "tool-avrdude"
    name = "avrdude.exe" if sys.platform == "win32" else "avrdude"
    for candidate in (tool / name, tool / "bin" / name):
        if candidate.exists():
            conf = next((p for p in (tool / "avrdude.conf", tool / "etc" / "avrdude.conf") if p.exists()), None)
            return candidate, conf
    return None


def upload_firmware(port: str, hex_path: Path, baud: int = 115200) -> subprocess.CompletedProcess:
    """Carga firmware.hex en el Arduino UNO con avrdude."""
    found = find_avrdude()
    if not found:
        raise FileNotFoundError("No se encontro avrdude. Instala PlatformIO (pip install platformio) o avrdude.")
    exe, conf = found
    cmd = [str(exe)]
    if conf:
        cmd += ["-C", str(conf)]
    cmd += ["-p", "atmega328p", "-c", "arduino", "-P", port, "-b", str(baud), "-D",
            "-U", f"flash:w:{hex_path}:i"]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)
