---
name: generator-agencji
description: Generator Agencji - system, który z linku do Instagrama studia robi branding (3 kierunki), redesign Instagrama i landing pod jedną ofertę wejściową. Używaj, gdy padnie "/generator-agencji", "nowy klient", "przerób kolejkę", "zrób zwiad", "kierunki brandingu dla", "film do landingu", "wpisz cennik klienta" albo link do Instagrama studia z prośbą o próbkę.
---

# Generator Agencji

Folder systemu: `~/generator-agencji`. Panel: `http://localhost:8900` (start: `~/generator-agencji/panel.sh`).
Silnik: `cd ~/generator-agencji && .venv/bin/python -m silnik <polecenie>` (lista poleceń: `pomoc`).

## Podział pracy

| Kto | Co robi |
|---|---|
| Ty (Claude) | zwiad, mapa usług, diagnoza, 3 kierunki brandingu, teksty pod klienta, film z fal.ai, cennik |
| Silnik (skrypty) | pliki logo, strona propozycji, eksport PNG, landing, klatki filmu |
| Człowiek (panel) | wybór kierunku, wybór oferty wejściowej, potwierdzenie danych do wdrożenia |

Nigdy nie wybieraj kierunku ani oferty za człowieka. Nigdy nie generuj płatnych kadrów bez `landing.film_zamowiony: true`.

## Start każdej sesji

1. Sprawdź, czy panel działa: `curl -s localhost:8900/api/stan >/dev/null || ~/generator-agencji/panel.sh`.
2. Jeśli użytkownik podał linki, dodaj je: `python -m silnik dodaj <link> [...]`.
3. `python -m silnik kolejka` i przerób wszystko z `dla_claude`. Klienta, nad którym pracuje agent w tle (`curl -s localhost:8900/api/stan`, pole `agent`), zostaw w spokoju. Kilku klientów = osobny subagent na klienta, równolegle.
4. Na końcu podaj listę klientów z decyzjami czekającymi w panelu i link do panelu.

## Zwiad (etap 1)

Cel: uzupełnić `klienci/<slug>/klient.json` i folder `zwiad/`.

1. `python -m silnik zwiad <slug>` pobiera liczby z Instagrama, awatar i wstępną mapę usług.
2. WebSearch: nazwa firmy, adres, telefon, strona www, wizytówka Google (ocena, liczba opinii), cennik jeśli publiczny.
3. Zdjęcia realizacji. Instagram blokuje pobieranie bez logowania, dlatego:
   - jeśli dostępne są narzędzia Chrome (claude-in-chrome), otwórz profil w przeglądarce użytkownika, odczytaj bio, nazwy wyróżnionych relacji i pobierz 12-16 zdjęć z siatki do `zwiad/zdjecia/`;
   - w innym wypadku poproś użytkownika o wrzucenie zrzutów lub zdjęć do `zwiad/zdjecia/` i idź dalej bez nich.
4. Zapisz `zwiad/zdjecia.json` (ścieżki względem `zwiad/`):
   ```json
   {"awatar_przed": "zdjecia/awatar.jpg",
    "siatka_przed": ["zdjecia/b0.jpg"],
    "wyroznione_przed": [{"nazwa": "Folia PPF", "plik": "zdjecia/h1.jpg"}],
    "foto": [{"plik": "zdjecia/t1.jpg", "duzy": "zdjecia/r1.jpg", "auto": "Porsche 911", "usluga": "Folia PPF", "format": "rolka|post"}]}
   ```
   `siatka_przed` to obecny wygląd siatki (z napisami). `foto` to czyste zdjęcia aut. Kolejność w `foto` = kolejność w nowej siatce.
5. W `klient.json` uzupełnij:
   - `dane`: nazwa, nazwa_krotka (najmocniejsze słowo nazwy), dopisek, miasto, adres, kod, telefon, bio, kategorie, ocena_google, liczba_opinii;
   - `pewnosc[pole]`: `odczytane` (widziałeś w źródle) albo `zgadniete` (szacunek). Niczego nie zmyślaj bez oznaczenia;
   - `zrodlo.www`, `zrodlo.google`;
   - `uslugi`: `{id, nazwa, typ, zrodlo, cena, uwagi}`. `id` i `typ` bierz ze słownika `nisze/<nisza>/nisza.json`. Nazwa w brzmieniu klienta;
   - `diagnoza.logo` (2 zdania o obecnym znaku), `diagnoza.podsumowanie`, `diagnoza.feed` (4-6 par `["teraz", "po zmianie"]`, konkret z tego profilu).
6. `python -m silnik etap <slug> zwiad gotowe`.

## Trzy kierunki brandingu (etap 2)

Wpisz do `branding.kierunki` dokładnie 3 kierunki o id `a`, `b`, `c`, po jednym na archetyp z `nisza.json` (ewolucja, premium, odwazny). Muszą się od siebie wyraźnie różnić krojem, akcentem i motywem.

```json
{"id": "a", "nazwa": "Rosso", "archetyp": "odwazny",
 "opis": "Jedno, dwa zdania o charakterze.", "uzasadnienie": "Dlaczego pasuje do TEGO studia.",
 "tokeny": {"ink": "#0a0a0b", "carbon": "#141416", "graphite": "#2a2a2e", "bone": "#ece8e1", "mute": "#8f8c87", "accent": "#e0301e", "on_accent": "#0a0a0b"},
 "fonty": {"display": {"rodzina": "Archivo", "wght": 900, "wdth": 125, "wersaliki": true, "tracking": -0.012},
           "tekst": {"rodzina": "Archivo"}, "mono": {"rodzina": "IBM Plex Mono"}},
 "logo": {"tekst": "Imperial", "dopisek": "Detailing Studio", "motyw": "refleks", "litera": 3, "monogram": "I"},
 "probka_tytulu": "Lakier jak *z salonu*", "probka_posta": "Folia *PPF*",
 "krawedzie": "ostre", "film": "grayscale(.9) contrast(1.12) brightness(.96)"}
```

Zasady:
- Kroje tylko z katalogu w `silnik/fonty.py` (KATALOG). Motywy: `refleks`, `belka`, `punkt`, `rama`, `ciecie`.
- Kontrast: ink/bone min. 7:1, accent/on_accent min. 3:1, accent/ink min. 3:1. Silnik odrzuci słabsze.
- `logo.litera` = indeks litery dla motywu refleks (liczony od 0). Wybierz literę z dużą powierzchnią (E, A, R, M).
- `film` = filtr CSS dopasowujący kolory filmu do akcentu (przy akcencie innym niż ciepły odbarwiaj: `grayscale(.9)`).
- Bez gradientów, bez złotych efektów, bez ikon aut. Jeden akcent.
- `*słowo*` w tekstach = słowo w kolorze akcentu.

Potem: `python -m silnik branding-szkice <slug>`. Etap sam przejdzie w stan `decyzja`. Obejrzyj `branding/kierunki.html` zrzutem z Chrome i popraw, jeśli logo wygląda źle (za szeroki krój, nieczytelny motyw).

Po wyborze kierunku w panelu silnik sam robi pliki logo i paczkę na Instagram. Możesz to też uruchomić ręcznie: `branding-final <slug> <id>`, `instagram <slug>`.

## Redesign Instagrama (etap 3)

Silnik planuje siatkę sam. Twoja rola to poprawki w `klient.json` pod kluczem `instagram` (każde pole nadpisuje automat): `haslo`, `lead`, `bio_po` (lista linii), `wyroznione` (`nazwa`, `skrot` do 8 znaków, `styl` s|o|p|rp, `img`), `siatka_po` (12 kafli), `szablony`. Układy kafli: `foto`, `okladka`, `podpis`, `solid`, `ciemny`, `split`, `tytulowy`, `tresc`, `kontakt`. Po zmianach: `python -m silnik instagram <slug>`.

## Oferta wejściowa i landing (etapy 4-5)

Zasada nadrzędna: landing sprzedaje JEDNĄ ofertę wejściową z niskim progiem ceny. Nigdy ceramiki, pełnego PPF ani zmiany koloru. Drogie usługi studio sprzedaje przy odbiorze auta.

- `python -m silnik oferty <slug>` pokazuje ranking. Wybiera człowiek w panelu.
- Treść bazowa pochodzi z `nisze/<nisza>/nisza.json` (`oferty_wejsciowe[].tresc`). Pod klienta nadpisuj w `klient.json` pod `landing.tresc` tylko to, co trzeba: `sceny`, `pakiety.lista` (realne ceny), `faq`. Listy podmieniają się w całości.
- Jeśli studio ma usługę wejściową, której nie ma w pakiecie niszy, dopisz nową ofertę do `nisza.json` w tym samym schemacie (z `storyboard`).
- `landing.auto` = auto do filmu (np. najczęstsza marka na profilu).
- Po zmianach: `python -m silnik landing <slug>`.

## Film do landingu (tylko gdy `landing.film_zamowiony`)

1. `python -m silnik film-prompty <slug>` zwraca 6 scen.
2. Kadr 1: `fal-ai/nano-banana-pro`, 16:9, 2K. Kadry 2-6: `fal-ai/nano-banana-pro/edit` z kadrem 1 jako referencją (to samo auto). Zapisz jako `landing/kadry/01-hero.png` itd.
3. Pokaż kadry użytkownikowi przed wideo. Wideo to większy koszt.
4. Przejścia: `minimax/h3-max/image-to-video`, `image_url` = kadr N, `end_image_url` = kadr N+1, 5 s, 1080P. Zapisz jako `landing/wideo/u1.mp4` ... `u5.mp4`.
5. `python -m silnik film-klatki <slug>`, potem `python -m silnik landing <slug>`.
6. Ustaw `landing.film_zamowiony: false`.

Same kadry bez wideo też działają: landing przenika między nimi przy przewijaniu (tryb `kadry`).
Z kluczem `FAL_KEY` w środowisku całość robi `python -m silnik film-generuj <slug>`.

## Dwie warstwy ofert (etapy 6-7)

Powstają automatycznie po landingu (`python -m silnik pokaz <slug>` buduje obie). Wynik: samodzielny folder `klienci/<slug>/pokaz/`.

| Warstwa | Plik | Kiedy się jej używa |
|---|---|---|
| 1. Pokaz prywatny | `pokaz/index.html` | wysyłka na zimno, cel: umówiona rozmowa |
| 2. Oferta współpracy | `pokaz/oferta/index.html` | po rozmowie sprzedażowej, cel: akceptacja pakietu |

- Treści bazowe: `nisza.json` pod kluczami `pokaz` i `oferta`. Nadpisania klienta: `klient.json` pod `pokaz.tresc` i `oferta.tresc`.
- Opowieść o znaku zależy od motywu logo. Własną wpisz w kierunku jako `historia_znaku: {naglowek, lead}`.
- Dane nadawcy (podpis, kalendarz, link do wiadomości) są wspólne: `agencja.json`, edycja w panelu.
- Po rozmowie użytkownik wpisuje w panelu cele klienta jego słowami, datę rozmowy, ważność i polecany pakiet. Możesz to też wpisać do `klient.json` pod `oferta` (`cele: [{cytat, odp, gdzie}]`, `rozmowa`, `wazna_do`, `polecany`).
- Pakiety i ceny agencji w `nisza.json` → `oferta.pakiety` są przykładowe, dopóki użytkownik ich nie potwierdzi. Nie zmieniaj ich bez polecenia.
- Język: liczba mnoga "my / Wy", bez krytyki obecnej marki, bez obietnic liczbowych, stopka z ujawnieniem projektu koncepcyjnego zostaje.

### Wizualizacje znaku (tylko gdy `pokaz.wizualizacje_zamowione`)

1. Wyeksportuj logo do PNG: `python -m silnik zrzut klienci/<slug>/branding/final/logo-podstawowe-jasne-na-ciemnym.svg <plik.png> 1600 500`.
2. Dla każdej pozycji z `nisza.json` → `pokaz.wizualizacje` uruchom `fal-ai/nano-banana-pro/edit` z logo jako referencją. Prompt = `prompt` pozycji + `pokaz.styl_wizualizacji` z podstawionymi kolorami kierunku.
3. Zapisz jako `klienci/<slug>/branding/wizualizacje/<plik>.jpg` (nazwy jak w `plik`), ustaw `pokaz.wizualizacje_zamowione: false`, uruchom `python -m silnik pokaz <slug>`.

Koszt: 7 obrazów, około 1 USD. Tablica rejestracyjna: zawsze podawaj format europejski 520 x 114 mm.

## Publikacja pokazu i śledzenie prospekta

Pokaz trafia na serwer użytkownika pod `<adres>/<slug>/`. Panel ma przycisk "Wyślij pokaz na serwer", z terminala: `python -m silnik publikuj <slug>`. Aktywność prospekta: `python -m silnik zdarzenia <slug>` (wizyty, dojście do końca, formularz, kliknięcia, akceptacje). Powiadomienia o kluczowych momentach idą na Telegram, jeśli w ustawieniach jest token i chat id.

### Podłączenie serwera ("podłącz serwer", "zainstaluj się na moim serwerze", "skonfiguruj hosting")

Użytkownik (często kursant) ma własny hosting i domenę. Przeprowadź go krok po kroku, jedno pytanie naraz:

1. Zapytaj, gdzie ma hosting (nazwa firmy) i czy ma dostęp SSH. Jeśli nie wie: w panelu hostingu szukaj "SSH", "dostęp do powłoki" albo "SFTP". Bez SSH publikacja nie zadziała; wtedy wskaż, jak włączyć SSH u swojego dostawcy (cyber_Folks, home.pl, nazwa.pl, OVH mają to w panelu).
2. Zbierz: host, port (domyślnie 22, cyber_Folks 222), użytkownik, domena. Katalog docelowy ustal sam: zwykle `domains/<domena>/public_html/pokaz` (cyber_Folks, DirectAdmin) albo `public_html/pokaz` (cPanel). Sprawdź przez `ssh` z `ls`, zanim wpiszesz.
3. Klucz SSH: jeśli `ssh -o BatchMode=yes` nie wchodzi, użytkownik musi raz wgrać klucz. Podaj mu do wpisania w terminalu: `ssh-keygen -t ed25519` (jeśli nie ma klucza) i `ssh-copy-id -p <port> <user>@<host>` (poda hasło). Ty nie znasz jego hasła i o nie nie pytasz.
4. Zapisz ustawienia: `python -m silnik dane` nie służy do tego; wpisz je do `agencja.json` pod `hosting` (host, port, user, sciezka, adres) albo poproś, żeby wpisał w panelu (Ustawienia agencji).
5. Telegram (opcjonalnie): bot przez @BotFather (token), chat id przez @userinfobot. Zapisz pod `telegram` w `agencja.json`.
6. `python -m silnik hosting-test`, potem `python -m silnik hosting-instaluj`. Instalacja wgrywa `_config.php`, `zdarzenia.php`, `.htaccess` i sprawdza adres z zewnątrz.
7. Test: `python -m silnik publikuj <slug>` na dowolnym gotowym kliencie, otwórz adres, zrób zrzut. Potem `zdarzenia <slug>` pokaże Twoją wizytę.

Serwer musi mieć PHP (na powiadomienia i zapis zdarzeń). Bez PHP strony działają, ale śledzenie nie. Cloudflare i podobne zapory blokują domyślny User-Agent Pythona, silnik używa przeglądarkowego.

## Koszty

Panel pokazuje koszt per klient: Claude z wyników agenta w tle (sesje w terminalu nie są liczone), fal.ai szacunkowo po plikach (kadry 0,90, wideo 0,95, wizualizacje 1,05 USD). Zapis w `klient.json` pod `koszty`.

## Pakiety agencji

Pakiety i ceny w ofercie po rozmowie: `agencja.json` pod `oferta` (nadpisuje `nisza.json` -> `oferta`), edycja w panelu. Gdy użytkownik mówi "zmień ceny pakietów", edytuj `agencja.json`, nie pakiet niszy.

## Agent w tle

Panel potrafi sam uruchomić zwiad (`panel/agent.py`, program `claude -p`). Kroki agenta zapisują się w `klienci/<slug>/agent.jsonl` i są widoczne w panelu na żywo. Gdy użytkownik pyta, co się dzieje z klientem, przeczytaj ten plik i `dziennik` w `klient.json`.

## Wdrożenie (etap 8)

Po przełączeniu trybu na Wdrożenie w panelu: potwierdź z użytkownikiem dane oznaczone `zgadniete`, wpisz realny cennik do `landing.tresc.pakiety.lista` oraz formularz `kroki` (ceny w opcjach), ustaw `landing.formularz_endpoint` i `landing.piksel_meta`. Publikacja folderu `landing/strona/` to osobna decyzja użytkownika, pytaj przed wysłaniem na serwer.

## Styl tekstów

- Nigdy półpauza ani pauza, tylko "-".
- Formy neutralne płciowo, bez domyślnej formy żeńskiej i męskiej.
- Krótkie zdania, konkret, bez marketingowych ogólników.

## Weryfikacja

Po każdym etapie zrób zrzut: `python -m silnik zrzut <plik.html> <plik.png> [szer] [wys]` i obejrzyj go. Strony z jednostkami svh (pokaz, oferta) oglądaj w oknie 1440 x 900. Stan przewijania landingu sprawdzaj przez serwer panelu (`/k/<slug>/landing/strona/index.html`). Zrzuty rób po kolei, nigdy równolegle.
