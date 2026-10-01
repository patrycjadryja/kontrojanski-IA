"""Etap 2: branding. Trzy tanie szkice kierunkow, po wyborze pelny zestaw plikow i ksiega znaku."""
import shutil

from markupsafe import Markup

from . import chrome, logo, styl
from .rdzen import folder, kierunek, ustaw_etap, wczytaj, zapisz


def sprawdz(k):
    kier = k["branding"].get("kierunki", [])
    if not kier:
        raise ValueError("Brak kierunkow brandingu w klient.json (branding.kierunki).")
    bledy = []
    for d in kier:
        bledy += ["kierunek %s: %s" % (d.get("id", "?"), b) for b in styl.sprawdz_kierunek(d)]
    if len({d.get("id") for d in kier}) != len(kier):
        bledy.append("kierunki musza miec rozne id")
    if bledy:
        raise ValueError("Bledy w kierunkach brandingu:\n- " + "\n- ".join(bledy))
    return kier


def szkice(slug):
    k = wczytaj(slug)
    kier = sprawdz(k)
    baza = folder(slug) / "branding"
    widoki = []
    for d in kier:
        d = styl.normalizuj(d)
        cel = baza / ("kierunek-" + d["id"])
        cel.mkdir(parents=True, exist_ok=True)
        for plik, svg in logo.szkic(d).items():
            (cel / plik).write_text(svg, encoding="utf-8")
        widoki.append({"kier": d, "css": Markup(styl.zmienne(d)), "folder": "kierunek-" + d["id"],
                       "fonty_url": styl.F.link_css(d["fonty"])})
    from .rdzen import slownik
    styl.renderuj("branding/kierunki.html", baza / "kierunki.html", k=k, d=k["dane"], widoki=widoki, sl=slownik(k["nisza"]))
    if not k["branding"].get("wybrany"):
        ustaw_etap(k, "branding", "decyzja", "%d kierunki do wyboru" % len(kier))
    zapisz(k)
    return baza / "kierunki.html"


def final(slug, kid=None):
    k = wczytaj(slug)
    sprawdz(k)
    if kid:
        k["branding"]["wybrany"] = kid
    d = kierunek(k)
    if not d:
        raise ValueError("Nie wybrano kierunku brandingu.")
    ustaw_etap(k, "branding", "w_toku", "kierunek " + d["id"])
    zapisz(k)
    cel = folder(slug) / "branding" / "final"
    if cel.exists():
        shutil.rmtree(cel)
    cel.mkdir(parents=True)
    pliki = logo.komplet(d)
    for plik, svg in pliki.items():
        (cel / plik).write_text(svg, encoding="utf-8")
    # awatar PNG 1000x1000 do wgrania na Instagram
    tmp = cel / "_awatar.html"
    tmp.write_text('<!doctype html><body style="margin:0"><img src="awatar-instagram.svg" '
                   'style="display:block;width:1000px;height:1000px"></body>', encoding="utf-8")
    try:
        chrome.zrzut(tmp, cel / "awatar-instagram.png", 1000, 1000, budzet_ms=1500)
    finally:
        tmp.unlink()
    ctx = styl.kontekst(k, d)
    styl.renderuj("branding/ksiega.html", folder(slug) / "branding" / "ksiega.html", **ctx)
    k = wczytaj(slug)
    ustaw_etap(k, "branding", "gotowe", "%d plikow logo" % (len(pliki) + 1))
    zapisz(k)
    return cel
