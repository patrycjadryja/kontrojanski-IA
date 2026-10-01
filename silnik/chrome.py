"""Zrzuty z bezglowego Chrome. Zawsze po kolei: rownolegle instancje daja puste obrazy."""
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

KANDYDACI = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
_kolejka = threading.Lock()


def znajdz():
    for k in KANDYDACI:
        if os.path.exists(k):
            return k
    for n in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    raise RuntimeError("Nie znaleziono Chrome. Zainstaluj Google Chrome.")


def zrzut(html, png, szer, wys, przezroczyste=False, budzet_ms=5000):
    """Zapisuje zrzut pliku HTML do PNG w dokladnym rozmiarze szer x wys."""
    adres = html if str(html).startswith("http") else Path(html).resolve().as_uri()
    png = Path(png).resolve()
    png.parent.mkdir(parents=True, exist_ok=True)
    if png.exists():
        png.unlink()
    profil = tempfile.mkdtemp(prefix="gen-chrome-")
    with _kolejka:
        cmd = [
            znajdz(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--force-device-scale-factor=1",
            "--user-data-dir=" + profil,
            "--window-size=%d,%d" % (szer, max(wys, 500)),  # ponizej 500 px Chrome przycina widok
            "--virtual-time-budget=%d" % budzet_ms,
            "--screenshot=" + str(png),
        ]
        if przezroczyste:
            cmd.append("--default-background-color=00000000")
        cmd.append(adres)
        # Chrome potrafi zapisac zrzut i nie zakonczyc procesu, dlatego czekamy na plik, nie na proces.
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        koniec = time.time() + 120
        rozmiar = -1
        while time.time() < koniec:
            if p.poll() is not None:
                break
            if png.exists():
                r = png.stat().st_size
                if r > 0 and r == rozmiar:
                    break
                rozmiar = r
            time.sleep(0.4)
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    shutil.rmtree(profil, ignore_errors=True)  # Chrome bywa jeszcze w trakcie zapisu profilu
    if not png.exists():
        raise RuntimeError("Chrome nie zapisal zrzutu: %s" % png.name)
    if wys < 500:
        from PIL import Image
        im = Image.open(png)
        im.crop((0, 0, szer, wys)).save(png)
    return png
