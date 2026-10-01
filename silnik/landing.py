"""Etap 5: landing pod jedna oferte wejsciowa. Tresc z pakietu niszowego + nadpisania klienta, styl z kierunku brandingu."""
import json
import re
import shutil

from PIL import Image

from markupsafe import Markup

from . import instagram as IG
from . import logo as L
from . import styl
from .rdzen import folder, kierunek, nisza as wczytaj_nisze, scal, slownik, ustaw_etap, wczytaj, zapisz

OBRAZY = (".png", ".jpg", ".jpeg", ".webp")


def oferta(k, oid=None):
    oid = oid or k["landing"].get("oferta_id")
    for o in wczytaj_nisze(k["nisza"])["oferty_wejsciowe"]:
        if o["id"] == oid:
            return o
    raise ValueError("Nie ma oferty wejsciowej '%s' w pakiecie niszy '%s'." % (oid, k["nisza"]))


def kandydaci(k):
    """Oferty wejsciowe posortowane wg dopasowania do uslug klienta. Pierwsza = rekomendacja."""
    ns = wczytaj_nisze(k["nisza"])
    sl = slownik(k["nisza"])
    ma = {u.get("id"): u for u in k.get("uslugi", [])}
    nazwy = {u["id"]: u["nazwa"] for u in ns["uslugi_slownik"]}
    out = []
    for o in ns["oferty_wejsciowe"]:
        trafione = [u for u in o["dla_uslug"] if u in ma]
        dalej = [u for u in o["prowadzi_do"] if u in ma]
        premium = [u for u in dalej if ma[u].get("typ") == "premium"]
        punkty = 3 * len(trafione) + 2 * len(premium) + len(dalej)
        if trafione:
            powod = "%s ma w ofercie: %s." % (sl["firma"].capitalize(), ", ".join(ma[u]["nazwa"] for u in trafione))
        else:
            powod = "%s nie pokazuje tej usługi na profilu. Do potwierdzenia, czy ją wykonuje." % sl["firma"].capitalize()
        if dalej:
            powod += " Naturalny kolejny krok: %s." % ", ".join(ma[u]["nazwa"] for u in dalej)
        out.append({"id": o["id"], "nazwa": o["nazwa"], "krotko": o["krotko"], "cena_tekst": o["cena_tekst"],
                    "czas": o["czas"], "dlaczego": o["dlaczego"], "dopasowanie": powod, "punkty": punkty,
                    "prowadzi_do": [nazwy.get(u, u) for u in o["prowadzi_do"]], "pasuje": bool(trafione)})
    out.sort(key=lambda x: -x["punkty"])
    if out:
        out[0]["rekomendowana"] = True
    return out


def _podstaw(w, zm):
    if isinstance(w, str):
        return re.sub(r"\{(\w+)\}", lambda m: str(zm.get(m.group(1), m.group(0))), w)
    if isinstance(w, list):
        return [_podstaw(x, zm) for x in w]
    if isinstance(w, dict):
        return {a: _podstaw(b, zm) for a, b in w.items()}
    return w


def tresc(k, o):
    d = k["dane"]
    t = scal(o["tresc"], k["landing"].get("tresc") or {})
    zm = {"nazwa": d["nazwa"], "nazwa_krotka": d.get("nazwa_krotka") or d["nazwa"], "miasto": d.get("miasto") or "",
          "telefon": d.get("telefon") or "", "liczba_opinii": d.get("liczba_opinii") or "",
          "cena_tekst": k["landing"].get("cena_tekst") or o["cena_tekst"]}
    t = _podstaw(t, zm)
    # bez miasta nie zostawiamy osieroconych separatorow
    for pole in ("title", "eyebrow", "opis_meta"):
        t[pole] = re.sub(r"\s*[,/]\s*$", "", re.sub(r"\s{2,}", " ", t[pole].replace(" .", "."))).strip()
    for s in t["sceny"]:
        s.setdefault("podpis", "")
        s.setdefault("cta", [])
    for p in t["pakiety"]["lista"]:
        p.setdefault("wyrozniony", False)
        p.setdefault("przed_cena", "")
        p.setdefault("etykieta", "")
    for kr in t["formularz"]["kroki"]:
        for p in kr["pola"]:
            p.setdefault("przyklad", "")
    return t


def _jpg(zrodlo, cel, szer=1600, jakosc=82):
    im = Image.open(zrodlo).convert("RGB")
    if im.width > szer:
        im = im.resize((szer, round(im.height * szer / im.width)), Image.LANCZOS)
    cel.parent.mkdir(parents=True, exist_ok=True)
    im.save(cel, "JPEG", quality=jakosc, optimize=True)


def _film(slug, strona, ile_scen, foto):
    """Ustala zrodlo obrazu dla sceny przewijanej: klatki wideo > kadry AI > zdjecia klienta."""
    baza = folder(slug) / "landing"
    klatki = sorted((strona / "frames").glob("f*.webp")) if (strona / "frames").exists() else []
    kadry_src = sorted(p for p in (baza / "kadry").glob("*") if p.suffix.lower() in OBRAZY) if (baza / "kadry").exists() else []
    kadry = []
    for i, p in enumerate(kadry_src[:ile_scen], 1):
        cel = strona / "img" / ("kadr-%02d.jpg" % i)
        _jpg(p, cel)
        kadry.append("img/" + cel.name)
    if len(klatki) >= ile_scen * 8:
        return {"tryb": "klatki", "pliki": ["frames/" + p.name for p in klatki], "ai": True}, kadry
    if len(kadry) == ile_scen:
        return {"tryb": "kadry", "pliki": kadry, "ai": True}, kadry
    if foto:
        pliki = []
        for i in range(ile_scen):
            z = foto[i % len(foto)]
            cel = strona / "img" / ("scena-%02d.jpg" % (i + 1))
            _jpg(folder(slug) / "zwiad" / z["duzy"], cel)
            pliki.append("img/" + cel.name)
        return {"tryb": "zdjecia", "pliki": pliki, "ai": False}, pliki
    raise ValueError("Landing potrzebuje obrazow: wgraj zdjecia do zwiad/zdjecia/ albo kadry do landing/kadry/.")


def buduj(slug, oid=None):
    k = wczytaj(slug)
    kier = kierunek(k)
    if not kier:
        raise ValueError("Najpierw wybierz kierunek brandingu.")
    if oid:
        k["landing"]["oferta_id"] = oid
    o = oferta(k)
    ustaw_etap(k, "landing", "w_toku", o["nazwa"])
    zapisz(k)

    t = tresc(k, o)
    baza = folder(slug) / "landing"
    strona = baza / "strona"
    (strona / "img").mkdir(parents=True, exist_ok=True)

    z = IG.zdjecia(slug)
    # w tle scen najlepiej wygladaja duze pliki, najpierw te z opisem auta
    foto = sorted(z["foto"], key=lambda f: (f.get("format") != "post", not f.get("auto")))
    film, obrazy = _film(slug, strona, len(t["sceny"]), foto)
    film["pierwszy"] = film["pliki"][0]

    for i, kr in enumerate(t["proces"]["kroki"]):
        nr = kr.get("kadr", i + 1)
        kr["img"] = obrazy[(nr - 1) % len(obrazy)] if obrazy else ""

    real = []
    (strona / "img" / "real").mkdir(exist_ok=True)
    for f in [x for x in foto if x.get("format") != "rolka" or x.get("auto")][:6]:
        nazwa = f["duzy"].split("/")[-1].rsplit(".", 1)[0] + ".jpg"
        _jpg(folder(slug) / "zwiad" / f["duzy"], strona / "img" / "real" / nazwa, 900)
        real.append({"img": "img/real/" + nazwa, "auto": f.get("auto", ""),
                     "usluga": IG.z_akcentem(f["usluga"]) if f.get("usluga") else ""})

    logo_kat = strona / "img" / "logo"
    if logo_kat.exists():
        shutil.rmtree(logo_kat)
    shutil.copytree(folder(slug) / "branding" / "final", logo_kat)

    _render(k, kier, o, t, film, real, strona)

    k = wczytaj(slug)
    k["landing"]["film"] = {"tryb": film["tryb"], "klatki": len(film["pliki"])}
    ustaw_etap(k, "usluga", "gotowe", o["nazwa"])
    ustaw_etap(k, "landing", "gotowe", "tryb obrazu: " + film["tryb"])
    if k["etapy"].get("pokaz") in ("czeka", "gotowe", "blad"):
        ustaw_etap(k, "pokaz", "w_kolejce", "landing gotowy, pora na dwie warstwy ofert")
    if k.get("tryb") == "wdrozenie":
        braki = braki_wdrozenia(k)
        ustaw_etap(k, "wdrozenie", "decyzja" if braki else "gotowe", "; ".join(braki))
    zapisz(k)
    return strona / "index.html"


def _render(k, kier, o, t, film, real, strona):
    ctx = styl.kontekst(k, kier)
    d = k["dane"]
    ocena = ""
    if d.get("ocena_google") and d.get("liczba_opinii"):
        ocena = ("%.1f" % float(d["ocena_google"])).replace(".", ",")
    akc = styl.akcenty(k, ctx["kier"])
    cfg = {
        "film": {"tryb": film["tryb"], "pliki": film["pliki"]},
        "sceny": len(t["sceny"]), "kroki": t["formularz"]["kroki"], "prog": t["formularz"]["prog_priorytetu"],
        "dzialania": t["formularz"]["dzialania"], "oferta": o["nazwa"], "studio": d["nazwa"],
        "telefon": d.get("telefon", ""), "endpoint": "" if ctx["probka"] else k["landing"].get("formularz_endpoint", ""),
    }
    styl.renderuj(
        "landing/index.html", strona / "index.html", t=t, oferta=o, film=film, realizacje=real, ocena=ocena,
        demo=not cfg["endpoint"],
        link_opinie=k["zrodlo"].get("google") or "https://www.google.com/search?q=" + re.sub(r"\s+", "+", "%s %s opinie" % (d["nazwa"], d.get("miasto", ""))),
        logo_nav=Markup(L.logotyp_html(ctx["kier"], "n", "lg", d["nazwa"])),
        logo_stopka=Markup(L.logotyp_html(ctx["kier"], "f", "lg", d["nazwa"])),
        css_akcentow=styl.css_akcentow(akc), akcenty_id=[a["id"] for a in akc],
        piksel="" if ctx["probka"] else k["landing"].get("piksel_meta", ""),
        cfg_json=json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"), **ctx)



def renderuj_strone(k, strona):
    """Sklada index.html jeszcze raz z plikow, ktore juz leza w folderze strony (bez kopiowania obrazow)."""
    kier = kierunek(k)
    o = oferta(k)
    t = tresc(k, o)
    klatki = sorted((strona / "frames").glob("f*.webp")) if (strona / "frames").exists() else []
    kadry = sorted(p.name for p in (strona / "img").glob("kadr-*.jpg"))
    sceny = sorted(p.name for p in (strona / "img").glob("scena-*.jpg"))
    if len(klatki) >= len(t["sceny"]) * 8:
        film = {"tryb": "klatki", "pliki": ["frames/" + p.name for p in klatki], "ai": True}
    elif len(kadry) == len(t["sceny"]):
        film = {"tryb": "kadry", "pliki": ["img/" + x for x in kadry], "ai": True}
    else:
        film = {"tryb": "zdjecia", "pliki": ["img/" + x for x in sceny], "ai": False}
    film["pierwszy"] = film["pliki"][0]
    obrazy = ["img/" + x for x in (kadry or sceny)]
    for i, kr in enumerate(t["proces"]["kroki"]):
        kr["img"] = obrazy[(kr.get("kadr", i + 1) - 1) % len(obrazy)] if obrazy else ""
    foto = {f["duzy"].split("/")[-1].rsplit(".", 1)[0]: f for f in IG.zdjecia(k["slug"])["foto"]}
    real = []
    for p in sorted((strona / "img" / "real").glob("*.jpg")):
        f = foto.get(p.stem, {})
        real.append({"img": "img/real/" + p.name, "auto": f.get("auto", ""),
                     "usluga": IG.z_akcentem(f["usluga"]) if f.get("usluga") else ""})
    _render(k, kier, o, t, film, real, strona)


def braki_wdrozenia(k):
    """Czego brakuje, zeby landing mogl isc pod kampanie."""
    b = []
    d = k["dane"]
    for pole in ("telefon", "adres", "miasto"):
        if not d.get(pole):
            b.append("brak pola: " + pole)
    for pole, stan in k.get("pewnosc", {}).items():
        if stan == "zgadniete" and d.get(pole) not in (None, ""):
            b.append("niepotwierdzone: " + pole)
    if not (k["landing"].get("tresc") or {}).get("pakiety"):
        b.append("ceny pakietow sa orientacyjne, potwierdz cennik klienta")
    if not k["landing"].get("formularz_endpoint"):
        b.append("brak adresu odbioru formularza (formularz_endpoint)")
    if not k["landing"].get("piksel_meta"):
        b.append("brak identyfikatora piksela Meta")
    return b
