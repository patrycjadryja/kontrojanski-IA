"""Wiersz polecen silnika. Uzycie: python -m silnik <polecenie> [argumenty]"""
import json
import sys

from . import branding, film, instagram, landing, rdzen, zwiad

POMOC = """Generator Agencji - polecenia:

  dodaj <link|nazwa> [...]        dodaje klientow do kolejki
  lista                           klienci i stany etapow
  kolejka                         co czeka na Claude, a co na decyzje w panelu
  dane <slug>                     caly klient.json
  zwiad <slug>                    pobiera publiczne metadane Instagrama
  etap <slug> <etap> <stan> [notatka]
  branding-szkice <slug>          rysuje kierunki z klient.json (branding.kierunki)
  branding-final <slug> [id]      pelny zestaw logo dla wybranego kierunku
  instagram <slug>                strona propozycji + paczka grafik PNG
  oferty <slug>                   oferty wejsciowe z rekomendacja
  landing <slug> [id_oferty]      buduje strone
  pokaz <slug>                    dwie warstwy ofert: pokaz prywatny + oferta po rozmowie
  oferta-leada <slug> [wlacz|wylacz]   oferta osobista dla leada po formularzu (modul opcjonalny)
  film-prompty <slug>             storyboard do wygenerowania kadrow
  film-klatki <slug>              tnie landing/wideo/*.mp4 na klatki
  film-generuj <slug>             kadry i wideo przez fal.ai (wymaga FAL_KEY)
  hosting-test                    sprawdza polaczenie z serwerem z agencja.json
  hosting-instaluj                wgrywa na serwer pliki wspolne (zdarzenia, Telegram)
  publikuj <slug>                 wysyla pokaz klienta na serwer
  zdarzenia <slug>                aktywnosc prospekta na opublikowanym pokazie
  nisze                           lista pakietow niszowych
  nisza-sprawdz <id>              sprawdza pakiet niszy (struktura, oferty, storyboard)
  zrzut <plik.html|adres> <plik.png> [szer] [wys]   zrzut strony do obejrzenia
  panel [port]                    uruchamia panel w przegladarce
"""


def _json(x):
    print(json.dumps(x, ensure_ascii=False, indent=2))


def main(a):
    if not a or a[0] in ("-h", "--help", "pomoc"):
        print(POMOC)
        return 0
    p, r = a[0], a[1:]
    if p == "dodaj":
        for w in r:
            k, nowy = rdzen.nowy_klient(w)
            print("%s  %s" % ("dodano " if nowy else "istnieje", k["slug"]))
    elif p == "lista":
        for k in rdzen.lista():
            print("%-34s %s" % (k["slug"], "  ".join("%s:%s" % (e, k["etapy"].get(e, "-")) for e in rdzen.ETAPY)))
    elif p == "kolejka":
        _json(kolejka())
    elif p == "dane":
        _json(rdzen.wczytaj(r[0]))
    elif p == "zwiad":
        _json(zwiad.instagram(r[0]))
    elif p == "etap":
        k = rdzen.wczytaj(r[0])
        rdzen.ustaw_etap(k, r[1], r[2], " ".join(r[3:]))
        rdzen.zapisz(k)
    elif p == "branding-szkice":
        print(branding.szkice(r[0]))
    elif p == "branding-final":
        print(branding.final(r[0], r[1] if len(r) > 1 else None))
    elif p == "instagram":
        print(instagram.buduj(r[0]))
    elif p == "oferty":
        _json(landing.kandydaci(rdzen.wczytaj(r[0])))
    elif p == "landing":
        print(landing.buduj(r[0], r[1] if len(r) > 1 else None))
    elif p == "pokaz":
        from . import pokaz
        print(pokaz.buduj(r[0]))
    elif p == "oferta-leada":
        from . import oferta_leada
        if len(r) > 1 and r[1] in ("wlacz", "wylacz"):
            k = rdzen.wczytaj(r[0])
            ol = k.setdefault("oferta_leada", {})
            ol["wlaczona"] = r[1] == "wlacz"
            if ol["wlaczona"] and k["landing"].get("oferta_id") and k["landing"]["oferta_id"] not in (ol.get("dla_ofert_wejsciowych") or []):
                ol.setdefault("dla_ofert_wejsciowych", []).append(k["landing"]["oferta_id"])
            rdzen.zapisz(k)
        if rdzen.wczytaj(r[0]).get("oferta_leada", {}).get("wlaczona"):
            print(oferta_leada.buduj(r[0]))
        else:
            print("oferta leada wylaczona")
    elif p == "film-prompty":
        _json(film.prompty(r[0]))
    elif p == "film-klatki":
        print(film.klatki(r[0]), "klatek")
    elif p == "film-generuj":
        print(film.generuj(r[0]), "kadrow")
    elif p == "hosting-test":
        from . import hosting
        _json(hosting.test())
    elif p == "hosting-instaluj":
        from . import hosting
        _json(hosting.instaluj())
    elif p == "publikuj":
        from . import hosting
        print(hosting.publikuj(r[0]))
    elif p == "zdarzenia":
        from . import hosting
        _json(hosting.zdarzenia(r[0]))
    elif p == "nisze":
        _json(rdzen.nisze())
    elif p == "nisza-sprawdz":
        from . import nisza_walidator
        bledy = nisza_walidator.sprawdz(r[0])
        print("OK, pakiet poprawny" if not bledy else "BLEDY:\n- " + "\n- ".join(bledy))
        return 0 if not bledy else 1
    elif p == "zrzut":
        from . import chrome
        print(chrome.zrzut(r[0], r[1], int(r[2]) if len(r) > 2 else 1440, int(r[3]) if len(r) > 3 else 2400))
    elif p == "panel":
        from panel import serwer
        serwer.start(int(r[0]) if r else 8900)
    else:
        print("Nieznane polecenie: %s\n\n%s" % (p, POMOC))
        return 2
    return 0


def kolejka():
    """Podzial pracy: co robi Claude, co czeka na czlowieka."""
    claude, czlowiek = [], []
    for k in rdzen.lista():
        e = k.get("etapy", {})
        nazwa = k["dane"].get("nazwa") or k["slug"]
        if e.get("zwiad") == "w_kolejce":
            claude.append({"slug": k["slug"], "nazwa": nazwa, "zadanie": "zwiad + 3 kierunki brandingu"})
        elif e.get("zwiad") == "gotowe" and not k["branding"].get("kierunki"):
            claude.append({"slug": k["slug"], "nazwa": nazwa, "zadanie": "3 kierunki brandingu"})
        if e.get("landing") == "gotowe" and k["landing"].get("film", {}).get("tryb") == "zdjecia" and k["landing"].get("film_zamowiony"):
            claude.append({"slug": k["slug"], "nazwa": nazwa, "zadanie": "film do landingu (fal.ai)"})
        for etap in rdzen.ETAPY:
            if e.get(etap) == "decyzja":
                czlowiek.append({"slug": k["slug"], "nazwa": nazwa, "decyzja": etap})
            if e.get(etap) == "blad":
                claude.append({"slug": k["slug"], "nazwa": nazwa, "zadanie": "blad w etapie %s, sprawdz dziennik" % etap})
    return {"dla_claude": claude, "dla_czlowieka": czlowiek}


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, RuntimeError, FileNotFoundError, IndexError) as e:
        print("BLAD: %s" % e, file=sys.stderr)
        sys.exit(1)
