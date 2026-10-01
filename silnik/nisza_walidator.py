"""Sprawdza pakiet niszy, zanim silnik na nim polegnie. Zwraca liste bledow po polsku."""
from .rdzen import nisza

SEKCJE_TRESCI = ("title", "opis_meta", "eyebrow", "nav_cta", "menu", "sceny", "realizacje", "pakiety", "proces", "dowod",
                 "formularz", "faq", "zamkniecie", "stopka_opis")
POKAZ = ("kurtyna", "znak", "instagram", "strona", "system", "liczby", "rozmowa", "stopka", "wizualizacje", "styl_wizualizacji")
OFERTA = ("naglowek", "intro", "start", "polecany", "budzet_reklamowy", "cele_przykladowe", "pakiety", "dodatki", "mapa",
          "tresci_wzor", "tresci_tytuly", "narzedzia", "zasady", "start_14")
MOTYWY = ("refleks", "belka", "punkt", "rama", "ciecie")


def sprawdz(nazwa):
    b = []
    try:
        n = nisza(nazwa)
    except Exception as e:
        return ["nie da sie wczytac nisze/%s/nisza.json: %s" % (nazwa, e)]
    for pole in ("id", "nazwa", "uslugi_slownik", "oferty_wejsciowe", "branding", "instagram", "pokaz", "oferta", "slownik"):
        if pole not in n:
            b.append("brak sekcji '%s'" % pole)
    if b:
        return b
    ids = set()
    for u in n["uslugi_slownik"]:
        for pole in ("id", "nazwa", "skrot", "typ", "slowa"):
            if not u.get(pole):
                b.append("uslugi_slownik: usluga bez pola '%s' (%s)" % (pole, u.get("id", "?")))
        if u.get("typ") not in ("premium", "srednia", "wejsciowa"):
            b.append("uslugi_slownik: typ musi byc premium/srednia/wejsciowa (%s)" % u.get("id"))
        if len(u.get("skrot", "")) > 10:
            b.append("uslugi_slownik: skrot dluzszy niz 10 znakow (%s)" % u.get("id"))
        ids.add(u.get("id"))
    if len(n["oferty_wejsciowe"]) < 2:
        b.append("potrzebne co najmniej 2 oferty wejsciowe")
    for o in n["oferty_wejsciowe"]:
        oid = o.get("id", "?")
        for pole in ("id", "nazwa", "krotko", "dla_uslug", "prowadzi_do", "dlaczego", "cena_od", "cena_tekst", "czas", "tresc", "storyboard", "fraza"):
            if pole not in o:
                b.append("oferta %s: brak pola '%s'" % (oid, pole))
        for u in o.get("dla_uslug", []) + o.get("prowadzi_do", []):
            if u not in ids:
                b.append("oferta %s: usluga '%s' nie istnieje w uslugi_slownik" % (oid, u))
        if not (o.get("fraza") or {}).get("biernik") or not (o.get("fraza") or {}).get("mianownik"):
            b.append("oferta %s: fraza wymaga 'mianownik' i 'biernik'" % oid)
        t = o.get("tresc") or {}
        for pole in SEKCJE_TRESCI:
            if pole not in t:
                b.append("oferta %s: tresc bez sekcji '%s'" % (oid, pole))
        if len(t.get("sceny", [])) != 6:
            b.append("oferta %s: potrzeba dokladnie 6 scen (jest %d)" % (oid, len(t.get("sceny", []))))
        if len(o.get("storyboard", [])) != len(t.get("sceny", [])):
            b.append("oferta %s: storyboard musi miec tyle kadrow, ile scen" % oid)
        if len((t.get("pakiety") or {}).get("lista", [])) != 3:
            b.append("oferta %s: pakiety.lista musi miec 3 pozycje" % oid)
        if sum(1 for p in (t.get("pakiety") or {}).get("lista", []) if p.get("wyrozniony")) != 1:
            b.append("oferta %s: dokladnie jeden pakiet ma byc wyrozniony" % oid)
        if len((t.get("proces") or {}).get("kroki", [])) != 4:
            b.append("oferta %s: proces.kroki musi miec 4 kroki" % oid)
        f = t.get("formularz") or {}
        if not f.get("kroki") or "prog_priorytetu" not in f or "dzialania" not in f:
            b.append("oferta %s: formularz wymaga kroki, prog_priorytetu, dzialania" % oid)
        ma_tekst = False
        for kr in f.get("kroki", []):
            for p in kr.get("pola", []):
                if p.get("typ") not in ("tekst", "lista", "wybor"):
                    b.append("oferta %s: pole formularza typu '%s' (dozwolone tekst/lista/wybor)" % (oid, p.get("typ")))
                if p.get("typ") == "tekst":
                    ma_tekst = True
                if p.get("typ") in ("lista", "wybor") and not p.get("opcje"):
                    b.append("oferta %s: pole '%s' bez opcji" % (oid, p.get("id")))
        if not ma_tekst:
            b.append("oferta %s: formularz powinien miec jedno pole tekstowe (co klient zamawia / jaki obiekt)" % oid)
        if len(t.get("faq", [])) < 3:
            b.append("oferta %s: faq powinno miec co najmniej 3 pytania" % oid)
    for m in MOTYWY:
        if m not in n["pokaz"].get("znak", {}):
            b.append("pokaz.znak: brak opowiesci dla motywu '%s'" % m)
    for pole in POKAZ:
        if pole not in n["pokaz"]:
            b.append("pokaz: brak sekcji '%s'" % pole)
    for pole in OFERTA:
        if pole not in n["oferta"]:
            b.append("oferta: brak sekcji '%s'" % pole)
    if len(n["oferta"].get("pakiety", [])) != 3:
        b.append("oferta.pakiety: potrzebne 3 pakiety")
    if len(n["oferta"].get("tresci_wzor", [])) != 24:
        b.append("oferta.tresci_wzor: potrzebne 24 pozycje (miesiac publikacji)")
    for pole in ("firma", "firmy", "obiekt", "obiektu", "split_podpis", "probka_tytulu", "probka_posta"):
        if pole not in n["slownik"]:
            b.append("slownik: brak slowa '%s'" % pole)
    return b
