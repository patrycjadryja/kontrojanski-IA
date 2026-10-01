# Jak powstał Koń Trojański IA: proces od zera, krok po kroku

Ten dokument jest dla osoby, która chce zbudować własny generator próbek dla agencji z pomocą Claude Code. Nie musisz kopiować tego systemu. Możesz powtórzyć proces i dojść do swojego. Każdy krok ma: co było do zdecydowania, co powiedzieć Claude Code, co sprawdzić, na czym się potknęłam.

Całość zajęła około dwóch dni pracy w kilku równoległych oknach Claude Code. Kolejność ma znaczenie: generator powstał dopiero po tym, jak trzy produkty zostały zrobione ręcznie dla jednego, prawdziwego klienta.

---

## Zasada 0: najpierw jeden wzorzec ręcznie, potem generator

Zanim ktokolwiek napisał linijkę generatora, powstały trzy rzeczy dla jednego studia detailingu (Imperial Detailing Studio), każda w osobnym oknie Claude Code:

1. **Landing scroll-film** pod jedną usługę (folia PPF): kadry z fal.ai, przejścia wideo, klatki na canvasie sterowane scrollem, formularz kwalifikujący leady.
2. **Logo**: pięć kierunków, wybór jednego ("Refleks", smuga światła w literze E), dopracowanie, komplet plików SVG, wizualizacje na nośnikach.
3. **Redesign Instagrama**: feed przed/po w telefonie, okładki rolek, karuzela, wyróżnione relacje, paczka PNG.

Dopiero mając te trzy rzeczy w ręku wiadomo, co w nich jest powtarzalne (układy, format plików, kolejność scen), a co wymaga oceny (kierunek marki, słowa do klienta, dobór zdjęć). Bez wzorca generator produkuje przeciętność.

**Prompt, od którego warto zacząć własny wzorzec:**

```
Mam klienta z branży X (link do Instagrama). Zrób mu landing pod jedną usługę jako próbkę
do pozyskania go na rozmowę. Styl: premium, strona-film sterowana scrollem, formularz,
który ocenia zapytania. Najpierw zaproponuj storyboard 6 scen i poczekaj na moją akceptację.
```

Przy wzorcu zapisuj, co działało (modele fal.ai, parametry, koszty, pułapki). Te notatki stały się potem fundamentem silnika.

---

## Krok 1: brainstorming, czyli decyzje przed kodem (30 minut)

Claude Code dostał jeden długi, mówiony prompt: trzy terminale zrobiły trzy rzeczy ręcznie, chcę jeden system, wklejam link do Instagrama, wybieram usługę, reszta masowo. Plus jedna zasada biznesowa: landing zawsze pod ofertę wejściową (przynętę), nigdy pod najdroższą usługę.

Claude nie zaczął pisać kodu. Zadał pięć pytań, po jednym naraz. Każde zmieniało architekturę:

| Pytanie | Decyzja | Dlaczego to ważne |
|---|---|---|
| Forma: komenda, panel czy hybryda? | hybryda: generowanie z Claude Code, panel w przeglądarce do przeglądania i decyzji | panel bez własnego backendu AI jest tani, komenda daje dostęp do narzędzi Claude |
| Próbka dla prospekta czy realizacja dla klienta? | oba, dwa tryby: PRÓBKA i WDROŻENIE | ten sam klient przechodzi z jednego w drugi bez budowania od zera |
| Jak masowo? | kolejka linków, płatne kroki dopiero po moich decyzjach | nie palisz budżetu fal.ai na słabych prospektów |
| Kto używa? | najpierw ja, potem kursanci | nisza od początku jako wymienny plik, bez sztywnych ścieżek |
| Ile kierunków brandingu? | 3 do wyboru | tanie szkice, drogie rzeczy dopiero po wyborze |

Potem Claude pokazał trzy podejścia (silnik szablonów z Claude jako mózgiem / trzy skille generujące wszystko od zera / osobna aplikacja na API) i zarekomendował pierwsze. Zgoda na podejście była ostatnią decyzją przed budową.

**Prompt:**

```
Użyj skilla brainstorming. Chcę zbudować system X. Zadawaj mi pytania po jednym,
potem zaproponuj 2-3 architektury z rekomendacją. Nie pisz kodu, dopóki nie zaakceptuję.
```

**Wniosek:** pół godziny pytań oszczędziło dni. Najważniejsza była tabela "etap / kto decyduje / koszt", bo z niej wprost wynika, gdzie w panelu są przyciski decyzji.

---

## Krok 2: rdzeń, czyli jedno źródło prawdy (1 godzina)

Pierwszy plik to nie szablon ani panel, tylko `klient.json`: wszystko o kliencie w jednym miejscu (dane, pewność danych, usługi, kierunki marki, wybory, stany etapów, dziennik). Każdy moduł czyta i pisze ten plik. Nic nie jest przekazywane "z pamięci" między krokami.

Do tego:
- lista etapów i stanów (`czeka / w_kolejce / w_toku / decyzja / gotowe / blad`),
- `pewnosc[pole]`: `odczytane` (widziane w źródle), `zgadniete` (szacunek), `potwierdzone` (człowiek) – żeby system nigdy nie udawał, że wie,
- katalog darmowych krojów Google Fonts, bo logo i strony muszą działać u klienta bez licencji.

**Prompt:**

```
Zbuduj rdzeń: schemat klient.json jako jedyne źródło prawdy, etapy ze stanami,
funkcje wczytaj/zapisz/dziennik. Żaden moduł nie trzyma własnego stanu.
```

---

## Krok 3: logo z tekstu na krzywe (2 godziny)

Najtrudniejszy technicznie element. Logo musi być prawdziwym SVG bez zależności od kroju, więc tekst jest zamieniany na krzywe (fontTools), a motyw graficzny (smuga, belka, punkt, rama, cięcie) jest rysowany parametrycznie w kolorze akcentu. Ten sam kod daje: komplet plików (jasne, ciemne, mono, sygnet, awatar) i wersję animowaną do pokazu.

Co się sprawdziło: pięć motywów wystarczy, żeby trzy kierunki jednego klienta wyglądały jak trzy różne marki. Co było pułapką: niektóre kroje mają nazwy osi inne niż Archivo, więc katalog krojów musi mieć zakresy osi wpisane jawnie.

**Jak sprawdzać:** generuj stronę testową z logo we wszystkich motywach na ciemnym i jasnym tle, rób zrzut z bezgłowego Chrome i oglądaj. Zrzut zamiast zaufania to zasada całego projektu.

---

## Krok 4: pakiet niszy jako plik (2 godziny pisania treści)

Wszystko, co jest o branży, poszło do jednego JSON-a: słownik usług (z podziałem premium / średnia / wejściowa), oferty wejściowe z pełną treścią landingu (6 scen, 3 pakiety, 4 kroki procesu, formularz z punktacją, FAQ, storyboard filmu), archetypy brandingu, typowa diagnoza profilu, teksty pokazu i oferty, słownik słów (firma / obiekt).

To był najdłuższy krok, bo treść pisze się wolniej niż kod. Ale dzięki temu zmiana branży to jeden plik, a kod i szablony zostają.

**Prompt (dla własnej branży, w gotowym systemie):** `/nowa-nisza`

---

## Krok 5: etapy od wzorców (4 godziny)

Każdy z trzech ręcznych wzorców został przerobiony na szablon Jinja zasilany z `klient.json` i pakietu niszy:

- **Instagram**: strona propozycji przed/po + eksport grafik PNG przez bezgłowy Chrome (1080 x 1350, 1080 x 1920, 1080 x 1080, nakładki przezroczyste) + ZIP + CZYTAJ.txt dla klienta.
- **Landing**: film na scrollu (klatki wideo) z dwoma tańszymi trybami zapasowymi (kadry AI przenikające się, zdjęcia klienta), formularz generowany z konfiguracji oferty, punktacja PRIORYTET / STANDARD.
- **Branding**: strona porównania trzech kierunków + księga znaku po wyborze.

Zasada przy każdym: kolory i kroje przychodzą jako zmienne CSS z kierunku, więc zmiana kierunku przebudowuje wszystko. Nic nie jest wpisane na sztywno.

**Pułapki, które kosztowały najwięcej czasu:**
- bezgłowy Chrome potrafi zapisać zrzut i nie zakończyć procesu (czekaj na plik, nie na proces), nie uruchamiaj go równolegle,
- Instagram nie oddaje zdjęć bez logowania, metadane profilu tak (po polsku mają inny format niż po angielsku),
- strony z jednostkami okna (`svh`, `vh`) do testów zrzutem trzeba kopiować z podmianą na piksele.

---

## Krok 6: panel i komenda (3 godziny)

Lokalny serwer w Pythonie bez zależności (stdlib), jeden plik HTML. Panel robi dwie rzeczy: pokazuje stan klientów i przyjmuje decyzje (kierunek, usługa, dane do wdrożenia). Po decyzji sam uruchamia kroki powtarzalne. Każdy krok silnika to osobny proces, więc poprawki w kodzie nie wymagają restartu panelu.

Komenda Claude Code (`/generator-agencji`) to skill: instrukcja, co Claude robi w zwiadzie, jak pisze kierunki, jak zamawia film. Skill jest ważniejszy niż kod, bo to on decyduje o jakości ocen.

---

## Krok 7: agent w tle (2 godziny), wymuszony przez pierwszą prawdziwą próbę

Pierwszy nowy klient wklejony do panelu: nic się nie działo, bo zwiad wymagał wpisania komendy w terminalu. To była wada projektu. Rozwiązanie: panel uruchamia `claude -p` w tle z listą dozwolonych narzędzi i pokazuje jego kroki na żywo (tłumacząc wywołania narzędzi na zdania: "Szukam w Google...", "Czytam stronę...").

Zasady dla agenta w tle: pracuje na jednym kliencie, niczego nie pyta, oznacza domysły, nie wydaje pieniędzy. Pierwszy zwiad z agenta trwał 8 minut i był lepszy od ręcznego.

**Wniosek:** gdy użytkownik mówi "nic się nie dzieje", to nie on ma się nauczyć komendy, tylko system ma ją wykonać sam.

---

## Krok 8: dwie warstwy ofert (3 godziny, z czego 2 w osobnym oknie)

W innym oknie powstał ręcznie, dla tego samego klienta, "pokaz prywatny" (strona-opakowanie próbek wysyłana na zimno) i "oferta współpracy" (interaktywna oferta po rozmowie z pakietami i akceptacją). Potem w tym oknie: odnalezienie tamtej sesji w historii, odczytanie plików, przerobienie na szablony, dopięcie jako etapy 6 i 7 po landingu.

**Prompt, którym to się zaczęło:**

```
W innym oknie zrobiliśmy dla tego klienta dwie warstwy ofert. Znajdź tamtą sesję,
zbierz proces i wynik, przerób na szablony zasilane z klient.json i dołóż jako etapy
na końcu przepływu, żeby po próbkach budowały się same.
```

---

## Krok 9: przegląd jakości na świeżym kliencie (2 godziny)

Wzorcowy klient zawsze wygląda dobrze, bo system był pisany pod niego. Test to kopia prawdziwego nowego klienta przepuszczona przez wszystkie etapy, zrzuty każdej strony na komputerze i telefonie, formularze wypełniane skryptem. Wyszło kilkanaście rzeczy: łamanie długich słów w kaflach, nieczytelny tekst na jasnych zdjęciach, nieuczciwa etykieta "stan na dziś" przy zdjęciach, które nie były zrzutem profilu, formularz udający wysyłkę.

**Prompt:**

```
Dokręć to. Przepuść świeżego klienta przez wszystkie etapy, obejrzyj każdy wynik
na zrzutach (komputer i telefon), przetestuj formularze skryptem, popraw co krzywe.
```

---

## Krok 10: domknięcie pętli sprzedażowej (2 godziny)

Najlepsza próbka jest bezwartościowa, jeśli zostaje na dysku. Dołożone: publikacja pokazu na własny serwer przez SSH jednym przyciskiem, śledzenie prospekta (wizyty, dojście do końca, formularz, kliknięcia) z powiadomieniem na Telegram, koszt per klient w panelu, pakiety i ceny agencji w ustawieniach. Dla kursantów: procedura "podłącz serwer" w skillu, bo każdy ma inny hosting.

---

## Krok 11: paczka open source (1 godzina)

Skrypt eksportu buduje repozytorium bez klientów i sekretów (i sam sprawdza, czy nic nie wyciekło), instalator tworzy środowisko i kopiuje skille, walidator pakietu niszy pilnuje struktury, skill `/nowa-nisza` prowadzi rozmowę o nowej branży. Test: instalacja z ZIP-a w czystym folderze.

---

## Zasady, które wyszły z tego procesu

1. **Wzorzec ręcznie, potem generator.** Generator bez wzorca produkuje przeciętność.
2. **Jedno źródło prawdy** (`klient.json`). Moduły nie rozmawiają ze sobą inaczej.
3. **Claude ocenia, skrypty powtarzają.** Zwiad, kierunki marki, słowa do klienta to Claude. Pliki, grafiki, strony to deterministyczny kod. Dzięki temu 20 klientów wygląda równie dobrze jak pierwszy.
4. **Branża to plik.** Kod nie zna słowa "auto".
5. **Człowiek decyduje w dwóch miejscach** (kierunek marki, usługa), reszta leci sama. Płatne kroki tylko po decyzji.
6. **System nie udaje, że wie.** Każda dana ma pewność, każda cena jest "orientacyjna", dopóki ktoś jej nie potwierdzi.
7. **Weryfikacja zrzutem, nie zaufaniem.** Każdy etap kończy się obejrzeniem wyniku.
8. **Gdy użytkownik mówi "nic się nie dzieje", wina jest w projekcie.**
9. **Pamięć między oknami.** Po każdej sesji notatka: co powstało, gdzie leży, jakie pułapki. Bez tego trzy okna Claude Code to trzy osobne projekty.

---

## Jak odtworzyć to u siebie w sześciu promptach

Jeśli chcesz zbudować własny system zamiast korzystać z tego, oto skrót rozmowy z Claude Code:

1. `Zrób ręcznie landing / logo / redesign IG dla jednego prawdziwego klienta z mojej branży. Zapisz, co zadziałało.`
2. `Użyj brainstorming. Chcę system, który robi to masowo z linku do Instagrama. Pytaj po jednym, zaproponuj architektury, nie pisz kodu bez akceptacji.`
3. `Zbuduj rdzeń: klient.json jako jedyne źródło prawdy, etapy, pakiet niszy jako JSON z całą treścią branżową.`
4. `Przerób moje trzy wzorce na szablony zasilane z klient.json. Każdy etap sprawdzaj zrzutem.`
5. `Zbuduj panel do decyzji i skill dla Claude Code do zwiadu. Panel ma sam uruchamiać Claude w tle i pokazywać, co robi.`
6. `Dokręć: świeży klient przez wszystkie etapy, zrzuty, testy formularzy. Potem publikacja na serwer i śledzenie, czy prospekt otworzył.`

Każdy z tych promptów to kilka godzin pracy z Claude Code. Najwięcej czasu zajmują treści i oglądanie wyników, nie kod.
