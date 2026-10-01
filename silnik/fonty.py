"""Kroje pisma: katalog darmowych krojow Google Fonts, link do CSS i pobieranie TTF do zamiany tekstu na krzywe."""
import re
import urllib.parse
import urllib.request

from .rdzen import FONTY, slug

# Tylko kroje z tego katalogu wolno wpisywac w kierunkach brandingu.
# osie: zakresy potrzebne do zbudowania linku CSS. "pojedynczy" = kroj w jednej odmianie.
KATALOG = {
    # tytulowe
    "Archivo": {"osie": "wdth,wght@62..125,100..900", "wdth": (62, 125), "wght": (100, 900), "rola": "display"},
    "Saira": {"osie": "wdth,wght@50..125,100..900", "wdth": (50, 125), "wght": (100, 900), "rola": "display"},
    "Unbounded": {"osie": "wght@200..900", "wght": (200, 900), "rola": "display"},
    "Big Shoulders Display": {"osie": "wght@100..900", "wght": (100, 900), "rola": "display"},
    "Syne": {"osie": "wght@400..800", "wght": (400, 800), "rola": "display"},
    "Oswald": {"osie": "wght@200..700", "wght": (200, 700), "rola": "display"},
    "Bebas Neue": {"osie": "", "wght": (400, 400), "rola": "display"},
    "Anton": {"osie": "", "wght": (400, 400), "rola": "display"},
    "Michroma": {"osie": "", "wght": (400, 400), "rola": "display"},
    "Krona One": {"osie": "", "wght": (400, 400), "rola": "display"},
    "Exo 2": {"osie": "wght@100..900", "wght": (100, 900), "rola": "display"},
    "Chakra Petch": {"osie": "wght@300;400;500;600;700", "wght": (300, 700), "rola": "display"},
    "Red Hat Display": {"osie": "wght@300..900", "wght": (300, 900), "rola": "display"},
    "Montserrat": {"osie": "wght@100..900", "wght": (100, 900), "rola": "display"},
    "Playfair Display": {"osie": "wght@400..900", "wght": (400, 900), "rola": "display"},
    "Bodoni Moda": {"osie": "wght@400..900", "wght": (400, 900), "rola": "display"},
    "Cormorant Garamond": {"osie": "wght@300..700", "wght": (300, 700), "rola": "display"},
    # tekstowe
    "Space Grotesk": {"osie": "wght@300..700", "wght": (300, 700), "rola": "tekst"},
    "Sora": {"osie": "wght@100..800", "wght": (100, 800), "rola": "tekst"},
    "Inter": {"osie": "wght@100..900", "wght": (100, 900), "rola": "tekst"},
    "Manrope": {"osie": "wght@200..800", "wght": (200, 800), "rola": "tekst"},
    "Instrument Sans": {"osie": "wdth,wght@75..100,400..700", "wdth": (75, 100), "wght": (400, 700), "rola": "tekst"},
    # maszynowe
    "IBM Plex Mono": {"osie": "wght@400;500", "wght": (400, 500), "rola": "mono"},
    "JetBrains Mono": {"osie": "wght@100..800", "wght": (100, 800), "rola": "mono"},
    "Space Mono": {"osie": "wght@400;700", "wght": (400, 700), "rola": "mono"},
    "DM Mono": {"osie": "wght@300;400;500", "wght": (300, 500), "rola": "mono"},
}

DOMYSLNE = {
    "display": {"rodzina": "Archivo", "wght": 900, "wdth": 125, "wersaliki": True, "tracking": -0.012},
    "tekst": {"rodzina": "Archivo"},
    "mono": {"rodzina": "IBM Plex Mono"},
}


def _sprawdz(rodzina):
    if rodzina not in KATALOG:
        raise ValueError("Kroj '%s' nie jest w katalogu. Dostepne: %s" % (rodzina, ", ".join(sorted(KATALOG))))
    return KATALOG[rodzina]


def uzupelnij(fonty):
    """Zwraca komplet ustawien krojow z domyslnymi wartosciami i przycietymi osiami."""
    out = {}
    for rola in ("display", "tekst", "mono"):
        f = dict(DOMYSLNE[rola])
        f.update((fonty or {}).get(rola) or {})
        k = _sprawdz(f["rodzina"])
        if rola == "display":
            lo, hi = k["wght"]
            f["wght"] = max(lo, min(hi, int(f.get("wght", 800))))
            if "wdth" in k:
                lo, hi = k["wdth"]
                f["wdth"] = max(lo, min(hi, int(f.get("wdth", 100))))
            else:
                f["wdth"] = 100
            f.setdefault("wersaliki", True)
            f.setdefault("tracking", 0)
        out[rola] = f
    return out


def link_css(fonty):
    """Jeden link do Google Fonts dla wszystkich krojow kierunku."""
    rodziny = []
    for rola in ("display", "tekst", "mono"):
        r = fonty[rola]["rodzina"]
        if r not in rodziny:
            rodziny.append(r)
    czesci = []
    for r in rodziny:
        osie = KATALOG[r]["osie"]
        czesci.append("family=" + r.replace(" ", "+") + ((":" + osie) if osie else ""))
    return "https://fonts.googleapis.com/css2?" + "&".join(czesci) + "&display=swap"


def pobierz_ttf(rodzina, wght=400, wdth=None):
    """Pobiera (raz) odmiane kroju jako TTF. Google zwraca TTF klientom bez obslugi woff2."""
    k = _sprawdz(rodzina)
    FONTY.mkdir(exist_ok=True)
    lo, hi = k["wght"]
    wght = max(lo, min(hi, int(wght)))
    ma_wdth = "wdth" in k and wdth
    nazwa = "%s-%s%s.ttf" % (slug(rodzina), wght, ("-w%s" % int(wdth)) if ma_wdth else "")
    cel = FONTY / nazwa
    if cel.exists() and cel.stat().st_size > 1000:
        return cel
    fam = rodzina.replace(" ", "+")
    if not k["osie"]:
        q = fam
    elif ma_wdth:
        q = "%s:wdth,wght@%s,%s" % (fam, int(wdth), wght)
    else:
        q = "%s:wght@%s" % (fam, wght)
    url = "https://fonts.googleapis.com/css2?family=" + q
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    m = re.findall(r"url\((https://[^)]+\.ttf)\)", css)
    if not m:
        raise RuntimeError("Google Fonts nie zwrocil pliku TTF dla: " + urllib.parse.unquote(q))
    # ostatni blok w odpowiedzi to zestaw lacinski podstawowy; przy TTF jest zwykle jeden
    dane = urllib.request.urlopen(m[-1], timeout=60).read()
    cel.write_bytes(dane)
    return cel
