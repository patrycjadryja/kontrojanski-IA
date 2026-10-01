"""Agent w tle: panel uruchamia Claude Code bez terminala i pokazuje na zywo, co robi.
Jeden klient naraz, kolejne czekaja w kolejce. Kazde zdarzenie trafia do klienci/<slug>/agent.jsonl."""
import json
import os
import shutil
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from silnik import rdzen

SKILL = Path.home() / ".claude" / "skills" / "generator-agencji" / "SKILL.md"
LIMIT_S = 25 * 60
NARZEDZIA = [
    "Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch",
    "Bash(.venv/bin/python -m silnik:*)", "Bash(.venv/bin/python -m silnik *)",
    "Bash(curl:*)", "Bash(ls:*)", "Bash(mkdir:*)", "Bash(sips:*)", "Bash(file:*)",
]
CHROME = ["mcp__claude-in-chrome"]

ZADANIA = {
    "zwiad": (
        "Jestes agentem Konia Trojańskiego IA i pracujesz bez nadzoru, w tle. Katalog roboczy to folder systemu.\n"
        "Przeczytaj plik {skill} i wykonaj dla klienta `{slug}` po kolei sekcje: 'Zwiad' oraz 'Trzy kierunki brandingu'.\n"
        "Zasady pracy w tle:\n"
        "- Pracuj wylacznie na kliencie `{slug}`. Nie dotykaj innych klientow ani plikow silnika.\n"
        "- Nie zadawaj pytan i nie czekaj na odpowiedz. Gdy czegos nie da sie ustalic, zostaw pole puste albo oznacz je jako zgadniete.\n"
        "- Zdjecia realizacji: sprobuj przez przegladarke (profil na Instagramie), a gdy narzedzia przegladarki sa niedostepne, "
        "poszukaj zdjec na stronie www studia i w wizytowce Google i pobierz je curl do zwiad/zdjecia/. "
        "Bez zdjec idz dalej i wpisz to w zrodlo.notatka.\n"
        "- Klient.json edytuj narzedziem Edit albo Write, zawsze jako poprawny JSON.\n"
        "- Polecenia w powloce uruchamiaj pojedynczo: bez &&, bez |, bez przekierowan i bez wlasnych skryptow. "
        "Dozwolone sa: `.venv/bin/python -m silnik ...`, curl, ls, mkdir, sips, file.\n"
        "- Zeby obejrzec wynik, uzyj `.venv/bin/python -m silnik zrzut <plik.html> <plik.png> 1300 2700` i przeczytaj obraz.\n"
        "- Na koniec uruchom `.venv/bin/python -m silnik branding-szkice {slug}` i popraw bledy, jesli silnik je zglosi.\n"
        "- Ostatnia wiadomosc: 3 zdania po polsku, co ustaliles i czego brakuje. Bez polpauz."
    ),
}

_blok = threading.Lock()
_kolejka = deque()
_stan = {"pracuje": False, "slug": "", "zadanie": "", "od": 0, "ostatnie": "", "pid": None, "bledy": ""}
_watek = None


def claude():
    return shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")


def ustawienia():
    try:
        return json.loads((rdzen.KORZEN / "agencja.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def dziennik_agenta(slug):
    return rdzen.folder(slug) / "agent.jsonl"


def zapisz_zdarzenie(slug, rodzaj, tekst):
    z = {"kiedy": rdzen.teraz(), "rodzaj": rodzaj, "tekst": tekst[:1200 if rodzaj in ("notatka", "blad") else 300]}
    with _blok:
        _stan["ostatnie"] = tekst[:160]
    with open(dziennik_agenta(slug), "a", encoding="utf-8") as f:
        f.write(json.dumps(z, ensure_ascii=False) + "\n")


def zdarzenia(slug, ile=60):
    p = dziennik_agenta(slug)
    if not p.exists():
        return []
    out = []
    for l in p.read_text(encoding="utf-8").splitlines()[-ile:]:
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def stan():
    with _blok:
        s = dict(_stan)
        s["kolejka"] = [{"slug": a, "zadanie": b} for a, b in _kolejka]
    s["trwa_s"] = int(time.time() - s["od"]) if s["pracuje"] else 0
    s["dostepny"] = os.path.exists(claude())
    return s


def _opis_narzedzia(nazwa, d):
    """Tlumaczy wywolanie narzedzia na zdanie zrozumiale w panelu."""
    if nazwa == "Bash":
        c = d.get("command", "")
        for klucz, opis in (("silnik zwiad", "Czytam profil na Instagramie"), ("branding-szkice", "Rysuję trzy kierunki marki"),
                            ("silnik etap", "Zapisuję stan etapu"), ("silnik pokaz", "Sprawdzam dane klienta"),
                            ("silnik dane", "Sprawdzam dane klienta"), ("silnik zrzut", "Robię zrzut, żeby obejrzeć wynik"),
                            ("silnik oferty", "Sprawdzam oferty wejściowe"), ("curl", "Pobieram plik z sieci"),
                            ("sips", "Przycinam zdjęcie"), ("mkdir", "Zakładam folder"), ("ls", "Sprawdzam pliki klienta")):
            if klucz in c:
                return opis
        return "Porządkuję pliki"
    if nazwa == "WebSearch":
        return "Szukam w Google: " + d.get("query", "")
    if nazwa == "WebFetch":
        return "Czytam stronę: " + (urlparse(d.get("url", "")).hostname or d.get("url", ""))
    if nazwa in ("Write", "Edit"):
        return "Zapisuję: " + Path(d.get("file_path", "")).name
    if nazwa == "Read":
        n = Path(d.get("file_path", "")).name
        return "Czytam instrukcję pracy" if n == "SKILL.md" else "Czytam: " + n
    if nazwa.startswith("mcp__claude-in-chrome"):
        akcja = nazwa.split("__")[-1]
        return "Przeglądarka: " + {"navigate": "otwieram " + (urlparse(d.get("url", "")).hostname or ""), "computer": "oglądam stronę",
                                   "get_page_text": "czytam tekst strony", "read_page": "czytam stronę",
                                   "tabs_create_mcp": "nowa karta", "tabs_context_mcp": "sprawdzam karty"}.get(akcja, akcja)
    if nazwa in ("Glob", "Grep"):
        return "Szukam w plikach"
    if nazwa in ("ToolSearch", "TodoWrite", "Skill"):
        return ""
    return nazwa


def _uruchom(slug, zadanie):
    prompt = ZADANIA[zadanie].format(slug=slug, skill=SKILL)
    ust = ustawienia()
    narz = list(NARZEDZIA) + (CHROME if ust.get("chrome", True) else [])
    cmd = [claude(), "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "acceptEdits", "--add-dir", str(rdzen.KORZEN), "--allowedTools"] + narz
    if ust.get("chrome", True):
        cmd.append("--chrome")
    k = rdzen.wczytaj(slug)
    rdzen.ustaw_etap(k, "zwiad", "w_toku", "agent w tle ruszył")
    rdzen.zapisz(k)
    zapisz_zdarzenie(slug, "start", "Claude startuje: zwiad i kierunki marki")
    p = subprocess.Popen(cmd, cwd=str(rdzen.KORZEN), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    with _blok:
        _stan["pid"] = p.pid
    straznik = threading.Timer(LIMIT_S, p.kill)
    straznik.start()
    wynik, ostatni, potkniecia = None, "", 0
    try:
        for linia in p.stdout:
            try:
                o = json.loads(linia)
            except ValueError:
                continue
            t = o.get("type")
            if t == "assistant":
                for c in o.get("message", {}).get("content", []):
                    if c.get("type") == "tool_use":
                        opis = _opis_narzedzia(c.get("name", ""), c.get("input") or {})
                        if opis and opis != ostatni:  # bez pustych i powtorzonych wpisow
                            zapisz_zdarzenie(slug, "krok", opis)
                            ostatni = opis
                    elif c.get("type") == "text" and c.get("text", "").strip():
                        zapisz_zdarzenie(slug, "notatka", c["text"].strip().replace("\n", " "))
            elif t == "user":
                for c in o.get("message", {}).get("content", []) if isinstance(o.get("message", {}).get("content"), list) else []:
                    if c.get("type") == "tool_result" and c.get("is_error"):
                        tr = c.get("content")
                        potkniecia += 1  # szczegoly techniczne zostaja w logu Claude, panel pokazuje tylko licznik
            elif t == "result":
                wynik = o
    finally:
        straznik.cancel()
        p.wait()
    blad = ""
    if wynik is None:
        blad = "Claude zakończył pracę bez wyniku. " + (p.stderr.read() or "")[:300]
    elif wynik.get("is_error"):
        blad = "Claude zgłosił błąd: " + str(wynik.get("result", ""))[:300]
    k = rdzen.wczytaj(slug)
    if wynik:
        ko = k.setdefault("koszty", {"claude_usd": 0, "claude_min": 0, "silnik_min": 0})
        ko["claude_usd"] = round(ko.get("claude_usd", 0) + float(wynik.get("total_cost_usd") or 0), 2)
        ko["claude_min"] = round(ko.get("claude_min", 0) + (wynik.get("duration_ms") or 0) / 60000, 1)
    if not blad and not k["branding"].get("kierunki"):
        blad = "Zwiad się skończył, ale kierunki marki nie powstały."
    if blad:
        rdzen.ustaw_etap(k, "zwiad" if k["etapy"].get("zwiad") != "gotowe" else "branding", "blad", blad)
        zapisz_zdarzenie(slug, "blad", blad)
    else:
        if k["etapy"].get("zwiad") != "gotowe":
            rdzen.ustaw_etap(k, "zwiad", "gotowe", "agent w tle")
        minuty = round((wynik.get("duration_ms") or 0) / 60000, 1)
        zapisz_zdarzenie(slug, "koniec", "Gotowe w %s min. Wybierz kierunek marki.%s" % (
            str(minuty).replace(".", ","), (" Po drodze %d razy trzeba było spróbować inaczej." % potkniecia) if potkniecia > 3 else ""))
    rdzen.zapisz(k)


def _petla():
    while True:
        with _blok:
            if not _kolejka:
                _stan.update(pracuje=False, slug="", zadanie="", pid=None)
                return
            slug, zadanie = _kolejka.popleft()
            _stan.update(pracuje=True, slug=slug, zadanie=zadanie, od=time.time(), ostatnie="Start")
        try:
            _uruchom(slug, zadanie)
        except Exception as e:  # agent nie moze polozyc panelu
            try:
                k = rdzen.wczytaj(slug)
                rdzen.ustaw_etap(k, "zwiad", "blad", "agent: %s" % e)
                rdzen.zapisz(k)
                zapisz_zdarzenie(slug, "blad", str(e))
            except Exception:
                pass


def zlec(slug, zadanie="zwiad"):
    """Dodaje klienta do kolejki agenta i budzi petle. Zwraca False, gdy klient juz czeka albo jest w pracy."""
    global _watek
    if zadanie not in ZADANIA:
        raise ValueError("Nieznane zadanie agenta: " + zadanie)
    if not os.path.exists(claude()):
        raise ValueError("Nie znaleziono programu claude. Zainstaluj Claude Code albo uruchom zwiad w terminalu: /generator-agencji")
    with _blok:
        if (_stan["pracuje"] and _stan["slug"] == slug) or any(a == slug for a, _ in _kolejka):
            return False
        _kolejka.append((slug, zadanie))
        rusz = _watek is None or not _watek.is_alive()
    if rusz:
        _watek = threading.Thread(target=_petla, daemon=True)
        _watek.start()
    return True


def zatrzymaj():
    with _blok:
        _kolejka.clear()
        pid = _stan["pid"]
    if pid:
        try:
            os.kill(pid, 15)
        except OSError:
            pass
    return True
