"""Etapy 6-7: dwie warstwy ofert.
Warstwa 1 "pokaz prywatny": jedna strona spinajaca znak, Instagram i landing, wysylana prospektowi na zimno.
Warstwa 2 "oferta wspolpracy": interaktywna oferta agencji na czas po rozmowie sprzedazowej.
Wynik to samodzielny folder klienci/<slug>/pokaz/ gotowy do wgrania na serwer."""
import json
import re
import shutil
from urllib.parse import urlparse

from markupsafe import Markup
from PIL import Image

from . import instagram as IG
from . import landing as LD
from . import logo as L
from . import styl
from .rdzen import agencja, folder, kierunek, nisza as wczytaj_nisze, scal, slownik, slug as na_slug, ustaw_etap, wczytaj, zapisz

OBRAZY = (".png", ".jpg", ".jpeg", ".webp")
OBCE_DOMENY = ("canva", "instagram", "facebook", "linktr", "google", "booksy", "wixsite", "bio.", "taplink")


def _sciezka_ig(p):
    """zwiad/zdjecia/x.jpg -> ig/x.jpg (pokaz jest samodzielnym folderem)."""
    return "ig/" + p.split("/")[-1] if p else ""


def _przepisz(w):
    if isinstance(w, dict):
        return {a: (_sciezka_ig(b) if a in ("img", "img_przed") and isinstance(b, str) else _przepisz(b)) for a, b in w.items()}
    if isinstance(w, list):
        return [_przepisz(x) for x in w]
    return w


def _domena(k):
    h = urlparse(k["zrodlo"].get("www") or "").hostname or ""
    h = h.replace("www.", "")
    if h and not any(o in h for o in OBCE_DOMENY):
        return h
    return na_slug(k["dane"]["nazwa"]).replace("-", "") + ".pl"


def _cena(tekst):
    c = re.sub(r"\D", "", tekst or "")
    return int(c) if c else 0


def _przyklad(t_landing, ns):
    """Przykladowe zapytanie na karcie obok landingu: najwyzej punktowane odpowiedzi z formularza."""
    wiersze, auto = [], ns["oferta"]["narzedzia"]["auta"][0][0]
    pole_auta = ""
    for kr in t_landing["formularz"]["kroki"]:
        for p in kr["pola"]:
            if p["typ"] == "tekst":
                pole_auta = pole_auta or p["etykieta"]
                continue
            naj = max(p["opcje"], key=lambda o: o[1] if len(o) > 1 else 0)
            wiersze.append([p["etykieta"], naj[0]])
    return {"auto": auto, "wiersze": wiersze, "dzialanie": t_landing["formularz"]["dzialania"]["priorytet"]}, pole_auta


def _tresci(k, ns, ig, foto):
    """Miesiac publikacji: 24 kafle wg wzoru z pakietu niszy, na zdjeciach klienta."""
    o = ns["oferta"]
    por = ig["szablony"]["karuzela"][0]["nadtytul"] if ig["szablony"]["karuzela"] else "Poradnik"
    liczniki, out, fi = {}, [], 0
    uslugi = [u["nazwa"] for u in k.get("uslugi", [])] or [u["nazwa"] for u in ns["uslugi_slownik"][:4]]
    for i, typ in enumerate(o["tresci_wzor"]):
        n = liczniki.get(typ, 0)
        liczniki[typ] = n + 1
        f = foto[fi % len(foto)] if foto else None
        if typ in ("Rolka", "Realizacja", "Przed i po") and f:
            fi += 1
            img = _sciezka_ig(f["plik"])
            if typ == "Realizacja":
                t = IG.kafel(img=img)
            elif typ == "Przed i po":
                t = IG.kafel(uklad="split", img=img, podpis=f.get("usluga") or slownik(k["nisza"])["split_podpis"])
            else:
                tytuly = o["tresci_tytuly"]["Rolka"]
                tytul = IG.z_akcentem(f["usluga"]) if f.get("usluga") else (tytuly[n % len(tytuly)] if n % 2 else IG.z_akcentem(uslugi[n % len(uslugi)]))
                t = IG.kafel(uklad="okladka", img=img, tytul=tytul, podpis=f.get("auto") or k["dane"].get("miasto", ""), etykieta="Rolka")
        else:
            tytuly = o["tresci_tytuly"].get(typ) or [IG.z_akcentem(uslugi[n % len(uslugi)])]
            tytul = tytuly[n % len(tytuly)].replace("{poradnik}", por)
            t = IG.kafel(uklad="solid" if len(out) % 2 == 0 else "ciemny", tytul=tytul, podpis=typ if typ != "Rolka" else "Proces")
        t["nazwa"] = typ
        out.append(t)
    return out


def _wizualizacje(slug, ns, cel):
    zr = folder(slug) / "branding" / "wizualizacje"
    if not zr.exists():
        return []
    opisy = {w["plik"]: w for w in ns["pokaz"]["wizualizacje"]}
    pliki = sorted(p for p in zr.iterdir() if p.suffix.lower() in OBRAZY)
    out = []
    cel.mkdir(parents=True, exist_ok=True)
    for p in pliki:
        o = opisy.get(p.stem, {})
        im = Image.open(p).convert("RGB")
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(cel / (p.stem + ".jpg"), "JPEG", quality=84, optimize=True)
        podpis = o.get("podpis") or re.sub(r"^\d+[-_ ]*", "", p.stem).replace("-", " ").capitalize()
        out.append({"img": "wiz/" + p.stem + ".jpg", "podpis": podpis, "uklad": o.get("uklad", ""), "kolejnosc": list(opisy).index(p.stem) if p.stem in opisy else 99})
    out.sort(key=lambda w: w["kolejnosc"])
    # siatka mozaiki: szerokie kafle parami, waskie czworkami
    return out


def buduj(slug):
    k = wczytaj(slug)
    kier = kierunek(k)
    strona = folder(slug) / "landing" / "strona"
    if not kier or not (strona / "index.html").exists():
        raise ValueError("Pokaz i oferta powstaja po landingu. Najpierw wybierz kierunek marki i usluge.")
    ns = wczytaj_nisze(k["nisza"])
    o_wej = LD.oferta(k)
    ustaw_etap(k, "pokaz", "w_toku")
    ustaw_etap(k, "oferta", "w_toku")
    zapisz(k)

    cel = folder(slug) / "pokaz"
    cel.mkdir(parents=True, exist_ok=True)
    for sub in ("landing", "ig", "wiz", "oferta", "branding"):
        if (cel / sub).exists():
            shutil.rmtree(cel / sub)
    shutil.copytree(strona, cel / "landing")
    # modul opcjonalny: oferta osobista dla leada, link z formularza ma dzialac tez po publikacji
    ol = folder(slug) / "oferta-leada" / "strona"
    if (cel / "oferta-leada").exists():
        shutil.rmtree(cel / "oferta-leada")
    if (k.get("oferta_leada") or {}).get("wlaczona") and (ol / "index.html").exists():
        shutil.copytree(ol, cel / "oferta-leada" / "strona")
        p = cel / "landing" / "index.html"
        p.write_text(p.read_text(encoding="utf-8").replace('href="../../oferta-leada/strona/', 'href="../oferta-leada/strona/'), encoding="utf-8")
    if k.get("tryb") == "wdrozenie":  # w pokazie formularz niczego nie wysyla i nie odpala piksela
        k_demo = dict(k, tryb="probka")
        LD.renderuj_strone(k_demo, cel / "landing")
        p = cel / "landing" / "index.html"
        p.write_text(p.read_text(encoding="utf-8").replace('href="../../oferta-leada/strona/', 'href="../oferta-leada/strona/'), encoding="utf-8")
    zr = folder(slug) / "zwiad" / "zdjecia"
    (cel / "ig").mkdir()
    if zr.exists():
        for p in zr.iterdir():
            if p.suffix.lower() in OBRAZY:
                shutil.copy2(p, cel / "ig" / p.name)
    for php in ("t.php", "akceptacja.php"):
        shutil.copy2(styl.SZABLONY / "pokaz" / php, cel / php)

    ctx = styl.kontekst(k, kier)
    kier = ctx["kier"]
    d, ag = k["dane"], agencja()
    ig = _przepisz(IG.plan(k))
    for pole in ("awatar_przed",):
        ig[pole] = _sciezka_ig(ig[pole])
    ig["siatka_przed"] = [_sciezka_ig(x) for x in ig["siatka_przed"]]
    foto = IG.zdjecia(slug)["foto"]
    akc = styl.akcenty(k, kier)
    t_landing = LD.tresc(k, o_wej)
    wiz = _wizualizacje(slug, ns, cel / "wiz")
    obrazy = sorted(p.name for p in (cel / "landing" / "img").glob("*.jpg"))
    kadry = [x for x in obrazy if x.startswith("kadr-")]
    tlo = "landing/img/" + (kadry[-1] if kadry else obrazy[0]) if obrazy else ""

    zm = {"nazwa": d["nazwa"], "nazwa_krotka": d.get("nazwa_krotka") or d["nazwa"], "miasto": d.get("miasto") or "",
          "oferta_nazwa": o_wej["nazwa"], "oferta_biernik": o_wej["fraza"]["biernik"], "oferta_mianownik": o_wej["fraza"]["mianownik"],
          "kierunek": kier["nazwa"],
          "stopka_ai": ("Film z autem na stronie" + (" i wizualizacje znaku zostały wygenerowane" if wiz else " został wygenerowany") + " komputerowo. ")
          if kadry else ("Wizualizacje znaku zostały wygenerowane komputerowo. " if wiz else "")}
    t = LD._podstaw(scal(ns["pokaz"], k["pokaz"].get("tresc") or {}), zm)
    motyw = kier["logo"].get("motyw", "refleks")
    znak = scal(t["znak"].get(motyw, t["znak"]["refleks"]), kier.get("historia_znaku") or {})
    przyklad, pole_auta = _przyklad(t_landing, ns)
    sz = ig["szablony"]
    szablony_ig = [g for g in (sz["karuzela"][:1] + sz["karuzela"][2:3] + [x for x in sz["posty"] if x["uklad"] == "podpis"][:1] + sz["karuzela"][3:4])
                   if g["img"] or g["uklad"] in ("kontakt", "solid", "ciemny", "tresc")]
    kafel_systemu = dict(sz["rolki"][0], etykieta_chip=True, dopisek=False) if sz["rolki"] else IG.kafel(uklad="solid", tytul=IG.z_akcentem(o_wej["fraza"]["mianownik"]))
    n = [0]

    def sygnet(_=None):
        n[0] += 1
        return Markup(L.sygnet_html(kier, "sg%d" % n[0], fg="var(--bone)"))

    wspolne = dict(ctx, css_akcentow=styl.css_akcentow(akc), akcenty=akc, akcenty_id=[a["id"] for a in akc], sygnet=sygnet,
                   znak_nazwa=d.get("nazwa_krotka") or d["nazwa"], oferta=o_wej,
                   logotyp_inline=Markup(L.logotyp_html(kier, "wm", "wml")),
                   logo_stat=Markup(L.logo_html(kier, "st", "logo-s", opis=d["nazwa"])))
    cfg = {"prospekt": slug, "nadawca": ag["nadawca"], "kalendarz": ag["kalendarz"], "wiadomosc": ag["wiadomosc"],
           "telefon": "", "track": "t.php", "akcenty": [a["id"] for a in akc], "pole_auta": pole_auta,
           "wideo": (cel / "wideo" / "powitanie.mp4").exists()}
    styl.renderuj(
        "pokaz/index.html", cel / "index.html", t=t, historia=znak, ig=ig, wiz=wiz, tlo=tlo, tlo_ai=bool(kadry),
        ma_zdjecia=bool(foto), szablony_ig=szablony_ig, kafel_systemu=kafel_systemu, przyklad=przyklad,
        www=re.sub(r"^https?://", "", k["zrodlo"].get("www") or "").strip("/"),
        adres_strony="%s/%s" % (_domena(k), na_slug(o_wej["fraza"]["mianownik"])),
        cta_landingu=t_landing["nav_cta"], logo_anim=Markup(L.logo_html(kier, "an", "logo", animowane=True, opis=d["nazwa"])),
        cfg_json=json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"), **wspolne)

    # ---- warstwa 2
    o = LD._podstaw(scal(scal(ns["oferta"], ag.get("oferta") or {}), k["oferta"].get("tresc") or {}), zm)
    ok = k["oferta"]
    cele = ok.get("cele") or o["cele_przykladowe"]
    polecany = ok.get("polecany") or o["polecany"]
    rolki = [f for f in foto if f.get("format") == "rolka"] or foto
    auta = [f["auto"] for f in foto if f.get("auto")]
    zakresy = [[p["nazwa"], p.get("etykieta", ""), _cena(p["cena"])] for p in t_landing["pakiety"]["lista"]]
    narz = dict(o["narzedzia"], domena=_domena(k), oferta=o_wej["nazwa"], zakresy=zakresy,
                auto_glowne=auta[0] if auta else o["narzedzia"]["auta"][0][0],
                usluga_glowna=(rolki[0].get("usluga") if rolki and rolki[0].get("usluga") else o_wej["nazwa"]),
                zdjecia=[_sciezka_ig(f["plik"]) for f in foto[:4]], numer="%s-2026-0142" % (kier["logo"].get("monogram") or d["nazwa"][:2]).upper())
    if auta:
        narz["auta"] = [[a, o["narzedzia"]["auta"][i % 4][1]] for i, a in enumerate((auta * 4)[:4])]
    cfg2 = {"klient": slug, "dla": d["nazwa"], "rozmowa": ok.get("rozmowa", ""), "wazna_do": ok.get("wazna_do", ""),
            "start": o["start"], "nadawca": ag["nadawca"], "polecany": polecany, "akceptacja": "../akceptacja.php",
            "platnosc": ok.get("platnosc") or {}, "cele": cele, "intro": o["intro"], "probka": ctx["probka"],
            "pakiety": o["pakiety"], "dodatki": o["dodatki"], "mapa": o["mapa"], "zasady": o["zasady"],
            "start_14": o["start_14"], "narzedzia": narz}
    kafle = sorted(x for x in obrazy if x.startswith("kadr-"))
    styl.renderuj(
        "pokaz/oferta.html", cel / "oferta" / "index.html", o=o, tresci=_tresci(k, ns, ig, foto),
        cele_przykladowe=not ok.get("cele"), foto_ig=_sciezka_ig(rolki[0]["duzy"]) if rolki else "",
        foto_strony="landing/img/" + (kafle[min(3, len(kafle) - 1)] if kafle else obrazy[0]) if obrazy else "",
        logo_go=Markup(L.logo_html(kier, "go", "logo-s", opis=d["nazwa"])),
        cfg_json=json.dumps(cfg2, ensure_ascii=False).replace("</", "<\\/"), **wspolne)

    k = wczytaj(slug)
    ustaw_etap(k, "pokaz", "gotowe", "%d scen, %d wizualizacji" % (7 if len(akc) > 1 else 6, len(wiz)))
    ustaw_etap(k, "oferta", "gotowe", "cele przykladowe" if not ok.get("cele") else "cele klienta: %d" % len(ok["cele"]))
    zapisz(k)
    return cel / "index.html"
