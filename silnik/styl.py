"""Styl kierunku jako zmienne CSS + srodowisko szablonow. Jeden styl zasila branding, Instagram i landing."""
import re

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

from . import fonty as F
from .logo import MOTYWY, jasnosc, kontrast
from .rdzen import SZABLONY

TOKENY = ["ink", "carbon", "graphite", "bone", "mute", "accent", "on_accent"]
OBROBKA = "contrast(1.1) saturate(.78) brightness(.88)"


def sprawdz_kierunek(k):
    """Zwraca liste bledow kierunku brandingu. Pusta lista = kierunek poprawny."""
    b = []
    for pole in ("id", "nazwa", "tokeny", "logo"):
        if not k.get(pole):
            b.append("brak pola '%s'" % pole)
    for t in TOKENY:
        w = (k.get("tokeny") or {}).get(t, "")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", w or ""):
            b.append("token '%s' musi byc kolorem #rrggbb (jest: %r)" % (t, w))
    try:
        F.uzupelnij(k.get("fonty"))
    except ValueError as e:
        b.append(str(e))
    lg = k.get("logo") or {}
    if not lg.get("tekst"):
        b.append("logo.tekst jest puste")
    if lg.get("motyw") not in MOTYWY:
        b.append("logo.motyw musi byc jednym z: " + ", ".join(MOTYWY))
    if not b:
        t = k["tokeny"]
        if kontrast(t["ink"], t["bone"]) < 7:
            b.append("za maly kontrast miedzy ink i bone (minimum 7:1)")
        if kontrast(t["accent"], t["on_accent"]) < 3:
            b.append("za maly kontrast miedzy accent i on_accent (minimum 3:1)")
        if kontrast(t["accent"], t["ink"]) < 3:
            b.append("akcent za slabo widoczny na tle ink (minimum 3:1)")
    return b


def normalizuj(kier):
    """Uzupelnia pola opcjonalne, zeby szablony nie musialy sprawdzac ich istnienia."""
    k = dict(kier)
    for pole in ("archetyp", "opis", "uzasadnienie", "probka_tytulu", "probka_posta"):
        k.setdefault(pole, "")
    k["schemat"] = "dark" if jasnosc(k["tokeny"]["ink"]) < 0.18 else "light"
    k.setdefault("krawedzie", "ostre")
    k["logo"] = dict(k["logo"])
    k["logo"].setdefault("dopisek", "")
    k["fonty"] = F.uzupelnij(k.get("fonty"))
    return k


def zmienne(kier):
    """Blok deklaracji CSS dla :root."""
    t = kier["tokeny"]
    f = F.uzupelnij(kier.get("fonty"))
    d = f["display"]
    ciemny = jasnosc(t["ink"]) < 0.18
    ostre = kier.get("krawedzie", "ostre") == "ostre"
    r = t["ink"].lstrip("#")
    rgb = ",".join(str(int(r[i:i + 2], 16)) for i in (0, 2, 4))
    linie = [
        "color-scheme:%s" % ("dark" if ciemny else "light"),
    ] + ["--%s:%s" % (n.replace("_", "-"), t[n]) for n in TOKENY] + [
        "--ink-rgb:%s" % rgb,
        "--on-accent-2:%s" % (t["bone"] if kontrast(t["bone"], t["accent"]) >= kontrast(t["ink"], t["accent"]) and t["on_accent"] != t["bone"] else
                              (t["ink"] if t["on_accent"] != t["ink"] else t["bone"])),
        '--display:"%s","Arial Narrow",Arial,sans-serif' % d["rodzina"],
        '--body:"%s",system-ui,-apple-system,"Segoe UI",sans-serif' % f["tekst"]["rodzina"],
        '--mono:"%s",ui-monospace,Menlo,monospace' % f["mono"]["rodzina"],
        "--display-stretch:%s%%" % d.get("wdth", 100),
        "--display-weight:%s" % d["wght"],
        "--display-weight-2:%s" % max(F.KATALOG[d["rodzina"]]["wght"][0], min(d["wght"], d["wght"] - 100 if d["wght"] >= 800 else d["wght"])),
        "--display-case:%s" % ("uppercase" if d.get("wersaliki", True) else "none"),
        "--display-tracking:%sem" % d.get("tracking", 0),
        "--display-leading:%s" % (".98" if d.get("wersaliki", True) else "1.06"),
        "--radius:%s" % ("0px" if ostre else "12px"),
        "--grade:%s" % kier.get("obrobka", OBROBKA),
        "--film:%s" % kier.get("film", "none"),
    ]
    return ";".join(linie)


def akcenty(k, kier):
    """Akcent wybranego kierunku + akcenty pozostalych kierunkow jako warianty do przelaczania."""
    out = []
    for d in [kier] + [x for x in k["branding"].get("kierunki", []) if x["id"] != kier["id"]]:
        t = d["tokeny"]
        if any(a["accent"].lower() == t["accent"].lower() for a in out):
            continue
        na = t["on_accent"] if kontrast(t["accent"], t["on_accent"]) >= 3 else kier["tokeny"]["ink"]
        out.append({"id": d["id"], "nazwa": d["nazwa"], "accent": t["accent"], "on_accent": na,
                    "film": d.get("film", "none"), "opis": (d.get("archetyp") or "").replace("odwazny", "sportowy").capitalize()})
    return out


def css_akcentow(lista):
    return Markup("\n".join(':root[data-accent="%s"]{--accent:%s;--on-accent:%s;--film:%s}' % (a["id"], a["accent"], a["on_accent"], a["film"])
                            for a in lista[1:]))


def _akcent(tekst):
    """*slowo* w tresci staje sie slowem w kolorze akcentu."""
    s = str(escape(tekst or ""))
    return Markup(re.sub(r"\*(.+?)\*", r"<em>\1</em>", s))


def _bez_gwiazdek(tekst):
    return (tekst or "").replace("*", "")


def _tel_link(tel):
    c = re.sub(r"\D", "", tel or "")
    if len(c) == 9:
        c = "48" + c
    return "tel:+" + c if c else "#"


def _tysiace(v):
    try:
        return "{:,}".format(int(v)).replace(",", " ")
    except (TypeError, ValueError):
        return v


def srodowisko():
    env = Environment(loader=FileSystemLoader(str(SZABLONY)), autoescape=True,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.filters["akcent"] = _akcent
    env.filters["czysty"] = _bez_gwiazdek
    env.filters["tel_link"] = _tel_link
    env.filters["tysiace"] = _tysiace
    return env


def renderuj(szablon, cel, **dane):
    html = srodowisko().get_template(szablon).render(**dane)
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_text(html, encoding="utf-8")
    return cel


def kontekst(k, kier):
    """Wspolne dane dla wszystkich szablonow."""
    from .logo import kolory
    from .rdzen import slownik
    kier = normalizuj(kier)
    f = kier["fonty"]
    return {
        "k": k, "d": k["dane"], "kier": kier, "css": Markup(zmienne(kier)),
        "fonty": f, "kolory": kolory(kier), "sl": slownik(k.get("nisza", "")),
        "fonty_url": F.link_css(f), "probka": k.get("tryb", "probka") != "wdrozenie",
        "znak": (kier["logo"]["tekst"]), "dopisek": kier["logo"].get("dopisek", ""),
    }
