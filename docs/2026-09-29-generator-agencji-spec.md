# Koń Trojański IA - specyfikacja (2026-09-29)

## Cel

Jeden system dla niszowej agencji (pierwsza nisza: studia detailingu). Wejście: link do Instagrama studia albo jego dane. Wyjście: propozycja brandingu, redesign Instagrama i landing pod jedną ofertę wejściową, wszystko w jednym stylu. Praca masowa: kolejka 5-20 linków naraz.

## Decyzje

| Temat | Decyzja |
|---|---|
| Forma | hybryda: komenda w Claude Code + panel w przeglądarce |
| Tryby | PRÓBKA (szybko, dane orientacyjne) i WDROŻENIE (dane potwierdzone, formularz, piksel) |
| Skala | kolejka linków, płatne kroki dopiero po decyzjach |
| Użytkownik | najpierw właścicielka, potem paczka dla kursantów |
| Branding | 3 kierunki, wybór jednego |
| Architektura | silnik szablonów + Claude jako mózg |
| Landing | zawsze jedna usługa, zawsze oferta wejściowa z niskim progiem ceny |

## Architektura

- `klient.json` w folderze klienta to jedno źródło prawdy: dane, pewność danych, usługi, kierunki, wybory, stany etapów, dziennik.
- Styl kierunku (tokeny kolorów, kroje, motyw logo) jest zapisany raz i zasila trzy produkty. Zmiana kierunku przebudowuje wszystko.
- Pakiet niszowy (`nisze/<nisza>/nisza.json`) trzyma słownik usług, oferty wejściowe z pełną treścią landingu i storyboardem filmu, archetypy brandingu, typową diagnozę profilu.
- Silnik jest deterministyczny: te same dane dają te same pliki. Claude wpisuje dane i decyzje projektowe do `klient.json`, nie pisze HTML od zera.

## Etapy i stany

Etapy: zwiad, branding, instagram, usluga, landing, wdrozenie.
Stany: czeka, w_kolejce (czeka na Claude), w_toku, decyzja (czeka na człowieka), gotowe, blad.

## Koszty

Etapy 1-4 i landing ze zdjęciami klienta: bez kosztów zewnętrznych. Film AI do landingu: około 2 USD na klienta, tylko na zamówienie z panelu.

## Ograniczenia znane na dziś

- Instagram nie oddaje zdjęć ani bio bez logowania. Automat czyta liczby, kategorie i awatar. Zdjęcia pobiera Claude przez Chrome albo wgrywa je użytkownik.
- Generowanie filmu przez REST fal.ai (`film-generuj`) nie było testowane, bo w środowisku nie ma klucza `FAL_KEY`. Ścieżka przez MCP fal-ai jest opisana w skillu.
- Formularz w trybie wdrożenia wysyła JSON na podany webhook. Odbiornik leadów (np. CRM, arkusz, Telegram) jest poza zakresem tej wersji.
- Publikacja landingu na serwerze jest poza zakresem tej wersji. Folder `landing/strona/` jest samodzielny i gotowy do wgrania.
- Paczka dla kursantów (instalator, Windows) jest poza zakresem tej wersji.

## Aktualizacja 2026-09-29 wieczór

- Dwa nowe etapy po landingu: `pokaz` (warstwa 1, pokaz prywatny na zimno) i `oferta` (warstwa 2, oferta po rozmowie). Szablony powstały z ręcznie zbudowanego wzorca `~/Downloads/imperial-pokaz/`. Folder `klienci/<slug>/pokaz/` jest samodzielny, z `t.php` (zdarzenia na Telegram) i `akceptacja.php` (zapis akceptacji).
- Agent w tle: panel uruchamia `claude -p` z listą dozwolonych narzędzi i pokazuje kroki na żywo. Zwiad rusza od razu po dodaniu linku.
- Wgrywanie zdjęć klienta przez panel.
- Kroki silnika panel uruchamia jako osobne procesy, więc zmiany w kodzie silnika nie wymagają restartu panelu.
- Nietestowane: `t.php` i `akceptacja.php` (brak PHP lokalnie), wizualizacje znaku przez fal.ai dla nowego klienta.

## Aktualizacja 2026-09-30

- Publikacja pokazów na serwerze użytkownika przez SSH + rsync (`silnik/hosting.py`): instalacja plików wspólnych (`_config.php`, `zdarzenia.php`, `.htaccess`), wysyłka folderu `pokaz/`, odczyt aktywności prospekta do panelu, powiadomienia Telegram. Ustawienia w `agencja.json` (hosting, telegram, oferta). Procedura dla kursantów w skillu ("podłącz serwer").
- Koszt i czas per klient w panelu (Claude z agenta w tle, silnik z pomiaru kroków, fal.ai szacunkowo).
- Pakiety i ceny agencji edytowane w panelu, nadpisują pakiet niszy.
- Przegląd jakości na świeżym kliencie: poprawki czytelności grafik, uczciwe etykiety "przed", formularz bez adresu odbioru zawsze w trybie pokazowym, kopia landingu w pokazie bez piksela i wysyłki.
