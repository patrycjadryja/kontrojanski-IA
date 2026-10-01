"""Generator logo: tekst zamieniany na krzywe SVG + motyw graficzny w kolorze akcentu.

Motywy: refleks (ukosne smugi w jednej literze), belka (kreska akcentu przy dopisku),
punkt (kwadrat po ostatniej literze), rama (obrys ze znacznikiem), ciecie (poziome przeciecie liter).
"""
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from . import fonty as F

MOTYWY = ["refleks", "belka", "punkt", "rama", "ciecie"]
H = 140.0  # wysokosc wersalika logotypu w jednostkach rysunku

_cache = {}


def _font(sciezka):
    s = str(sciezka)
    if s not in _cache:
        _cache[s] = TTFont(s)
    return _cache[s]


def _n(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def jasnosc(hexkolor):
    h = hexkolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def kontrast(a, b):
    """Wspolczynnik kontrastu WCAG dwoch kolorow (1-21)."""
    x, y = sorted((jasnosc(a), jasnosc(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def napis(ttf, tekst, wys=H, tracking_em=0.0):
    """Zwraca krzywe napisu. Wysokosc wersalika = wys, lewa krawedz pierwszej litery w x=0."""
    font = _font(ttf)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    cap = getattr(font["OS/2"], "sCapHeight", 0) or 0.7 * upm
    s = wys / cap
    em = upm * s
    hmtx = font["hmtx"]
    x = 0.0
    gl = []
    for ch in tekst:
        nazwa = cmap.get(ord(ch))
        if ch == " " or not nazwa:
            x += (hmtx[cmap[32]][0] * s if 32 in cmap else em * 0.28) + tracking_em * em
            continue
        bp = BoundsPen(gs)
        gs[nazwa].draw(bp)
        if bp.bounds is None:
            x += hmtx[nazwa][0] * s + tracking_em * em
            continue
        pen = SVGPathPen(gs, ntos=_n)
        gs[nazwa].draw(TransformPen(pen, (s, 0, 0, -s, x, wys)))
        b = bp.bounds
        gl.append({"d": pen.getCommands(), "x0": x + b[0] * s, "x1": x + b[2] * s,
                   "y0": wys - b[3] * s, "y1": wys - b[1] * s, "ch": ch})
        x += hmtx[nazwa][0] * s + tracking_em * em
    if not gl:
        raise ValueError("Kroj nie zawiera znakow napisu: %r" % tekst)
    dx = gl[0]["x0"]
    return {
        "glify": gl, "dx": dx,
        "szer": gl[-1]["x1"] - dx,
        "y0": min(g["y0"] for g in gl), "y1": max(g["y1"] for g in gl),
    }


def _sciezki(n, fill, extra="", litery=False):
    if litery:  # kazda litera w grupie, zeby animacja CSS nie nadpisywala atrybutu transform
        srodek = "".join('<g class="l" style="--i:%d"><path d="%s"/></g>' % (i, g["d"]) for i, g in enumerate(n["glify"]))
    else:
        srodek = "".join('<path d="%s"/>' % g["d"] for g in n["glify"])
    return '<g class="lg-letters" transform="translate(%s 0)" fill="%s"%s>%s</g>' % (_n(-n["dx"]), fill, extra, srodek)


def _motyw(tresc):
    return '<g class="lg-motif">%s</g>' % tresc


def _smugi(cx, wys, skala=1.0):
    """Dwie ukosne smugi (szeroka i cienka) wycentrowane na cx."""
    k = 0.53
    a, przerwa, b = 0.31 * wys * skala, 0.085 * wys * skala, 0.065 * wys * skala
    zapas = 0.15 * wys
    dol, gora = wys + zapas, -zapas
    lewa = cx - (a + przerwa + b) / 2 - k * (wys / 2 + zapas)
    out = []
    for start, szer in ((lewa, a), (lewa + a + przerwa, b)):
        gx = start + k * (dol - gora)
        out.append('<polygon points="%s,%s %s,%s %s,%s %s,%s"/>' % (
            _n(start), _n(dol), _n(start + szer), _n(dol), _n(gx + szer), _n(gora), _n(gx), _n(gora)))
    return "".join(out)


def _indeks_litery(n, cfg):
    i = cfg.get("litera")
    ile = len(n["glify"])
    if i is None:
        i = ile // 2
    return max(0, min(ile - 1, int(i)))


def _znak(n, cfg, fg, akcent, uid, litery=False):
    """Logotyp (sam napis) z motywem. Zwraca (svg, szer, y0, y1)."""
    motyw = cfg.get("motyw", "refleks")
    W, y0, y1 = n["szer"], min(0, n["y0"]), max(H, n["y1"])
    czesci = []
    if motyw == "ciecie":
        yc, g = H * 0.60, H * 0.075
        czesci.append('<mask id="m%s"><rect x="-10" y="%s" width="%s" height="%s" fill="#fff"/>'
                      '<rect x="-10" y="%s" width="%s" height="%s" fill="#000"/></mask>' % (
                          uid, _n(y0 - 10), _n(W + 20), _n(y1 - y0 + 20), _n(yc), _n(W + 20), _n(g)))
        czesci.append(_sciezki(n, fg, ' mask="url(#m%s)"' % uid, litery))
        czesci.append(_motyw('<rect x="0" y="%s" width="%s" height="%s" fill="%s"/>' % (
            _n(yc + g * 0.3), _n(W * 0.34), _n(g * 0.4), akcent)))
    else:
        czesci.append(_sciezki(n, fg, litery=litery))
    if motyw == "refleks":
        g = n["glify"][_indeks_litery(n, cfg)]
        cx = (g["x0"] + g["x1"]) / 2 - n["dx"]
        czesci.append('<clipPath id="c%s"><path transform="translate(%s 0)" d="%s"/></clipPath>' % (
            uid, _n(-n["dx"]), g["d"]))
        if litery:  # przelot smugi przez caly napis, zanim zostanie w jednej literze
            czesci.append('<clipPath id="a%s">%s</clipPath>' % (uid, "".join(
                '<path transform="translate(%s 0)" d="%s"/>' % (_n(-n["dx"]), x["d"]) for x in n["glify"])))
            czesci.append('<g clip-path="url(#a%s)"><g class="lg-sweep" style="--sw:%spx" fill="%s">%s</g></g>' % (
                uid, _n(W + H * 1.6), akcent, _smugi(-H * 0.8, H)))
        czesci.append('<g clip-path="url(#c%s)">%s</g>' % (uid, _motyw('<g fill="%s">%s</g>' % (akcent, _smugi(cx, H)))))
    if motyw == "punkt":
        bok = H * 0.24
        czesci.append(_motyw('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (
            _n(W + H * 0.09), _n(H - bok), _n(bok), _n(bok), akcent)))
        W += H * 0.09 + bok
    return "".join(czesci), W, y0, y1


def _svg(szer, wys, tresc, tlo=None, minx=0.0, miny=0.0):
    t = '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (_n(minx), _n(miny), _n(szer), _n(wys), tlo) if tlo else ""
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s">%s%s</svg>' % (
        _n(minx), _n(miny), _n(szer), _n(wys), t, tresc)


def _ttf(kier):
    f = F.uzupelnij(kier.get("fonty"))
    d, m = f["display"], f["mono"]
    return f, F.pobierz_ttf(d["rodzina"], d["wght"], d.get("wdth")), F.pobierz_ttf(m["rodzina"], 400)


def _teksty(kier):
    f = F.uzupelnij(kier.get("fonty"))
    cfg = kier["logo"]
    t = cfg["tekst"]
    if f["display"].get("wersaliki", True):
        t = t.upper()
    return t, (cfg.get("dopisek") or "").upper(), cfg


def logotyp(kier, fg, akcent, tlo=None, margines=0.0, uid="l", litery=False):
    """Sam napis z motywem, bez dopisku."""
    f, ttf_d, _ = _ttf(kier)
    t, _, cfg = _teksty(kier)
    n = napis(ttf_d, t, H, f["display"].get("tracking", 0))
    znak, W, y0, y1 = _znak(n, cfg, fg, akcent, uid, litery)
    m = margines * H
    return _svg(W + 2 * m, (y1 - y0) + 2 * m, znak, tlo, -m, y0 - m)


def logo(kier, fg, akcent, tlo=None, margines=0.0, uid="p", litery=False):
    """Logo podstawowe: napis + dopisek + motyw."""
    f, ttf_d, ttf_m = _ttf(kier)
    t, dop, cfg = _teksty(kier)
    motyw = cfg.get("motyw", "refleks")
    n = napis(ttf_d, t, H, f["display"].get("tracking", 0))
    znak, W, y0, y1 = _znak(n, cfg, fg, akcent, uid, litery)
    czesci = [znak]
    dol = y1
    if dop:
        wd = H * 0.2
        odstep = H * 0.3
        belka = (H * 0.42, H * 0.035) if motyw == "belka" else (0, 0)
        wolne = W - (belka[0] + H * 0.14 if belka[0] else 0)
        nd = napis(ttf_m, dop, wd, 0.3)
        if nd["szer"] > wolne:  # dopisek nie moze byc szerszy od logotypu
            wd *= wolne / nd["szer"]
            nd = napis(ttf_m, dop, wd, 0.3)
        ty = y1 + odstep
        tx = 0
        if belka[0]:
            czesci.append(_motyw('<rect x="0" y="%s" width="%s" height="%s" fill="%s"/>' % (
                _n(ty + wd / 2 - belka[1] / 2), _n(belka[0]), _n(belka[1]), akcent)))
            tx = belka[0] + H * 0.14
        czesci.append('<g class="lg-sub" transform="translate(%s %s)">%s</g>' % (_n(tx), _n(ty), _sciezki(nd, fg)))
        dol = ty + wd
    elif motyw == "belka":
        czesci.append(_motyw('<rect x="0" y="%s" width="%s" height="%s" fill="%s"/>' % (
            _n(y1 + H * 0.2), _n(H * 0.9), _n(H * 0.06), akcent)))
        dol = y1 + H * 0.26
    minx, miny, szer, wys = 0.0, y0, W, dol - y0
    if motyw == "rama":
        p = H * 0.42
        gr = H * 0.035
        minx, miny, szer, wys = -p, y0 - p, W + 2 * p, (dol - y0) + 2 * p
        czesci.append('<rect class="lg-sub" x="%s" y="%s" width="%s" height="%s" fill="none" stroke="%s" stroke-width="%s"/>' % (
            _n(minx + gr / 2), _n(miny + gr / 2), _n(szer - gr), _n(wys - gr), fg, _n(gr)))
        bok = H * 0.2
        czesci.append(_motyw('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (
            _n(minx + szer - bok), _n(miny), _n(bok), _n(bok), akcent)))
    m = margines * H
    return _svg(szer + 2 * m, wys + 2 * m, "".join(czesci), tlo, minx - m, miny - m)


def sygnet(kier, fg, akcent, tlo, bok=1000.0, skala=0.5, uid="s"):
    """Kwadratowy znak: inicjal lub monogram z tym samym motywem co logo."""
    f, ttf_d, _ = _ttf(kier)
    t, _, cfg = _teksty(kier)
    mono = (cfg.get("monogram") or t[:1])
    if f["display"].get("wersaliki", True):
        mono = mono.upper()
    motyw = cfg.get("motyw", "refleks")
    n = napis(ttf_d, mono, H, f["display"].get("tracking", 0) if len(mono) > 1 else 0)
    cfg2 = dict(cfg, litera=0 if len(mono) == 1 else cfg.get("litera_monogramu", 0))
    znak, W, y0, y1 = _znak(n, cfg2, fg, akcent, uid)
    wys = y1 - y0
    dodatki = ""
    if motyw == "belka":
        dodatki = '<rect x="0" y="%s" width="%s" height="%s" fill="%s"/>' % (
            _n(y1 + H * 0.2), _n(max(W, H * 0.5)), _n(H * 0.08), akcent)
        wys += H * 0.28
        W = max(W, H * 0.5)
    # monogram wieloliterowy nie moze wyjsc poza pole
    s = min(bok * skala / H, bok * 0.62 / W)
    tx, ty = (bok - W * s) / 2, (bok - wys * s) / 2 - y0 * s
    tresc = '<g transform="translate(%s %s) scale(%s)">%s%s</g>' % (_n(tx), _n(ty), _n(s), znak, dodatki)
    if motyw == "rama":
        gr = bok * 0.018
        o = bok * 0.13
        tresc += '<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="%s" stroke-width="%s"/>' % (
            _n(o), _n(o), _n(bok - 2 * o), _n(bok - 2 * o), fg, _n(gr))
        tresc += '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (
            _n(bok - o - bok * 0.09), _n(o - gr / 2), _n(bok * 0.09 + gr / 2), _n(bok * 0.09 + gr / 2), akcent)
    return _svg(bok, bok, tresc, tlo)


def kolory(kier):
    """Jasny i ciemny kolor marki niezaleznie od schematu (ciemny lub jasny)."""
    t = kier["tokeny"]
    para = sorted([t["ink"], t["bone"]], key=jasnosc)
    return {"ciemny": para[0], "jasny": para[1], "akcent": t["accent"], "na_akcencie": t.get("on_accent", para[0])}


def szkic(kier):
    """Tani podglad kierunku: logo, logotyp i sygnet na tle marki."""
    t = kier["tokeny"]
    return {
        "logo.svg": logo(kier, t["bone"], t["accent"]),
        "logotyp.svg": logotyp(kier, t["bone"], t["accent"]),
        "sygnet.svg": sygnet(kier, t["bone"], t["accent"], t["ink"]),
        "logo-odwrocone.svg": logo(kier, t["ink"], t["accent"]),
    }


def komplet(kier):
    """Pelny zestaw plikow logo dla wybranego kierunku."""
    c = kolory(kier)
    return {
        "logo-podstawowe-jasne-na-ciemnym.svg": logo(kier, c["jasny"], c["akcent"]),
        "logo-podstawowe-ciemne-na-jasnym.svg": logo(kier, c["ciemny"], c["akcent"]),
        "logo-mono-biale.svg": logo(kier, "#ffffff", "#ffffff"),
        "logo-mono-czarne.svg": logo(kier, "#000000", "#000000"),
        "logotyp-jasny.svg": logotyp(kier, c["jasny"], c["akcent"]),
        "logotyp-ciemny.svg": logotyp(kier, c["ciemny"], c["akcent"]),
        "logotyp-na-akcencie.svg": logotyp(kier, c["na_akcencie"], c["jasny"] if jasnosc(c["na_akcencie"]) < .18 else c["ciemny"]),
        "sygnet-jasny.svg": sygnet(kier, c["ciemny"], c["akcent"], c["jasny"]),
        "sygnet-ciemny.svg": sygnet(kier, c["jasny"], c["akcent"], c["ciemny"]),
        "awatar-instagram.svg": sygnet(kier, c["jasny"], c["akcent"], c["ciemny"], skala=0.46),
    }


AKCENT_CSS = "#ac0ce7"  # znacznik podmieniany na zmienna CSS


def _do_html(svg, klasa, opis):
    svg = svg.replace('fill="%s"' % AKCENT_CSS, 'style="fill:var(--accent)"')
    svg = svg.replace('class="lg-sweep" style="', 'class="lg-sweep" style="fill:var(--accent);')
    svg = svg.replace(' style="fill:var(--accent);--sw', ' style="--sw').replace('px" style="fill:var(--accent)"', 'px;fill:var(--accent)"')
    assert AKCENT_CSS not in svg, "akcent zostal w SVG"
    etykieta = 'role="img" aria-label="%s"' % opis.replace('"', "") if opis else 'aria-hidden="true"'
    return svg.replace("<svg ", '<svg class="%s" %s ' % (klasa, etykieta), 1)


def logo_html(kier, uid, klasa="logo", animowane=False, opis=""):
    """Logo do osadzenia w stronie: kolor liter = currentColor, akcent = var(--accent)."""
    return _do_html(logo(kier, "currentColor", AKCENT_CSS, uid=uid, litery=animowane), klasa, opis)


def logotyp_html(kier, uid, klasa="logo-s", opis=""):
    return _do_html(logotyp(kier, "currentColor", AKCENT_CSS, uid=uid), klasa, opis)


def sygnet_html(kier, uid, klasa="sg", tlo="none", fg="currentColor"):
    svg = sygnet(kier, fg, AKCENT_CSS, None if tlo == "none" else tlo, uid=uid, skala=0.62)
    return _do_html(svg, klasa, "")
