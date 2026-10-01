"""Publikacja pokazow na serwerze uzytkownika (SSH + rsync) i odczyt aktywnosci prospekta.
Ustawienia w agencja.json -> hosting: host, port, user, sciezka (katalog pokazow na serwerze), adres (jego adres www), klucz (opcjonalnie)."""
import json
import os
import secrets
import shutil
import subprocess
import time
import urllib.parse
import urllib.request

from .rdzen import SZABLONY, agencja, dziennik, folder, wczytaj, zapisz, zapisz_agencje

WYMAGANE = ("host", "user", "sciezka", "adres")


def _get(url, limit=15):
    """GET z przegladarkowym User-Agent: Cloudflare i podobne zapory blokuja domyslny naglowek Pythona."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) KonTrojanskiIA/1", "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=limit)


def ustawienia():
    a = agencja()
    h = a.get("hosting") or {}
    braki = [p for p in WYMAGANE if not h.get(p)]
    if braki:
        raise ValueError("Brak ustawien hostingu: %s. Uzupelnij w panelu (Ustawienia agencji) albo popros Claude: 'podlacz serwer'." % ", ".join(braki))
    h.setdefault("port", 22)
    h["sciezka"] = h["sciezka"].rstrip("/")
    h["adres"] = h["adres"].rstrip("/")
    return h, a


def _ssh_opcje(h):
    o = ["-p", str(h["port"]), "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR"]
    if h.get("klucz"):
        o += ["-i", h["klucz"]]
    return o


def ssh(h, polecenie, limit=60):
    r = subprocess.run(["ssh"] + _ssh_opcje(h) + ["%s@%s" % (h["user"], h["host"]), polecenie],
                       capture_output=True, text=True, timeout=limit)
    if r.returncode != 0:
        raise RuntimeError("SSH: %s" % (r.stderr.strip().splitlines() or ["blad polaczenia"])[-1])
    return r.stdout


def test():
    """Sprawdza polaczenie, PHP i katalog. Zwraca slownik z wynikami."""
    h, _ = ustawienia()
    out = ssh(h, "echo OK; php -v 2>/dev/null | head -1; command -v rsync >/dev/null && echo RSYNC; mkdir -p %s && echo KATALOG" % h["sciezka"])
    return {"polaczenie": "OK" in out, "php": next((l for l in out.splitlines() if l.startswith("PHP")), ""),
            "rsync": "RSYNC" in out, "katalog": "KATALOG" in out, "adres": h["adres"]}


def instaluj():
    """Wgrywa na serwer pliki wspolne: _config.php (Telegram + sekret), zdarzenia.php, .htaccess."""
    h, a = ustawienia()
    tg = a.get("telegram") or {}
    sekret = h.get("sekret") or secrets.token_urlsafe(24)
    if not h.get("sekret"):
        h["sekret"] = sekret
        zapisz_agencje({"hosting": h})
    cfg = "<?php\nreturn json_decode(<<<'J'\n%s\nJ, true);\n" % json.dumps(
        {"tg_token": tg.get("token", ""), "tg_chat": str(tg.get("chat_id", "")), "sekret": sekret}, ensure_ascii=False)
    ssh(h, "mkdir -p %s/_zdarzenia" % h["sciezka"])
    for nazwa, tresc in (("_config.php", cfg), (".htaccess", (SZABLONY / "hosting" / "htaccess").read_text()),
                         ("zdarzenia.php", (SZABLONY / "hosting" / "zdarzenia.php").read_text()),
                         ("_zdarzenia/.htaccess", "Require all denied\n"), ("index.html", "<!doctype html><title>.</title>")):
        subprocess.run(["ssh"] + _ssh_opcje(h) + ["%s@%s" % (h["user"], h["host"]), "cat > %s/%s && chmod 644 %s/%s" % (h["sciezka"], nazwa, h["sciezka"], nazwa)],
                       input=tresc, text=True, check=True, timeout=30)
    r = _get(h["adres"] + "/zdarzenia.php?k=" + urllib.parse.quote(sekret) + "&p=test")
    if r.status != 200:
        raise RuntimeError("Serwer odpowiedzial %s na zdarzenia.php" % r.status)
    return {"ok": True, "adres": h["adres"], "telegram": bool(tg.get("token") and tg.get("chat_id"))}


def publikuj(slug):
    """Wysyla folder pokaz/ klienta na serwer. Adres: <adres>/<slug>/"""
    h, _ = ustawienia()
    k = wczytaj(slug)
    zr = folder(slug) / "pokaz"
    if not (zr / "index.html").exists():
        raise ValueError("Pokaz jeszcze nie powstal. Najpierw wybierz kierunek i usluge.")
    for nazwa in ("t.php",):
        shutil.copy2(SZABLONY / "hosting" / nazwa, zr / nazwa)
    shutil.copy2(SZABLONY / "hosting" / "akceptacja.php", zr / "oferta" / "akceptacja.php")
    (zr / "akceptacja.php").unlink(missing_ok=True)
    cel = "%s/%s/" % (h["sciezka"], slug)
    ssh(h, "mkdir -p " + cel)
    rsync = shutil.which("rsync")
    if rsync:
        cmd = [rsync, "-az", "--delete", "--exclude", ".DS_Store", "--exclude", "_qa.html", "--chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r",
               "-e", "ssh " + " ".join(_ssh_opcje(h)), str(zr) + "/", "%s@%s:%s" % (h["user"], h["host"], cel)]
    else:
        cmd = ["scp", "-r", "-P", str(h["port"]), str(zr) + "/.", "%s@%s:%s" % (h["user"], h["host"], cel)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError("Wysylka: %s" % (r.stderr.strip().splitlines() or ["blad"])[-1][:300])
    ssh(h, "find %s -type d -exec chmod 755 {} + ; find %s -type f -exec chmod 644 {} +" % (cel, cel))
    adres = "%s/%s/" % (h["adres"], slug)
    try:
        kod = _get(adres, 20).status
    except Exception as e:
        raise RuntimeError("Pokaz wgrany, ale adres %s nie odpowiada: %s" % (adres, e))
    k = wczytaj(slug)
    k["publikacja"] = {"adres": adres, "oferta": adres + "oferta/", "kiedy": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "wersja": int((zr / "index.html").stat().st_mtime)}
    dziennik(k, "publikacja: %s (HTTP %s)" % (adres, kod))
    zapisz(k)
    return adres


def zdarzenia(slug):
    """Aktywnosc prospekta z serwera: sesje, otwarcia, dojscie do konca, klikniecia."""
    h, _ = ustawienia()
    if not h.get("sekret"):
        raise ValueError("Serwer nie jest zainstalowany. Uruchom: hosting-instaluj.")
    url = "%s/zdarzenia.php?k=%s&p=%s" % (h["adres"], urllib.parse.quote(h["sekret"]), slug)
    d = json.loads(_get(url).read().decode("utf-8"))
    z = d.get("zdarzenia", [])
    sesje = {}
    for x in z:
        s = sesje.setdefault(x["sesja"], {"od": x["kiedy"], "do": x["kiedy"], "co": set()})
        s["do"] = x["kiedy"]
        s["co"].add(x["co"])
    KLIK = {"cta-kalendarz", "cta-wiadomosc", "cta-pasek"}
    return {
        "sesje": len(sesje), "otwarcia": sum(1 for x in z if x["co"] == "otwarcie"),
        "koniec": sum(1 for s in sesje.values() if "scena-rozmowa" in s["co"]),
        "landing": sum(1 for s in sesje.values() if "landing-wejscie" in s["co"]),
        "zapytania": sum(1 for x in z if x["co"] == "landing-zapytanie"),
        "klikniecia": sum(1 for x in z if x["co"] in KLIK),
        "akceptacje": d.get("akceptacje", 0),
        "ostatnio": z[-1]["kiedy"] if z else "", "ostatnie_co": z[-1]["co"] if z else "",
        "sciezka": [x["co"] for x in z if x["sesja"] == (z[-1]["sesja"] if z else "")][-12:],
    }
