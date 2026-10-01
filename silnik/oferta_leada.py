"""Oferta osobista dla leada: strona z mapa stref, pakietami i wizualizacja ze zdjecia, otwierana linkiem po formularzu z landingu.

Uzycie:
  python -m silnik.oferta_leada buduj <slug>
  python -m silnik.oferta_leada serwer [port]     podglad + wizualizacja ze zdjecia (fal.ai) + zapis zdarzen
"""
import base64
import csv
import json
import mimetypes
import os
import re
import shutil
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from . import instagram as IG
from . import styl
from .landing import _jpg, _podstaw
from .rdzen import KLIENCI, KORZEN, NISZE, dziennik, folder, kierunek, scal, teraz, wczytaj, zapisz

KATALOG = "oferta-leada"
MODEL_EDYCJI = "fal-ai/nano-banana/edit"
LIMIT_NA_GODZINE = 20          # bezpiecznik kosztow: tyle wizualizacji na godzine obsluzy serwer
MAKS_OBRAZ = 6 * 1024 * 1024   # bajty po zdekodowaniu

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")


def konfiguracja(k):
    """Pakiet niszowy + nadpisania klienta (klient.json -> oferta_leada)."""
    p = NISZE / k["nisza"] / "oferta_leada.json"
    if not p.exists():
        raise ValueError("Pakiet niszy '%s' nie ma pliku oferta_leada.json." % k["nisza"])
    with open(p, encoding="utf-8") as f:
        baza = json.load(f)
    return scal(baza, k.get("oferta_leada") or {})


def sprawdz(c):
    """Bledy konfiguracji, ktore popsulyby cennik na stronie."""
    b = []
    strefy = {s["id"] for s in c["strefy"]}
    for p in c["pakiety"]:
        for s in p["strefy"]:
            if s not in strefy:
                b.append("pakiet '%s' ma nieznana strefe '%s'" % (p["id"], s))
        suma = sum(s["cena"] for s in c["strefy"] if s["id"] in p["strefy"])
        if p["cena"] > suma:
            b.append("pakiet '%s' jest drozszy (%s) niz jego strefy osobno (%s)" % (p["id"], p["cena"], suma))
    for pole in ("domyslny_pakiet", "kolejny_krok"):
        if c.get(pole) and c[pole] not in {p["id"] for p in c["pakiety"]}:
            b.append("%s wskazuje nieistniejacy pakiet '%s'" % (pole, c[pole]))
    return b


def klucz_fal():
    k = os.environ.get("FAL_KEY", "").strip()
    if k:
        return k
    p = KORZEN / ".fal_key"
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def buduj(slug):
    k = wczytaj(slug)
    kier = kierunek(k)
    if not kier:
        raise ValueError("Najpierw wybierz kierunek brandingu.")
    c = konfiguracja(k)
    bledy = sprawdz(c)
    if bledy:
        raise ValueError("Konfiguracja oferty: " + "; ".join(bledy))

    baza = folder(slug) / KATALOG
    strona = baza / "strona"
    (strona / "img").mkdir(parents=True, exist_ok=True)

    logo_kat = strona / "img" / "logo"
    if logo_kat.exists():
        shutil.rmtree(logo_kat)
    shutil.copytree(folder(slug) / "branding" / "final", logo_kat)

    # tlo naglowka: zdjecie realizacji studia, najpierw te z opisanym autem
    tlo = ""
    foto = sorted(IG.zdjecia(slug)["foto"], key=lambda f: (f.get("format") != "post", not f.get("auto")))
    for f in foto:
        src = folder(slug) / "zwiad" / (f.get("duzy") or f["plik"])
        if src.exists():
            _jpg(src, strona / "img" / "tlo.jpg", 1600)
            tlo = "img/tlo.jpg"
            break

    # przyklad wizualizacji: <klient>/oferta-leada/demo/przed.jpg + po-<efekt>.jpg
    demo = {}
    if (baza / "demo" / "przed.jpg").exists():
        (strona / "img" / "demo").mkdir(exist_ok=True)
        _jpg(baza / "demo" / "przed.jpg", strona / "img" / "demo" / "przed.jpg", 1600, 84)
        po = {}
        for e in c["wizualizacja"]["efekty"]:
            src = baza / "demo" / ("po-%s.jpg" % e["id"])
            if src.exists():
                _jpg(src, strona / "img" / "demo" / src.name, 1600, 84)
                po[e["id"]] = "img/demo/" + src.name
        if po:
            demo = {"przed": "img/demo/przed.jpg", "po": po, "auto": (c.get("demo") or {}).get("auto", "")}

    ctx = styl.kontekst(k, kier)
    d = k["dane"]
    zm = {"nazwa": d["nazwa"], "studio": d.get("nazwa_krotka") or d["nazwa"], "miasto": d.get("miasto") or "",
          "telefon": d.get("telefon") or ""}
    cfg = {
        "slug": slug, "studio": d["nazwa"], "studio_krotko": zm["studio"], "telefon": d.get("telefon", ""),
        "probka": ctx["probka"], "waznosc_dni": c["waznosc_dni"], "przyklad": c["przyklad"],
        "nadwozia": c["nadwozia"], "kolory": c["kolory"], "modele": c["modele"],
        "strefy": c["strefy"], "pakiety": c["pakiety"], "dodatki": c["dodatki"],
        "domyslny_pakiet": c["domyslny_pakiet"], "kolejny_krok": c.get("kolejny_krok", ""),
        "teksty": c["teksty"], "termin": c["termin"],
        "wizualizacja": {"efekty": [{"id": e["id"], "nazwa": e["nazwa"]} for e in c["wizualizacja"]["efekty"]],
                         "demo": demo, "stan": "/api/wizualizacja/stan", "endpoint": "/api/wizualizacja"},
        "zdarzenia": "/api/zdarzenie",
        "akcent": kier["tokeny"]["accent"], "tlo_auta": kier["tokeny"]["carbon"],
    }
    styl.renderuj(
        "oferta-leada/index.html", strona / "index.html", c=_podstaw(c, zm), tlo=tlo,
        logo_plik="logotyp-ciemny.svg" if ctx["kier"]["schemat"] == "light" else "logotyp-jasny.svg",
        cfg_json=json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"), **ctx)

    k = wczytaj(slug)
    # flaga dla szablonu landingu: po formularzu pokazuje link do oferty (szablony/oferta-leada/_hak.html)
    stan = k.setdefault("oferta_leada", {})
    stan["wlaczona"] = True
    stan["dla_ofert_wejsciowych"] = c.get("dla_ofert_wejsciowych") or []
    dziennik(k, "oferta leada: zbudowana (%d stref, %d pakietow)" % (len(c["strefy"]), len(c["pakiety"])))
    zapisz(k)
    return strona / "index.html"


def link(lead, baza="index.html"):
    """Adres oferty z danymi leada w kotwicy. Bez telefonu: adres moze trafic do historii przegladarki."""
    dane = {p: lead[p] for p in ("imie", "auto", "rocznik", "zakres", "plany", "termin", "kiedy") if lead.get(p)}
    b = base64.urlsafe_b64encode(json.dumps(dane, ensure_ascii=False).encode("utf-8")).decode().rstrip("=")
    return "%s#o=%s" % (baza, b)


# --- serwer podgladu: pliki klientow + wizualizacja ze zdjecia + zdarzenia ---

_wywolania = []
_blokada = threading.Lock()


def _wizualizuj(slug, efekt, obraz):
    klucz = klucz_fal()
    if not klucz:
        raise RuntimeError("Brak klucza fal.ai. Ustaw FAL_KEY albo zapisz klucz w pliku .fal_key w folderze generatora.")
    m = re.fullmatch(r"data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)", obraz or "")
    if not m:
        raise ValueError("Zdjecie musi byc plikiem JPG, PNG albo WEBP.")
    if len(m.group(2)) * 3 // 4 > MAKS_OBRAZ:
        raise ValueError("Zdjecie jest za duze. Maksymalnie 6 MB.")
    c = konfiguracja(wczytaj(slug))
    prompt = next((e["prompt"] for e in c["wizualizacja"]["efekty"] if e["id"] == efekt), None)
    if not prompt:
        raise ValueError("Nieznany efekt: %s" % efekt)
    with _blokada:
        teraz_s = time.time()
        _wywolania[:] = [t for t in _wywolania if teraz_s - t < 3600]
        if len(_wywolania) >= LIMIT_NA_GODZINE:
            raise RuntimeError("Limit wizualizacji na godzine zostal wykorzystany. Sprobuj pozniej.")
        _wywolania.append(teraz_s)
    req = urllib.request.Request(
        "https://fal.run/" + MODEL_EDYCJI, method="POST",
        data=json.dumps({"prompt": prompt, "image_urls": [obraz], "num_images": 1, "output_format": "jpeg"}).encode(),
        headers={"Authorization": "Key " + klucz, "Content-Type": "application/json"})
    try:
        w = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError("fal.ai odpowiedzial bledem %s: %s" % (e.code, e.read().decode(errors="replace")[:300]))
    if not w.get("images"):
        raise RuntimeError("fal.ai nie zwrocil obrazu.")
    return w["images"][0]["url"]


def _zdarzenie(dane):
    slug = re.sub(r"[^a-z0-9\-]", "", str(dane.get("slug", "")))[:60]
    if not slug or not (KLIENCI / slug / "klient.json").exists():
        raise ValueError("Nieznany klient.")
    czysc = lambda w, n: re.sub(r"[\r\n;]+", " ", str(w or ""))[:n]
    p = KLIENCI / slug / KATALOG / "zdarzenia.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    with _blokada, open(p, "a", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";").writerow([teraz(), czysc(dane.get("oferta"), 24), czysc(dane.get("co"), 40),
                                               czysc(dane.get("opis"), 200)])


class Obsluga(BaseHTTPRequestHandler):
    server_version = "OfertaLeada/1"

    def log_message(self, *a):
        pass

    def _wyslij(self, kod, tresc, typ="application/json; charset=utf-8"):
        if isinstance(tresc, (dict, list)):
            tresc = json.dumps(tresc, ensure_ascii=False).encode("utf-8")
        elif isinstance(tresc, str):
            tresc = tresc.encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(tresc)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(tresc)

    def do_GET(self):
        sciezka = unquote(urlparse(self.path).path)
        try:
            if sciezka == "/api/wizualizacja/stan":
                return self._wyslij(200, {"aktywna": bool(klucz_fal())})
            if sciezka in ("/", "/index.html"):
                linki = "".join('<li><a href="/k/%s/%s/strona/index.html">%s</a></li>' % (p.parent.parent.parent.name, KATALOG, p.parent.parent.parent.name)
                                for p in sorted(KLIENCI.glob("*/%s/strona/index.html" % KATALOG)))
                return self._wyslij(200, "<!doctype html><meta charset=utf-8><title>Oferty leadów</title><h1>Oferty leadów</h1><ul>%s</ul>" % linki,
                                    "text/html; charset=utf-8")
            if sciezka.startswith("/k/"):
                cel = (KLIENCI / sciezka[3:]).resolve()
                if KLIENCI.resolve() not in cel.parents:
                    return self._wyslij(403, {"blad": "Poza folderem klientow."})
                if cel.is_dir():
                    cel = cel / "index.html"
                if not cel.is_file() or cel.suffix in (".json", ".csv"):
                    return self._wyslij(404, {"blad": "Nie ma takiego pliku."})
                typ = mimetypes.guess_type(str(cel))[0] or "application/octet-stream"
                if typ.startswith("text/") or typ in ("application/javascript", "image/svg+xml"):
                    typ += "; charset=utf-8"
                return self._wyslij(200, cel.read_bytes(), typ)
            self._wyslij(404, {"blad": "Nie ma takiej strony."})
        except Exception as e:
            traceback.print_exc()
            self._wyslij(500, {"blad": str(e)})

    def do_POST(self):
        sciezka = unquote(urlparse(self.path).path)
        try:
            if self.headers.get("Origin") and urlparse(self.headers["Origin"]).hostname not in ("localhost", "127.0.0.1"):
                return self._wyslij(403, {"blad": "Zapis tylko z tego serwera."})
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAKS_OBRAZ * 2:
                return self._wyslij(413, {"blad": "Zdjecie jest za duze."})
            dane = json.loads(self.rfile.read(n).decode("utf-8") or "{}") if n else {}
            if sciezka == "/api/wizualizacja":
                return self._wyslij(200, {"url": _wizualizuj(str(dane.get("slug", "")), dane.get("efekt"), dane.get("obraz"))})
            if sciezka == "/api/zdarzenie":
                _zdarzenie(dane)
                return self._wyslij(200, {"ok": True})
            self._wyslij(404, {"blad": "Nie ma takiej akcji."})
        except (ValueError, KeyError, FileNotFoundError) as e:
            self._wyslij(400, {"blad": str(e)})
        except RuntimeError as e:
            self._wyslij(503, {"blad": str(e)})
        except Exception as e:
            traceback.print_exc()
            self._wyslij(500, {"blad": str(e)})


def serwer(port=8901):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Obsluga)
    print("Oferty leadow: http://localhost:%d  (wizualizacja ze zdjecia: %s)" % (port, "aktywna" if klucz_fal() else "brak klucza fal.ai, tryb przykladu"))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a and a[0] == "buduj" and len(a) > 1:
            print(buduj(a[1]))
        elif a and a[0] == "serwer":
            serwer(int(a[1]) if len(a) > 1 else 8901)
        else:
            print(__doc__)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print("BLAD: %s" % e, file=sys.stderr)
        sys.exit(1)
