"""Etap 3: redesign Instagrama. Plan siatki, strona propozycji i eksport grafik PNG w stylu wybranego kierunku."""
import json
import re
import shutil

from . import chrome, styl
from .rdzen import folder, kierunek, nisza as wczytaj_nisze, slownik, ustaw_etap, wczytaj, zapisz

ROZSZ = (".jpg", ".jpeg", ".png", ".webp")
KAFEL = {"uklad": "foto", "img": "", "alt": "", "tytul": "", "podpis": "", "etykieta": "", "etykieta_chip": False,
         "nadtytul": "", "tresc": "", "licznik": "", "dopisek": False, "linie": [], "nazwa": "", "opis": "", "plik": ""}
STYLE_OKLADEK = ["s", "o", "p", "rp", "o", "p", "s", "p", "o"]
EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿️‍]+")


def kafel(**kw):
    t = dict(KAFEL)
    t.update(kw)
    return t


def z_akcentem(nazwa):
    """Ostatnie slowo nazwy w kolorze akcentu: 'Folia PPF' -> 'Folia *PPF*'."""
    if "*" in nazwa:
        return nazwa
    s = nazwa.strip().split()
    if len(s) < 2:
        return "*%s*" % nazwa.strip()
    return " ".join(s[:-1]) + " *" + s[-1] + "*"


def zdjecia(slug):
    """Czyta zwiad/zdjecia.json, a gdy go nie ma, buduje liste z plikow w zwiad/zdjecia/."""
    baza = folder(slug) / "zwiad"
    p = baza / "zdjecia.json"
    z = {"awatar_przed": "", "siatka_przed": [], "wyroznione_przed": [], "foto": []}
    if p.exists():
        z.update(json.loads(p.read_text(encoding="utf-8")))
    else:
        kat = baza / "zdjecia"
        if kat.exists():
            for f in sorted(kat.iterdir()):
                if f.suffix.lower() in ROZSZ:
                    if f.stem.lower() in ("awatar", "avatar", "profil"):
                        z["awatar_przed"] = "zdjecia/" + f.name
                    else:
                        z["foto"].append({"plik": "zdjecia/" + f.name})
    for f in z["foto"]:
        f.setdefault("duzy", f["plik"])
        f.setdefault("auto", "")
        f.setdefault("usluga", "")
    # sciezki w zdjecia.json sa wzgledem folderu zwiad/
    return z


def _skrot(nazwa, slownik):
    n = nazwa.lower()
    for u in slownik:
        if any(s in n for s in u["slowa"]) or u["nazwa"].lower() == n:
            return u["skrot"], u["id"]
    pierwsze = re.sub(r"[^\w/]", "", nazwa.split()[0]) if nazwa.split() else nazwa
    return pierwsze[:8], ""


def _usluga_glowna(k, slownik):
    """Usluga premium klienta, na ktorej opieramy przyklady w szablonach."""
    for typ in ("premium", "srednia", "wejsciowa"):
        for u in k.get("uslugi", []):
            if u.get("typ") == typ:
                return u
    return {"id": "", "nazwa": slownik[0]["nazwa"], "typ": "premium"}


def plan(k):
    """Buduje kompletny opis redesignu. To, co Claude wpisal w klient.json, ma pierwszenstwo."""
    ns = wczytaj_nisze(k["nisza"])
    sl = slownik(k["nisza"])
    slownik_uslug = ns["uslugi_slownik"]
    d = k["dane"]
    z = zdjecia(k["slug"])
    P = lambda s: ("zwiad/" + s) if s else ""
    foto = z["foto"]
    ile = len(foto)

    def f(i):
        return foto[i % ile] if ile else {"plik": "", "duzy": "", "auto": "", "usluga": ""}

    glowna = _usluga_glowna(k, slownik_uslug)
    uslugi = [u["nazwa"] for u in k.get("uslugi", [])] or [u["nazwa"] for u in slownik_uslug[:6]]
    druga = uslugi[1] if len(uslugi) > 1 else uslugi[0]

    # wyroznione relacje: obecne nazwy klienta albo jego uslugi
    zrodlo = z["wyroznione_przed"] or [{"nazwa": n, "plik": ""} for n in uslugi]
    wyr = []
    for i, w in enumerate(zrodlo[:9]):
        sk, _ = _skrot(w["nazwa"], slownik_uslug)
        st = STYLE_OKLADEK[i % len(STYLE_OKLADEK)]
        if st == "p" and not ile:
            st = "o"
        wyr.append({"nazwa": w["nazwa"], "skrot": w.get("skrot") or sk, "styl": st,
                    "img": P(f(i)["plik"]) if st == "p" else "", "img_przed": P(w.get("plik", ""))})

    por = ns["instagram"]["poradniki"]
    por = por.get(glowna.get("id") or "", por["domyslny"])
    podpis = lambda i: f(i)["auto"] or d.get("miasto") or d["nazwa"]
    tytul = lambda i, zapas: z_akcentem(f(i)["usluga"] or zapas)

    siatka = [
        kafel(uklad="okladka", img=P(f(0)["plik"]), tytul=tytul(0, glowna["nazwa"]), podpis=podpis(0), etykieta="Rolka"),
        kafel(img=P(f(1)["plik"])),
        kafel(uklad="solid", tytul=por["tytul"], podpis="Poradnik"),
        kafel(img=P(f(2)["plik"])),
        kafel(uklad="okladka", img=P(f(3)["plik"]), tytul=tytul(3, druga), podpis=podpis(3), etykieta="Rolka"),
        kafel(img=P(f(4)["plik"])),
        kafel(img=P(f(5)["plik"])),
        kafel(img=P(f(6)["plik"])),
        kafel(uklad="split", img=P(f(7)["plik"]), podpis=sl["split_podpis"]),
        kafel(uklad="ciemny", tytul=z_akcentem(uslugi[2] if len(uslugi) > 2 else druga), podpis="Jak wygląda proces"),
        kafel(img=P(f(8)["plik"])),
        kafel(img=P(f(9)["plik"])),
    ]
    if not ile:  # bez zdjec kafle fotograficzne staja sie typograficzne
        for i, t in enumerate(siatka):
            if t["uklad"] in ("foto", "split"):
                siatka[i] = kafel(uklad="ciemny", tytul=z_akcentem(uslugi[i % len(uslugi)]), podpis=d.get("miasto", ""))

    pion = [x for x in foto if x.get("format") == "rolka"] or foto
    poziom = [x for x in foto if x.get("format") == "post"] or foto
    # druga okladka rolki ma pokazac inna usluge niz pierwsza
    if len(pion) > 1:
        inne = [x for x in pion[1:] if (x.get("usluga") or "") != (pion[0].get("usluga") or "")]
        pion = [pion[0]] + inne + [x for x in pion[1:] if x not in inne]
    pf = lambda lista, i: lista[i % len(lista)] if lista else f(0)
    tytul2 = pf(pion, 1)["usluga"] if pf(pion, 1)["usluga"] and pf(pion, 1)["usluga"] != pf(pion, 0)["usluga"] else \
        (druga if druga != (pf(pion, 0)["usluga"] or glowna["nazwa"]) else uslugi[-1])
    kontakt = [x for x in (d.get("telefon"), d.get("miasto")) if x]

    szablony = {
        "rolki": [
            kafel(uklad="okladka", img=P(pf(pion, 0)["duzy"]), tytul=z_akcentem(pf(pion, 0)["usluga"] or glowna["nazwa"]),
                  podpis=pf(pion, 0)["auto"] or d.get("miasto", ""), etykieta="Rolka", dopisek=True, plik="rolka-realizacja",
                  nazwa="Okładka rolki, realizacja", opis="1080 x 1920 px. Tytuł to nazwa usługi, linia pod spodem to %s." % sl["realizacja_opis"]),
            kafel(uklad="okladka", img=P(pf(pion, 1)["duzy"]), tytul=z_akcentem(tytul2),
                  podpis=pf(pion, 1)["auto"] or d.get("miasto", ""), etykieta="Proces", etykieta_chip=True, dopisek=True, plik="rolka-proces",
                  nazwa="Okładka rolki, proces", opis="Ten sam układ. Etykieta w rogu odróżnia kulisy pracy od gotowych realizacji."),
        ],
        "posty": [
            kafel(uklad="podpis", img=P(pf(poziom, 0)["duzy"]), plik="post-podpis-realizacji",
                  podpis=" / ".join(x for x in (pf(poziom, 0)["auto"], pf(poziom, 0)["usluga"] or glowna["nazwa"]) if x),
                  nazwa="Podpis realizacji", opis="1080 x 1350 px. Najlżejsza nakładka: model, usługa i znak. Zdjęcie zostaje bohaterem."),
            kafel(uklad="foto", img=P(pf(poziom, 1)["duzy"]), plik="post-zdjecie",
                  nazwa="Zdjęcie bez nakładki", opis="Większość postów. Łączy je tylko wspólna obróbka kolorów."),
            kafel(uklad="solid", tytul=por["tytul"], podpis="Poradnik", plik="post-okladka-poradnik",
                  nazwa="Okładka poradnika", opis="Pełny kolor akcentu. Najwyżej jedna taka grafika na rząd siatki."),
            kafel(uklad="ciemny", tytul=z_akcentem(uslugi[2] if len(uslugi) > 2 else druga), podpis="Jak wygląda proces", plik="post-okladka-proces",
                  nazwa="Okładka na ciemnym tle", opis="Wersja spokojniejsza, na zmianę z okładką w kolorze akcentu."),
        ],
        "karuzela": [
            kafel(uklad="tytulowy", img=P(pf(poziom, 2)["duzy"]), nadtytul=por["tytul"], tytul=por["obietnica"], licznik="1 / 4", dopisek=True,
                  plik="karuzela-1-tytul", nazwa="Slajd tytułowy", opis="Zdjęcie %s i jedna obietnica." % sl["obiektu"]),
            kafel(uklad="tresc", tresc=por["tresc"], podpis=por["wniosek"], licznik="2 / 4", plik="karuzela-2-tresc",
                  nazwa="Slajd z treścią", opis="Ciemne tło, jedna myśl na slajd, duży tekst."),
            kafel(uklad="split", img=P(pf(poziom, 3)["duzy"]), licznik="3 / 4", plik="karuzela-3-przed-po",
                  nazwa="Slajd przed i po", opis="Podgląd układu. Docelowo lewa połowa to zdjęcie przed pracą."),
            kafel(uklad="kontakt", tytul="Umów termin", linie=kontakt, licznik="4 / 4", dopisek=True, plik="karuzela-4-kontakt",
                  nazwa="Slajd kontaktowy", opis="Jedyny slajd w pełnym kolorze akcentu, zamyka każdą karuzelę."),
        ],
    }
    if not ile:
        szablony["posty"] = [g for g in szablony["posty"] if not g["uklad"] in ("podpis", "foto")]

    bio = [l.strip() for l in (d.get("bio") or "").split("\n") if l.strip()]
    uwagi = ["Zdjęcia pochodzą z publicznych materiałów %s, więc mają obniżoną jakość. Do finalnych plików potrzebne są zdjęcia źródłowe." % sl["firmy"]] if ile else \
        ["Propozycja pokazuje układ bez zdjęć. " + sl["brak_zdjec"]]
    auto = {
        "haslo": ns["instagram"]["haslo"], "lead": ns["instagram"]["lead"],
        "diagnoza": k.get("diagnoza", {}).get("feed") or ns["instagram"]["diagnoza_typowa"],
        "diagnoza_lead": k.get("diagnoza", {}).get("podsumowanie") or "Zdjęcia są mocną stroną profilu. Tanio wygląda to, co jest na nie nałożone i wokół nich.",
        "awatar_przed": P(z["awatar_przed"]), "prawdziwa_siatka": bool(z["siatka_przed"]),
        "siatka_przed": [P(x) for x in z["siatka_przed"]] or [P(x["plik"]) for x in foto[:12]],
        "bio_przed": bio, "bio_po": [x for x in (EMOJI.sub("", l).strip() for l in bio) if x],
        "wyroznione": wyr, "siatka_po": siatka, "szablony": szablony,
        "probka_typografii": z_akcentem(glowna["nazwa"]), "uwagi": " ".join(uwagi),
    }
    reczne = k.get("instagram") or {}
    out = dict(auto)
    for kl, w in reczne.items():
        if w not in (None, "", [], {}):
            out[kl] = w
    # kafle wpisane recznie moga miec tylko czesc pol
    out["siatka_po"] = [kafel(**t) for t in out["siatka_po"]]
    out["szablony"] = {g: [kafel(**t) for t in out["szablony"].get(g, [])] for g in ("rolki", "posty", "karuzela")}
    return out


def _grafika(env_ctx, cel_html, cel_png, szer, wys, **dane):
    styl.renderuj("instagram/grafika.html", cel_html, szer=szer, wys=wys, **dict(env_ctx, **dane))
    chrome.zrzut(cel_html, cel_png, szer, wys, przezroczyste=dane.get("nakladka", False), budzet_ms=4000)


def buduj(slug, eksport=True):
    k = wczytaj(slug)
    kier = kierunek(k)
    if not kier:
        raise ValueError("Najpierw wybierz kierunek brandingu.")
    if not (folder(slug) / "branding" / "final" / "logotyp-jasny.svg").exists():
        raise ValueError("Brak plikow logo. Uruchom najpierw: branding final.")
    ustaw_etap(k, "instagram", "w_toku")
    zapisz(k)
    ig = plan(k)
    baza = folder(slug) / "instagram"
    ctx = styl.kontekst(k, kier)
    styl.renderuj("instagram/propozycja.html", baza / "propozycja.html", ig=ig, baza="../", **ctx)

    ile = 0
    if eksport:
        paczka = baza / "paczka"
        if paczka.exists():
            shutil.rmtree(paczka)
        rob = baza / "_render"
        rob.mkdir(parents=True, exist_ok=True)
        g = dict(ctx, baza="../../")
        zadania = []
        for t in ig["szablony"]["rolki"]:
            zadania.append(("02-okladki-rolek", t["plik"], 1080, 1920, dict(t=t, format="r916", rodzaj="kafel", nakladka=False)))
            zadania.append(("05-nakladki-przezroczyste", "nakladka-" + t["plik"], 1080, 1920, dict(t=t, format="r916", rodzaj="kafel", nakladka=True)))
        for t in ig["szablony"]["posty"] + ig["szablony"]["karuzela"]:
            zadania.append(("03-posty-i-karuzela", t["plik"], 1080, 1350, dict(t=t, format="r45", rodzaj="kafel", nakladka=False)))
            if t["uklad"] in ("podpis", "tytulowy", "split"):
                zadania.append(("05-nakladki-przezroczyste", "nakladka-" + t["plik"], 1080, 1350, dict(t=t, format="r45", rodzaj="kafel", nakladka=True)))
        for i, w in enumerate(ig["wyroznione"], 1):
            from .rdzen import slug as na_slug
            zadania.append(("04-okladki-wyroznionych", "%02d-%s" % (i, na_slug(w["nazwa"])), 1080, 1080, dict(t=w, format="", rodzaj="okladka", nakladka=False)))
        for kat, nazwa, szer, wys, dane in zadania:
            _grafika(g, rob / (nazwa + ".html"), paczka / kat / (nazwa + ".png"), szer, wys, **dane)
            ile += 1
        shutil.rmtree(rob)
        # podglad przed i po: gorna czesc strony propozycji
        try:
            chrome.zrzut(baza / "propozycja.html", paczka / "01-podglad-przed-i-po" / "feed-przed-i-po.png", 1180, 1500, budzet_ms=6000)
            ile += 1
        except RuntimeError:
            pass
        kat_logo = paczka / "00-logo"
        shutil.copytree(folder(slug) / "branding" / "final", kat_logo)
        _czytaj(k, kier, ctx, paczka)
        shutil.make_archive(str(baza / ("%s-instagram" % slug)), "zip", str(paczka))

    k = wczytaj(slug)
    ustaw_etap(k, "instagram", "gotowe", "%d grafik" % ile if eksport else "sama strona propozycji")
    if k["etapy"].get("usluga") in ("czeka", None):
        ustaw_etap(k, "usluga", "decyzja", "wybierz oferte wejsciowa")
    zapisz(k)
    return baza / "propozycja.html"


def _czytaj(k, kier, ctx, paczka):
    t, f = kier["tokeny"], ctx["fonty"]
    txt = """%s - PACZKA GRAFIK NA INSTAGRAM
Propozycja, kierunek: %s

ZAWARTOSC
00-logo                    pliki logo (SVG) i zdjecie profilowe (PNG)
01-podglad-przed-i-po      porownanie profilu: stan obecny i propozycja
02-okladki-rolek           okladki rolek, 1080 x 1920 px
03-posty-i-karuzela        posty i 4 slajdy karuzeli, 1080 x 1350 px
04-okladki-wyroznionych    okladki wyroznionych relacji, 1080 x 1080 px
05-nakladki-przezroczyste  same nakladki (PNG z przezroczystym tlem) do nalozenia na wlasne zdjecie

JAK UZYWAC NAKLADEK
Nakladke kladziemy jako gorna warstwe na zdjeciu w tym samym formacie.
Przyciemnienie gory i dolu kadru jest juz w pliku, dzieki temu tekst zostaje czytelny.
Teksty w nakladkach sa przykladowe. Inna realizacja lub inna usluga wymaga nowego eksportu.

ZASADY
- Tekst trzymamy w srodkowym polu 3:4, bo tylko tyle Instagram pokazuje w siatce profilu.
- Najwyzej jedna grafika z tekstem w rzedzie siatki, w kazdym rzedzie w innej kolumnie.
- Wszystkie zdjecia w jednej obrobce.
- Kolor akcentu pojawia sie w jednym slowie tytulu albo na jednym calym slajdzie.

KOLORY
Tlo        %s
Powierzchnie %s
Linie      %s
Tekst      %s
Akcent     %s

KROJE PISMA (darmowe, Google Fonts)
Tytuly     %s, grubosc %s
Opisy      %s, wersaliki, szerokie odstepy miedzy literami
Tekst      %s
""" % (k["dane"]["nazwa"].upper(), kier["nazwa"], t["ink"].upper(), t["carbon"].upper(), t["graphite"].upper(),
       t["bone"].upper(), t["accent"].upper(), f["display"]["rodzina"], f["display"]["wght"],
       f["mono"]["rodzina"], f["tekst"]["rodzina"])
    (paczka / "CZYTAJ.txt").write_text(txt, encoding="utf-8")
