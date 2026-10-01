"""Film do landingu: prompty scen, generowanie przez fal.ai (opcjonalnie) i ciecie wideo na klatki."""
import colorsys
import json
import os
import subprocess
import time
import urllib.request
from collections import Counter

from . import instagram as IG
from .landing import oferta
from .rdzen import dziennik, folder, kierunek, wczytaj, zapisz

MODEL_OBRAZ = "fal-ai/nano-banana-pro"
MODEL_WIDEO = "minimax/h3-max/image-to-video"
AUTO_DOMYSLNE = "dark grey premium sports coupe"


def _nazwa_koloru(hexkolor):
    h = hexkolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.18:
        return "cool white" if v > 0.6 else "steel grey"
    for granica, nazwa in ((20, "red"), (45, "amber orange"), (70, "warm gold"), (160, "green"),
                           (200, "cyan"), (260, "blue"), (300, "violet"), (345, "magenta"), (361, "red")):
        if hh * 360 < granica:
            return nazwa


def prompty(slug):
    """Storyboard oferty z podstawionym autem i kolorem swiatla. Pierwszy kadr jest referencja dla pozostalych."""
    k = wczytaj(slug)
    kier = kierunek(k)
    o = oferta(k)
    auta = Counter(f["auto"] for f in IG.zdjecia(slug)["foto"] if f.get("auto"))
    auto = k["landing"].get("auto") or (auta.most_common(1)[0][0] if auta else AUTO_DOMYSLNE)
    akcent = _nazwa_koloru(kier["tokeny"]["accent"]) if kier else "white"
    out = []
    for i, s in enumerate(o["storyboard"]):
        out.append({"nr": i + 1, "plik": s["plik"] + ".png", "tytul": s["tytul"], "ruch": s["ruch"],
                    "prompt": s["prompt"].replace("{auto}", auto).replace("{akcent}", akcent),
                    "referencja": None if i == 0 else o["storyboard"][0]["plik"] + ".png"})
    return out


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def klatki(slug, fps=12, szer=1280, jakosc=72):
    """Tnie landing/wideo/*.mp4 na klatki webp. Pierwsza klatka kolejnych klipow jest duplikatem, wiec ja pomijamy."""
    baza = folder(slug) / "landing"
    klipy = sorted((baza / "wideo").glob("*.mp4"))
    if not klipy:
        raise ValueError("Brak plikow mp4 w landing/wideo/.")
    cel = baza / "strona" / "frames"
    if cel.exists():
        for p in cel.glob("f*.webp"):
            p.unlink()
    cel.mkdir(parents=True, exist_ok=True)
    tmp = baza / "_klatki"
    n = 0
    for i, klip in enumerate(klipy):
        if tmp.exists():
            for p in tmp.iterdir():
                p.unlink()
        tmp.mkdir(exist_ok=True)
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(klip), "-vf", "fps=%d,scale=%d:-2" % (fps, szer),
                        "-c:v", "libwebp", "-quality", str(jakosc), str(tmp / "k%04d.webp")], check=True)
        for j, p in enumerate(sorted(tmp.glob("k*.webp"))):
            if i > 0 and j == 0:
                continue
            n += 1
            p.replace(cel / ("f%04d.webp" % n))
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    k = wczytaj(slug)
    dziennik(k, "film: %d klatek z %d klipow" % (n, len(klipy)))
    zapisz(k)
    return n


# --- fal.ai przez REST (wymaga zmiennej FAL_KEY). Bez klucza Claude generuje te same kadry przez MCP fal-ai. ---

def _fal(metoda, url, dane=None):
    req = urllib.request.Request(url, method=metoda, data=json.dumps(dane).encode() if dane is not None else None,
                                 headers={"Authorization": "Key " + os.environ["FAL_KEY"], "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read().decode())


def _fal_uruchom(model, dane, limit_s=900):
    start = _fal("POST", "https://queue.fal.run/" + model, dane)
    koniec = time.time() + limit_s
    while time.time() < koniec:
        st = _fal("GET", start["status_url"])
        if st.get("status") == "COMPLETED":
            return _fal("GET", start["response_url"])
        if st.get("status") in ("FAILED", "ERROR"):
            raise RuntimeError("fal.ai: zadanie nieudane: %s" % st)
        time.sleep(4)
    raise RuntimeError("fal.ai: przekroczony czas oczekiwania (%s)" % model)


def _pobierz(url, cel):
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_bytes(urllib.request.urlopen(url, timeout=300).read())


def generuj(slug, wideo=True):
    """Kadry i przejscia wideo przez fal.ai. Koszt orientacyjny calego filmu: okolo 2 USD."""
    if not os.environ.get("FAL_KEY"):
        raise RuntimeError("Brak zmiennej FAL_KEY. Ustaw klucz fal.ai albo wygeneruj kadry przez Claude (MCP fal-ai) "
                           "i zapisz je w landing/kadry/, a klipy w landing/wideo/.")
    baza = folder(slug) / "landing"
    sceny = prompty(slug)
    adresy = []
    for s in sceny:
        if s["referencja"] is None:
            w = _fal_uruchom(MODEL_OBRAZ, {"prompt": s["prompt"], "aspect_ratio": "16:9", "resolution": "2K"})
        else:
            w = _fal_uruchom(MODEL_OBRAZ + "/edit", {"prompt": s["prompt"], "image_urls": [adresy[0]],
                                                     "aspect_ratio": "16:9", "resolution": "2K"})
        url = w["images"][0]["url"]
        adresy.append(url)
        _pobierz(url, baza / "kadry" / s["plik"])
    if wideo:
        for i in range(len(sceny) - 1):
            w = _fal_uruchom(MODEL_WIDEO, {"prompt": sceny[i + 1]["ruch"], "image_url": adresy[i],
                                           "end_image_url": adresy[i + 1], "duration": "5", "resolution": "1080P"})
            _pobierz(w["video"]["url"], baza / "wideo" / ("u%d.mp4" % (i + 1)))
        klatki(slug)
    return len(adresy)
