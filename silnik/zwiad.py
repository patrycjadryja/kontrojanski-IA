"""Etap 1: zwiad. Czesc automatyczna: publiczne metadane profilu na Instagramie i wstepna mapa uslug.
Reszte (adres, telefon, oceny Google, zdjecia realizacji, diagnoza) uzupelnia Claude wg instrukcji w skillu."""
import html
import json
import re
import urllib.request

from .rdzen import dziennik, folder, nisza as wczytaj_nisze, wczytaj, zapisz

UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"


def _meta(strona, nazwa):
    m = re.search(r'<meta[^>]+property="og:%s"[^>]+content="([^"]*)"' % nazwa, strona) or \
        re.search(r'<meta[^>]+content="([^"]*)"[^>]+property="og:%s"' % nazwa, strona)
    return html.unescape(m.group(1)) if m else ""


def _liczba(t):
    t = t.strip().replace(",", "").replace(" ", "").replace(" ", "")
    mn = 1
    if t[-1:].upper() == "K":
        mn, t = 1000, t[:-1]
    elif t[-1:].upper() == "M":
        mn, t = 1000000, t[:-1]
    try:
        return int(float(t) * mn)
    except ValueError:
        return None


def mapuj_uslugi(tekst, nazwa_niszy):
    """Wstepna mapa uslug: slowa kluczowe ze slownika niszy znalezione w tekscie."""
    t = tekst.lower()
    out = []
    for u in wczytaj_nisze(nazwa_niszy)["uslugi_slownik"]:
        if any(s in t for s in u["slowa"]):
            out.append({"id": u["id"], "nazwa": u["nazwa"], "typ": u["typ"], "zrodlo": "opis profilu (automat)",
                        "cena": "", "uwagi": ""})
    return out


def instagram(slug):
    """Pobiera publiczne metadane profilu. Instagram bywa kaprysny, dlatego brak danych nie jest bledem."""
    k = wczytaj(slug)
    url = k["zrodlo"].get("instagram")
    if not url:
        return {"ok": False, "powod": "klient nie ma linku do Instagrama"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8"})
        strona = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
    except Exception as e:
        dziennik(k, "zwiad: Instagram nie odpowiedzial (%s)" % e)
        zapisz(k)
        return {"ok": False, "powod": str(e)}
    og = {n: _meta(strona, n) for n in ("title", "description", "image")}
    kat = folder(slug) / "zwiad"
    kat.mkdir(parents=True, exist_ok=True)
    (kat / "og.json").write_text(json.dumps(og, ensure_ascii=False, indent=1), encoding="utf-8")
    d, p = k["dane"], k.setdefault("pewnosc", {})
    m = re.match(r"\s*(.+?)\s*\(@", og["title"])
    if m and m.group(1):
        wysw = m.group(1).strip()
        # nazwa wyswietlana bywa lista uslug ("Detailing • PPF • Miasto"), wtedy to kategorie, nie nazwa firmy
        if "•" in wysw or "|" in wysw or len(wysw) > 40:
            d["kategorie"] = wysw
            p["kategorie"] = "odczytane"
        else:
            d["nazwa"] = wysw
            p["nazwa"] = "odczytane"
    opis = og["description"]
    L = r"([\d.,\s\u00a0]*\d\s?(?:[KkMm]|tys\.|mln)?)"
    for wzory, pole in (((L + r"\s+Followers", r"Obserwuj\w+:\s*" + L), "obserwujacy"),
                        ((L + r"\s+Posts", r"posty:\s*" + L), "posty")):
        for wzor in wzory:
            m = re.search(wzor, opis)
            if m and _liczba(m.group(1)) is not None:
                d[pole] = _liczba(m.group(1))
                p[pole] = "odczytane"
                break
    m = re.search(r'on Instagram: "(.*)"\s*$', opis, re.S) or re.search(r'na Instagramie: [„"](.*)["”]\s*$', opis, re.S)
    if m:
        d["bio"] = m.group(1).strip()
        p["bio"] = "odczytane"
    if og["image"]:
        try:
            req = urllib.request.Request(og["image"], headers={"User-Agent": UA})
            (kat / "zdjecia").mkdir(exist_ok=True)
            (kat / "zdjecia" / "awatar.jpg").write_bytes(urllib.request.urlopen(req, timeout=25).read())
        except Exception:
            pass
    if not k.get("uslugi"):
        k["uslugi"] = mapuj_uslugi(" ".join([d.get("bio") or "", d.get("kategorie") or "", d["nazwa"]]), k["nisza"])
    dziennik(k, "zwiad: metadane Instagrama %s" % ("odczytane" if og["title"] else "puste"))
    zapisz(k)
    return {"ok": bool(og["title"]), "og": og, "uslugi": [u["nazwa"] for u in k["uslugi"]]}
