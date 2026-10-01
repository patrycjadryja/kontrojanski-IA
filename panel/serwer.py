"""Panel Generatora Agencji: lokalny serwer do przegladania klientow i podejmowania decyzji.
Kroki powtarzalne (pliki logo, grafiki, landing) panel uruchamia sam. Kroki wymagajace oceny robi Claude Code."""
import json
import mimetypes
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

KORZEN = Path(__file__).resolve().parent.parent
if str(KORZEN) not in sys.path:
    sys.path.insert(0, str(KORZEN))

import subprocess  # noqa: E402
import time  # noqa: E402

from silnik import instagram, landing, rdzen  # noqa: E402
from silnik.__main__ import kolejka  # noqa: E402
from panel import agent  # noqa: E402
from silnik import hosting  # noqa: E402

_aktywnosc = {}  # slug -> (czas, dane) - odczyt z serwera najwyzej raz na minute

PYTHON = str(KORZEN / ".venv" / "bin" / "python")
ROZSZ_ZDJEC = (".jpg", ".jpeg", ".png", ".webp")

PANEL = Path(__file__).resolve().parent
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")

_praca = {}  # slug -> watek, jeden ciag zadan na klienta


def w_tle(slug, etap, *kroki):
    """Uruchamia kroki silnika po kolei, kazdy jako osobny proces. Blad zapisuje w etapie, zeby panel go pokazal."""
    if slug in _praca and _praca[slug].is_alive():
        raise ValueError("Silnik jeszcze pracuje nad tym klientem. Poczekaj na koniec.")

    def rob():
        for nazwa, polecenie in kroki:
            start = time.time()
            r = subprocess.run([PYTHON, "-m", "silnik"] + polecenie, cwd=str(KORZEN), capture_output=True, text=True)
            try:
                k = rdzen.wczytaj(slug)
                ko = k.setdefault("koszty", {"claude_usd": 0, "claude_min": 0, "silnik_min": 0})
                ko["silnik_min"] = round(ko.get("silnik_min", 0) + (time.time() - start) / 60, 1)
                rdzen.zapisz(k)
            except Exception:
                pass
            if r.returncode != 0:
                blad = (r.stderr.strip().splitlines() or ["nieznany blad"])[-1]
                k = rdzen.wczytaj(slug)
                rdzen.ustaw_etap(k, nazwa, "blad", blad[:400])
                rdzen.zapisz(k)
                return

    t = threading.Thread(target=rob, daemon=True)
    _praca[slug] = t
    t.start()


def po_landingu(slug):
    """Po landingu od razu powstaja dwie warstwy ofert, a gdy wlaczona, takze oferta dla leada."""
    kroki = [("landing", ["landing", slug])]
    try:
        if rdzen.wczytaj(slug).get("oferta_leada", {}).get("wlaczona"):
            kroki.append(("landing", ["oferta-leada", slug]))
    except FileNotFoundError:
        pass
    return kroki + [("pokaz", ["pokaz", slug])]


def skrot(k):
    e = k.get("etapy", {})
    d = k.get("dane", {})
    decyzja = next((x for x in rdzen.ETAPY if e.get(x) == "decyzja"), "")
    return {
        "slug": k["slug"], "nazwa": d.get("nazwa") or k["slug"], "miasto": d.get("miasto", ""),
        "tryb": k.get("tryb", "probka"), "etapy": e, "decyzja": decyzja,
        "blad": next((x for x in rdzen.ETAPY if e.get(x) == "blad"), ""),
        "pracuje": k["slug"] in _praca and _praca[k["slug"]].is_alive(),
        "agent": agent.stan()["slug"] == k["slug"],
        "zmieniono": k.get("zmieniono", ""),
        "awatar": awatar(k["slug"]),
    }


def awatar(slug):
    f = rdzen.folder(slug)
    for p in ("branding/final/awatar-instagram.svg", "zwiad/zdjecia/awatar.jpg", "zwiad/zdjecia/h0.jpg"):
        if (f / p).exists():
            return "/k/%s/%s" % (slug, p)
    return ""


def szczegoly(slug):
    k = rdzen.wczytaj(slug)
    f = rdzen.folder(slug)
    jest = lambda p: (f / p).exists()
    grafiki = len(list((f / "instagram" / "paczka").rglob("*.png"))) if jest("instagram/paczka") else 0
    return {
        "klient": k, "skrot": skrot(k),
        "kandydaci": landing.kandydaci(k) if k.get("uslugi") or k["etapy"].get("instagram") == "gotowe" else [],
        "braki": landing.braki_wdrozenia(k),
        "pliki": {
            "kierunki": jest("branding/kierunki.html"), "ksiega": jest("branding/ksiega.html"),
            "propozycja": jest("instagram/propozycja.html"), "zip": jest("instagram/%s-instagram.zip" % slug),
            "podglad_ig": jest("instagram/paczka/01-podglad-przed-i-po/feed-przed-i-po.png"),
            "landing": jest("landing/strona/index.html"), "grafiki": grafiki,
            "pokaz": jest("pokaz/index.html"), "oferta": jest("pokaz/oferta/index.html"),
            "wizualizacje": len(list((f / "branding" / "wizualizacje").glob("*.jpg"))) if jest("branding/wizualizacje") else 0,
            "wideo_powitalne": jest("pokaz/wideo/powitanie.mp4"),
            "oferta_leada": jest("oferta-leada/strona/index.html"),
            "oferta_leada_dostepna": k["landing"].get("oferta_id") in ((rdzen.nisza(k["nisza"]).get("oferta_leada_dla") or []) + _ol_oferty(k)),
            "zdjecia": len(instagram.zdjecia(slug)["foto"]),
        },
        "folder": str(f),
        "agent": agent.zdarzenia(slug),
        "agencja": agencja_bez_sekretow(),
        "publikacja": dict(k.get("publikacja") or {}, aktualna=aktualna_publikacja(k)),
        "aktywnosc": aktywnosc(slug) if k.get("publikacja") else None,
        "koszty": koszty(k, f),
        "braki_pokazu": braki_pokazu(k),
        "braki_oferty": braki_oferty(k),
        "pakiety": [{"id": p["id"], "nazwa": p["nazwa"], "cena": p["cena"], "wdrozenie": p["wdrozenie"]}
                    for p in rdzen.nisza(k["nisza"]).get("oferta", {}).get("pakiety", [])],
    }


def agencja_bez_sekretow():
    a = rdzen.agencja()
    tg = dict(a.get("telegram") or {})
    if tg.get("token"):
        tg["token"] = "zapisany"
    h = dict(a.get("hosting") or {})
    h.pop("sekret", None)
    return dict(a, telegram=tg, hosting=h, hosting_gotowy=bool((a.get("hosting") or {}).get("sekret")))


def aktualna_publikacja(k):
    p = rdzen.folder(k["slug"]) / "pokaz" / "index.html"
    return bool(k.get("publikacja")) and p.exists() and int(p.stat().st_mtime) <= int(k["publikacja"].get("wersja") or 0)


def aktywnosc(slug):
    """Aktywnosc prospekta z serwera, z pamiecia podreczna na minute."""
    t, dane = _aktywnosc.get(slug, (0, None))
    if time.time() - t < 60:
        return dane
    try:
        dane = hosting.zdarzenia(slug)
    except Exception as e:
        dane = {"blad": str(e)[:200]}
    _aktywnosc[slug] = (time.time(), dane)
    return dane


def koszty(k, f):
    """Koszt i czas jednego klienta. fal.ai to szacunek na podstawie plikow, ktore powstaly."""
    ko = dict(k.get("koszty") or {})
    fal = 0.0
    if (f / "landing" / "kadry").exists() and any((f / "landing" / "kadry").glob("*")):
        fal += 0.9
    if (f / "landing" / "wideo").exists() and any((f / "landing" / "wideo").glob("*.mp4")):
        fal += 0.95
    if (f / "branding" / "wizualizacje").exists() and any((f / "branding" / "wizualizacje").glob("*")):
        fal += 1.05
    ko["fal_usd"] = round(fal, 2)
    ko["razem_usd"] = round(ko.get("claude_usd", 0) + fal, 2)
    ko["razem_min"] = round(ko.get("claude_min", 0) + ko.get("silnik_min", 0), 1)
    return ko


def _ol_oferty(k):
    """Oferty wejsciowe, dla ktorych pakiet niszy ma konfiguracje oferty leada."""
    p = rdzen.NISZE / k["nisza"] / "oferta_leada.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("dla_ofert_wejsciowych") or []
    except ValueError:
        return []


def braki_pokazu(k):
    a, b = rdzen.agencja(), []
    if not a["nadawca"]:
        b.append("brak podpisu nadawcy (ustawienia agencji)")
    if not a["kalendarz"] and not a["wiadomosc"]:
        b.append("brak linku do kalendarza rozmów albo do wiadomości (ustawienia agencji)")
    if not (a.get("hosting") or {}).get("sekret"):
        b.append("serwer do publikacji nie jest podłączony (ustawienia agencji albo 'podłącz serwer' w Claude)")
    elif k.get("publikacja") and not aktualna_publikacja(k):
        b.append("na serwerze jest starsza wersja pokazu, wyślij ponownie")
    if k["landing"].get("film", {}).get("tryb") == "zdjecia":
        b.append("landing bez filmu AI, w tle scen są zdjęcia klienta")
    if not (rdzen.folder(k["slug"]) / "branding" / "wizualizacje").exists():
        b.append("brak wizualizacji znaku (opcjonalne, około 1 USD)")
    return b


def braki_oferty(k):
    o, b = k.get("oferta", {}), []
    if not o.get("cele"):
        b.append("cele klienta są przykładowe, wpisz jego słowa po rozmowie")
    if not o.get("rozmowa"):
        b.append("brak daty rozmowy")
    if not o.get("wazna_do"):
        b.append("brak terminu ważności oferty")
    b.append("pakiety i ceny agencji pochodzą z pakietu niszy, potwierdź je przed pierwszą wysyłką")
    return b


class Obsluga(BaseHTTPRequestHandler):
    server_version = "GeneratorAgencji/1"

    def log_message(self, *a):
        pass

    def _wyslij(self, kod, tresc, typ="application/json; charset=utf-8", naglowki=None):
        if isinstance(tresc, (dict, list)):
            tresc = json.dumps(tresc, ensure_ascii=False).encode("utf-8")
        elif isinstance(tresc, str):
            tresc = tresc.encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(tresc)))
        self.send_header("Cache-Control", "no-store")
        for n, w in (naglowki or {}).items():
            self.send_header(n, w)
        self.end_headers()
        self.wfile.write(tresc)

    def _plik(self, p, pobierz=False):
        if not p.is_file():
            return self._wyslij(404, {"blad": "Nie ma takiego pliku."})
        typ = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        if typ.startswith("text/") or typ in ("application/javascript", "image/svg+xml"):
            typ += "; charset=utf-8"
        nag = {"Content-Disposition": 'attachment; filename="%s"' % p.name} if pobierz else None
        self._wyslij(200, p.read_bytes(), typ, nag)

    def do_GET(self):
        u = urlparse(self.path)
        sciezka = unquote(u.path)
        try:
            if sciezka in ("/", "/index.html"):
                return self._plik(PANEL / "index.html")
            if sciezka == "/api/agencja":
                ns = rdzen.nisza("detailing")["oferta"]
                a = rdzen.agencja()
                return self._wyslij(200, dict(agencja_bez_sekretow(), oferta_efektywna=rdzen.scal(ns, a.get("oferta") or {})))
            if sciezka == "/api/stan":
                return self._wyslij(200, {"klienci": [skrot(k) for k in rdzen.lista()], "kolejka": kolejka(),
                                          "korzen": str(KORZEN), "agent": agent.stan(), "agencja": agencja_bez_sekretow(),
                                          "nisze": rdzen.nisze()})
            if sciezka.startswith("/api/klient/"):
                return self._wyslij(200, szczegoly(sciezka.split("/")[3]))
            if sciezka.startswith("/k/"):
                cel = (rdzen.KLIENCI / sciezka[3:]).resolve()
                if rdzen.KLIENCI.resolve() not in cel.parents:
                    return self._wyslij(403, {"blad": "Poza folderem klientow."})
                if cel.is_dir():
                    cel = cel / "index.html"
                return self._plik(cel, pobierz=cel.suffix == ".zip")
            self._wyslij(404, {"blad": "Nie ma takiej strony."})
        except FileNotFoundError:
            self._wyslij(404, {"blad": "Nie ma takiego klienta."})
        except Exception as e:
            traceback.print_exc()
            self._wyslij(500, {"blad": str(e)})

    def do_POST(self):
        sciezka = unquote(urlparse(self.path).path)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            surowe = self.rfile.read(n) if n else b""
            if self.headers.get("Origin") and urlparse(self.headers["Origin"]).hostname not in ("localhost", "127.0.0.1"):
                return self._wyslij(403, {"blad": "Zapis tylko z panelu."})
            cz = sciezka.split("/")
            if sciezka.startswith("/k/") and sciezka.endswith("/t.php"):
                return self._wyslij(204, b"")  # zdarzenia pokazu dzialaja dopiero na serwerze
            if len(cz) == 5 and cz[1] == "api" and cz[2] == "klient" and cz[4] == "zdjecia":
                return self._wyslij(200, self._zdjecie(cz[3], surowe))
            dane = json.loads(surowe.decode("utf-8") or "{}") if surowe else {}
            if sciezka == "/api/dodaj":
                return self._wyslij(200, self._dodaj(dane))
            if sciezka == "/api/agent":
                return self._wyslij(200, self._agent(dane))
            if sciezka == "/api/agencja":
                tg = dane.get("telegram") or {}
                if tg.get("token") in ("zapisany", ""):
                    tg.pop("token", None)
                rdzen.zapisz_agencje(dane)
                return self._wyslij(200, agencja_bez_sekretow())
            if sciezka == "/api/hosting":
                r = subprocess.run([PYTHON, "-m", "silnik", "hosting-" + ("instaluj" if dane.get("akcja") == "instaluj" else "test")],
                                   cwd=str(KORZEN), capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    raise ValueError((r.stderr.strip().splitlines() or ["blad"])[-1][:300])
                return self._wyslij(200, json.loads(r.stdout))
            if len(cz) == 5 and cz[1] == "api" and cz[2] == "klient":
                return self._wyslij(200, self._akcja(cz[3], cz[4], dane))
            self._wyslij(404, {"blad": "Nie ma takiej akcji."})
        except (ValueError, KeyError, FileNotFoundError) as e:
            self._wyslij(400, {"blad": str(e)})
        except Exception as e:
            traceback.print_exc()
            self._wyslij(500, {"blad": str(e)})

    def _dodaj(self, dane):
        wpisy = [w.strip() for w in (dane.get("linki") or "").replace(",", "\n").split("\n") if w.strip()]
        if not wpisy:
            raise ValueError("Wklej co najmniej jeden link do Instagrama albo nazwe firmy.")
        if dane.get("nisza") and dane["nisza"] not in [n["id"] for n in rdzen.nisze()]:
            raise ValueError("Nie ma pakietu niszy: " + dane["nisza"])
        out = []
        for w in wpisy[:40]:
            k, nowy = rdzen.nowy_klient(w, dane.get("nisza") or "detailing")
            ruszyl = False
            if dane.get("uruchom", True) and k["etapy"].get("zwiad") == "w_kolejce":
                ruszyl = agent.zlec(k["slug"])
            out.append({"slug": k["slug"], "nowy": nowy, "agent": ruszyl})
        return {"dodano": out}

    def _agent(self, dane):
        if dane.get("stop"):
            agent.zatrzymaj()
            return agent.stan()
        cele = [dane["slug"]] if dane.get("slug") else [x["slug"] for x in kolejka()["dla_claude"] if x["zadanie"].startswith(("zwiad", "3 kierunki"))]
        for s in cele:
            k = rdzen.wczytaj(s)
            zmiana = False
            for e in ("zwiad", "branding"):
                if k["etapy"].get(e) == "blad":
                    rdzen.ustaw_etap(k, e, "w_kolejce" if e == "zwiad" else "czeka", "ponowna próba")
                    zmiana = True
            if zmiana:
                rdzen.zapisz(k)
            agent.zlec(s)
        return agent.stan()

    def _zdjecie(self, slug, surowe):
        rdzen.wczytaj(slug)
        nazwa = Path(unquote(self.headers.get("X-Nazwa") or "zdjecie.jpg")).name
        if Path(nazwa).suffix.lower() not in ROZSZ_ZDJEC:
            raise ValueError("Dozwolone pliki: JPG, PNG, WEBP.")
        if not surowe or len(surowe) > 25 * 1024 * 1024:
            raise ValueError("Plik jest pusty albo większy niż 25 MB.")
        kat = rdzen.folder(slug) / "zwiad" / "zdjecia"
        kat.mkdir(parents=True, exist_ok=True)
        (kat / rdzen.slug(Path(nazwa).stem)).with_suffix(Path(nazwa).suffix.lower()).write_bytes(surowe)
        return {"ok": True, "zdjecia": len(instagram.zdjecia(slug)["foto"])}

    def _akcja(self, slug, akcja, dane):
        k = rdzen.wczytaj(slug)
        if akcja == "kierunek":
            kid = dane["id"]
            if not rdzen.kierunek(k, kid):
                raise ValueError("Nie ma kierunku '%s'." % kid)
            k["branding"]["wybrany"] = kid
            rdzen.ustaw_etap(k, "branding", "w_toku", "wybrano kierunek " + kid)
            rdzen.zapisz(k)
            kroki = [("branding", ["branding-final", slug]), ("instagram", ["instagram", slug])]
            if k["landing"].get("oferta_id"):  # zmiana stylu po wyborze oferty: landing i oferty tez dostaja nowy styl
                kroki += po_landingu(slug)
            w_tle(slug, "branding", *kroki)
        elif akcja == "oferta":
            landing.oferta(k, dane["id"])
            if not k["branding"].get("wybrany"):
                raise ValueError("Najpierw wybierz kierunek brandingu.")
            k["landing"]["oferta_id"] = dane["id"]
            rdzen.ustaw_etap(k, "usluga", "gotowe", dane["id"])
            rdzen.ustaw_etap(k, "landing", "w_toku")
            rdzen.zapisz(k)
            w_tle(slug, "landing", *po_landingu(slug))
        elif akcja == "dane":
            zmienione = []
            for pole, w in (dane.get("dane") or {}).items():
                if pole not in k["dane"]:
                    continue
                if pole in ("posty", "obserwujacy", "liczba_opinii"):
                    w = int(w) if str(w).strip() else None
                elif pole == "ocena_google":
                    w = float(str(w).replace(",", ".")) if str(w).strip() else None
                if k["dane"].get(pole) != w:
                    k["dane"][pole] = w
                    zmienione.append(pole)
            for pole in set(zmienione) | set(dane.get("potwierdz") or []):
                k.setdefault("pewnosc", {})[pole] = "potwierdzone"
            for pole in ("formularz_endpoint", "piksel_meta"):
                if pole in (dane.get("landing") or {}):
                    k["landing"][pole] = dane["landing"][pole].strip()
            if dane.get("tryb") in ("probka", "wdrozenie"):
                k["tryb"] = dane["tryb"]
            rdzen.dziennik(k, "panel: zapisano dane (%s)" % (", ".join(zmienione) or "bez zmian w polach"))
            if k["tryb"] == "wdrozenie":
                braki = landing.braki_wdrozenia(k)
                rdzen.ustaw_etap(k, "wdrozenie", "decyzja" if braki else "gotowe", "; ".join(braki))
            elif k["etapy"].get("wdrozenie") != "czeka":
                rdzen.ustaw_etap(k, "wdrozenie", "czeka", "powrot do trybu probki")
            rdzen.zapisz(k)
            if dane.get("przebuduj") and k["landing"].get("oferta_id") and k["branding"].get("wybrany"):
                w_tle(slug, "instagram", ("instagram", ["instagram", slug]), *po_landingu(slug))
        elif akcja == "przebuduj":
            etap = dane.get("etap")
            kroki = {
                "branding": [("branding", ["branding-szkice", slug]), ("branding", ["branding-final", slug])],
                "instagram": [("instagram", ["instagram", slug])],
                "landing": po_landingu(slug),
                "pokaz": [("pokaz", ["pokaz", slug])],
                "oferta": [("pokaz", ["pokaz", slug])],
            }.get(etap)
            if not kroki:
                raise ValueError("Tego etapu panel nie przebuduje sam.")
            rdzen.ustaw_etap(k, etap, "w_toku", "przebudowa z panelu")
            rdzen.zapisz(k)
            w_tle(slug, etap, *kroki)
        elif akcja == "oferta-dane":
            o = k["oferta"]
            for pole in ("rozmowa", "wazna_do", "polecany"):
                if pole in dane:
                    o[pole] = str(dane[pole]).strip()
            if "cele" in dane:
                o["cele"] = [{"cytat": c.get("cytat", "").strip(), "odp": c.get("odp", "").strip(), "gdzie": c.get("gdzie", "").strip()}
                             for c in dane["cele"] if c.get("cytat", "").strip()]
            rdzen.dziennik(k, "panel: zapisano dane oferty po rozmowie")
            rdzen.zapisz(k)
            if k["landing"].get("oferta_id"):
                w_tle(slug, "oferta", ("pokaz", ["pokaz", slug]))
        elif akcja == "publikuj":
            hosting.ustawienia()
            if not (rdzen.folder(slug) / "pokaz" / "index.html").exists():
                raise ValueError("Pokaz jeszcze nie powstal.")
            _aktywnosc.pop(slug, None)
            w_tle(slug, "pokaz", ("pokaz", ["publikuj", slug]))
        elif akcja == "oferta-leada":
            wlacz = bool(dane.get("wlacz"))
            ol = k.setdefault("oferta_leada", {})
            ol["wlaczona"] = wlacz
            rdzen.dziennik(k, "panel: oferta dla leada %s" % ("wlaczona" if wlacz else "wylaczona"))
            rdzen.zapisz(k)
            if k["landing"].get("oferta_id"):
                w_tle(slug, "landing", *po_landingu(slug))
        elif akcja == "wizualizacje":
            k["pokaz"]["wizualizacje_zamowione"] = bool(dane.get("zamow", True))
            rdzen.zapisz(k)
        elif akcja == "film":
            k["landing"]["film_zamowiony"] = bool(dane.get("zamow", True))
            rdzen.dziennik(k, "panel: film AI %s" % ("zamowiony" if k["landing"]["film_zamowiony"] else "anulowany"))
            rdzen.zapisz(k)
        else:
            raise ValueError("Nieznana akcja: " + akcja)
        return szczegoly(slug)


def start(port=8900):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Obsluga)
    print("Panel Generatora Agencji: http://localhost:%d" % port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    start(int(sys.argv[1]) if len(sys.argv) > 1 else 8900)
