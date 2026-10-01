"""Rdzen: sciezki, klient.json (jedno zrodlo prawdy), etapy, dziennik."""
import json
import re
import threading
import time
import unicodedata
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
KLIENCI = KORZEN / "klienci"
NISZE = KORZEN / "nisze"
SZABLONY = KORZEN / "szablony"
FONTY = KORZEN / "fonty"

# Kolejnosc etapow jest kolejnoscia zaleznosci: kazdy etap korzysta z poprzedniego.
ETAPY = ["zwiad", "branding", "instagram", "usluga", "landing", "pokaz", "oferta", "wdrozenie"]

# czeka      - etap jeszcze nie ruszyl
# w_kolejce  - czeka na Claude Code (komenda /generator-agencji)
# w_toku     - silnik wlasnie pracuje
# decyzja    - potrzebna decyzja czlowieka w panelu
# gotowe     - zrobione
# blad       - nie wyszlo, szczegoly w dzienniku
STANY = ["czeka", "w_kolejce", "w_toku", "decyzja", "gotowe", "blad"]

_blokada = threading.Lock()


def teraz():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def slug(tekst):
    t = unicodedata.normalize("NFKD", tekst.replace("ł", "l").replace("Ł", "L"))
    t = t.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "klient"


def handle_z_linku(link):
    """Wyciaga nazwe profilu z linku do Instagrama albo z samego @handle."""
    link = link.strip()
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", link)
    if m:
        return m.group(1).strip("/")
    if link.startswith("@"):
        return link[1:]
    return ""


def folder(s):
    return KLIENCI / s


def sciezka(s):
    return folder(s) / "klient.json"


def wczytaj(s):
    with open(sciezka(s), encoding="utf-8") as f:
        k = json.load(f)
    # klienci zalozeni przed dodaniem nowych etapow dostaja brakujace pola
    for e in ETAPY:
        k.setdefault("etapy", {}).setdefault(e, "czeka")
    k.setdefault("pokaz", {"tresc": {}, "wizualizacje_zamowione": False})
    k.setdefault("oferta", {"rozmowa": "", "wazna_do": "", "polecany": "", "cele": [], "platnosc": {}, "tresc": {}})
    return k


def agencja():
    """Dane nadawcy wspolne dla wszystkich klientow: podpis, kalendarz rozmow, kanal wiadomosci."""
    p = KORZEN / "agencja.json"
    d = {"nazwa": "", "nadawca": "", "kalendarz": "", "wiadomosc": "", "chrome": True,
         "hosting": {}, "telegram": {}, "oferta": {}}
    if p.exists():
        with open(p, encoding="utf-8") as f:
            d.update({a: b for a, b in json.load(f).items() if not a.startswith("_")})
    return d


def zapisz_agencje(d):
    stare = agencja()
    for a, b in d.items():
        if a not in stare:
            continue
        if isinstance(stare[a], dict) and isinstance(b, dict):
            stare[a].update(b)
        else:
            stare[a] = b
    with open(KORZEN / "agencja.json", "w", encoding="utf-8") as f:
        json.dump(stare, f, ensure_ascii=False, indent=2)
    return stare


def zapisz(k):
    k["zmieniono"] = teraz()
    p = sciezka(k["slug"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with _blokada:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(k, f, ensure_ascii=False, indent=2)
        tmp.replace(p)
    return k


def lista():
    out = []
    if not KLIENCI.exists():
        return out
    for d in sorted(KLIENCI.iterdir()):
        if (d / "klient.json").exists():
            try:
                out.append(wczytaj(d.name))
            except Exception as e:  # uszkodzony plik nie moze polozyc panelu
                out.append({"slug": d.name, "blad_pliku": str(e), "dane": {"nazwa": d.name}, "etapy": {}})
    return out


def dziennik(k, tekst):
    k.setdefault("dziennik", []).append({"kiedy": teraz(), "co": tekst})
    k["dziennik"] = k["dziennik"][-80:]


def ustaw_etap(k, etap, stan, notatka=""):
    assert etap in ETAPY and stan in STANY, (etap, stan)
    k.setdefault("etapy", {})[etap] = stan
    dziennik(k, "%s: %s%s" % (etap, stan, (" - " + notatka) if notatka else ""))


def pusty_klient(s, nisza="detailing"):
    return {
        "slug": s,
        "nisza": nisza,
        "tryb": "probka",
        "utworzono": teraz(),
        "zrodlo": {"instagram": "", "www": "", "google": "", "notatka": ""},
        "dane": {
            "nazwa": "", "nazwa_krotka": "", "dopisek": "", "miasto": "", "adres": "", "kod": "",
            "telefon": "", "email": "", "ig_handle": "", "bio": "", "kategorie": "",
            "posty": None, "obserwujacy": None, "ocena_google": None, "liczba_opinii": None,
        },
        # pewnosc[pole] = "odczytane" | "zgadniete" | "potwierdzone"
        "pewnosc": {},
        "uslugi": [],
        "diagnoza": {"logo": "", "feed": []},
        "branding": {"kierunki": [], "wybrany": ""},
        "instagram": {},
        "landing": {"usluga_id": "", "oferta_id": "", "tresc": {}, "film": {"tryb": "kadry"},
                    "formularz_endpoint": "", "piksel_meta": ""},
        # warstwa 1: pokaz prywatny wysylany na zimno; warstwa 2: oferta po rozmowie sprzedazowej
        "pokaz": {"tresc": {}, "wizualizacje_zamowione": False},
        "oferta": {"rozmowa": "", "wazna_do": "", "polecany": "", "cele": [], "platnosc": {}, "tresc": {}},
        "etapy": {e: "czeka" for e in ETAPY},
        "dziennik": [],
    }


def nowy_klient(wejscie, nisza="detailing"):
    """Tworzy klienta z linku do IG, @handle albo samej nazwy. Zwraca (klient, czy_nowy)."""
    wejscie = wejscie.strip()
    h = handle_z_linku(wejscie)
    s = slug(h.replace("_", "-").replace(".", "-")) if h else slug(wejscie)
    if sciezka(s).exists():
        return wczytaj(s), False
    k = pusty_klient(s, nisza)
    if h:
        k["zrodlo"]["instagram"] = "https://www.instagram.com/%s/" % h
        k["dane"]["ig_handle"] = h
        k["dane"]["nazwa"] = h.replace("_", " ").replace(".", " ").title()
    else:
        k["dane"]["nazwa"] = wejscie
    for sub in ("zwiad/zdjecia", "branding", "instagram", "landing"):
        (folder(s) / sub).mkdir(parents=True, exist_ok=True)
    ustaw_etap(k, "zwiad", "w_kolejce", "dodano do kolejki")
    return zapisz(k), True


def nisza(nazwa):
    with open(NISZE / nazwa / "nisza.json", encoding="utf-8") as f:
        return json.load(f)


def slownik(nazwa_niszy):
    """Slowa zalezne od niszy (firma/obiekt), z bezpiecznymi domyslnymi."""
    d = {"firma": "firma", "firmy": "firmy", "firmie": "firmie", "obiekt": "realizacja", "obiektu": "realizacji",
         "obiektem": "realizacją", "realizacja_opis": "nazwa realizacji", "split_podpis": "Przed i po",
         "probka_tytulu": "Efekt, który *widać*", "probka_posta": "Jak to *robimy*",
         "brak_zdjec": "Po dostarczeniu zdjęć realizacji kafle wypełnią się pracami firmy.", "przyklad_klienta": "np. nazwa"}
    try:
        d.update(nisza(nazwa_niszy).get("slownik") or {})
    except (FileNotFoundError, ValueError):
        pass
    return d


def nisze():
    """Lista dostepnych pakietow niszowych."""
    out = []
    for d in sorted(NISZE.iterdir()) if NISZE.exists() else []:
        if (d / "nisza.json").exists():
            try:
                n = nisza(d.name)
                out.append({"id": d.name, "nazwa": n.get("nazwa", d.name), "klient": n.get("nazwa_klienta", "")})
            except ValueError:
                out.append({"id": d.name, "nazwa": d.name + " (uszkodzony plik)", "klient": ""})
    return out


def kierunek(k, kid=None):
    kid = kid or k["branding"].get("wybrany")
    for d in k["branding"].get("kierunki", []):
        if d["id"] == kid:
            return d
    return None


def scal(baza, nadpisanie):
    """Glebokie scalenie slownikow: nadpisanie wygrywa, puste wartosci nie kasuja bazy."""
    if not isinstance(baza, dict) or not isinstance(nadpisanie, dict):
        return nadpisanie if nadpisanie not in (None, "", [], {}) else baza
    out = dict(baza)
    for kl, w in nadpisanie.items():
        out[kl] = scal(baza.get(kl), w) if kl in baza else w
    return out
