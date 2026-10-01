# Jak zbudować własnego Konia Trojańskiego IA: proces krok po kroku

Ten dokument jest dla osoby, która zaczyna z agencją i chce zbudować z Claude Code swój własny system do robienia próbek dla klientów. Nie trzeba umieć programować. Trzeba umieć opisać, czego się chce, podejmować decyzje, kiedy Claude pyta, i oglądać wyniki.

Tak powstał Koń Trojański IA. Poniżej dokładnie te prompty, które wpisywałam, w tej kolejności. Oczyściłam je z literówek i powtórzeń (nagrywałam je głosem), ale treść jest ta sama. Możesz je wkleić i zmienić tylko branżę i nazwę klienta.

Cały proces zajął dwa dni. Najwięcej czasu zajęło oglądanie wyników i pisanie treści, nie kod.

---

## Zanim zaczniesz

**Czego potrzebujesz**

- Komputer Mac (albo Linux). Na Windowsie da się przez WSL, ale tego nie testowałam.
- **Claude Code** z aktywnym planem. To program, który uruchamiasz w terminalu (czarne okienko z tekstem) i rozmawiasz z nim jak na czacie, tylko że on może tworzyć pliki, uruchamiać programy i przeglądać internet.
- Google Chrome.
- Konto na **fal.ai** (generowanie obrazów i wideo, kilka dolarów wystarczy na start) podłączone do Claude Code jako MCP. Jak podłączyć: wpisz w Claude Code "podłącz mi fal.ai jako MCP", przeprowadzi Cię.
- Jeden prawdziwy klient z Twojej branży, który ma Instagram. Nie musi wiedzieć, że coś dla niego robisz.

**Jak rozmawiać z Claude Code**

Trzy rzeczy, które robią największą różnicę:

1. Mów, po co coś robisz, nie tylko co. "Chcę landing jako próbkę, żeby pozyskać klienta na rozmowę" daje lepszy wynik niż "zrób landing".
2. Jeśli Claude pyta, odpowiadaj. Pięć pytań na początku oszczędza dni.
3. Każdy wynik obejrzyj. Powiedz, co Ci się nie podoba, konkretnie. "Nagłówek za długi, zdjęcie za jasne" działa. "Zrób ładniej" nie działa.

Słowa, które będą się pojawiać:

- **Panel**: strona w Twojej przeglądarce, na której klikasz decyzje. Działa tylko na Twoim komputerze.
- **Skill**: instrukcja dla Claude Code, zapisana w pliku. Dzięki niej Claude wie, jak robić daną rzecz tak samo za każdym razem. Uruchamiasz ją ukośnikiem, np. `/brainstorming`.
- **Zwiad**: zebranie informacji o firmie klienta (dane, usługi, zdjęcia, co ma na Instagramie).
- **Oferta wejściowa**: tania usługa, od której klient końcowy zaczyna (np. przegląd lakieru za 149 zł), zamiast najdroższej.

---

## Etap A: trzy próbki ręcznie dla jednego klienta (1 dzień)

Najważniejsza zasada: **zanim zbudujesz maszynę, zrób jedną rzecz ręcznie i dobrze.** Ja zrobiłam dla Imperial Detailing Studio trzy rzeczy w trzech osobnych oknach Claude Code: landing, logo i redesign Instagrama. Dopiero potem powstał generator. Bez wzorca generator produkuje przeciętność.

### A1. Landing jako próbka

Otwórz Claude Code i wklej:

```
Chcę stworzyć generator landing pages, które będę wykorzystywać jako próbki,
takiego konia trojańskiego do pozyskania klienta w agencji social media.

Zaczynamy od niszy: auto detailing. Docelowo chcę wysłać masowo 10-20 landingów,
każdy dopasowany pod innego klienta, z którym chcę współpracować.

Zakładam, że każdy z tych klientów ma słabą stronę albo nie ma landingu, który sprzedaje
jego najbardziej marżową usługę. W detailingu to pewnie ceramika albo folia PPF.

Chcę też od razu prototyp formularza kontaktowego, który filtruje leady, żeby zgłaszały się
głównie osoby zainteresowane i z pieniędzmi na droższe usługi. To będzie część mojej oferty
dla klienta: "zbieramy tylko dobre zapytania".

Powiedz mi, co według Ciebie powinno być początkiem: pierwszy landing czy od razu generator?
```

Claude odpowie, że najpierw jeden landing wzorcowy. Zgódź się. Potem:

```
Zacznijmy od landingu dla tego klienta: [link do Instagrama klienta]

Chcę, żeby landing był interaktywny, najlepiej 3D. Użyj fal.ai do wygenerowania najpierw
obrazków (kadrów), wrzuć je do Pobranych i pokaż mi je jako komponenty. Potem zanimujemy je
w film, który przewija się razem ze stroną. Przykład tego, o co mi chodzi: [link do
inspiracji, np. TikTok ze stroną 3D]

Użyj naszych najlepszych wzorców projektowania landingów i brand booków.
```

Claude zrobi storyboard (6 scen), wygeneruje kadry, pokaże Ci je. **Obejrzyj je, zanim pozwolisz robić wideo**, bo wideo kosztuje więcej. Potem "tak, działaj".

Co sprawdzić w wyniku: strona otwiera się w przeglądarce, film przewija się ze scrollem, formularz działa (wypełnij go jak klient), ceny są oznaczone jako orientacyjne.

Koszt mojego wzorca na fal.ai: około 2 USD.

### A2. Logo i identyfikacja

W nowym oknie Claude Code (żeby nie mieszać kontekstów):

```
[link do Instagrama klienta]

W Pobranych wrzuciłam Ci kilka przykładów brandingów, które mi się podobają (logo z wizytówką)
oraz przykłady dobrych feedów na Instagramie. Poznasz po zdjęciach, co jest czym.

Chcę zrobić rebranding logo dla tego klienta, bo obecne wygląda tanio. Chcemy trafić do klientów
premium, wyczulonych na estetykę, w tym właścicieli drogich aut.

Zaproponuj mi najpierw 3-5 kierunków stylu. Zrób to w artefakcie (stronie do obejrzenia),
ja wybiorę najlepszy i będziemy go dopracowywać.
```

Wybierz kierunek. Potem:

```
Najlepsza jest wersja A. Dopracuj ją i doszlifuj.

Wklejam Ci link do redesignu Instagrama, który zrobiłam temu klientowi: [link].
Bardzo podoba mi się ten styl. Chcę, żebyś w tym stylu dokręcił propozycję A.

Użyj fal.ai do wizualizacji logo na prawdziwych rzeczach (szyld, wizytówka, strój, brelok),
ale zachowaj estetykę bardzo premium. Masz myśleć jak światowej klasy projektant identyfikacji
wizualnej dla marek premium.
```

Co sprawdzić: logo jest czytelne w małym kółku (zdjęcie profilowe) i na szyldzie, pliki są w SVG (skalują się bez utraty jakości), wizualizacje pokazują to samo logo, nie jego wariacje.

Pułapka: modele obrazów źle odtwarzają logo z opisu. Dawaj logo jako obraz referencyjny i pisz w prompcie "the exact logo from the reference image".

### A3. Redesign Instagrama

Ten zrobiłam w claude.ai (na czacie, nie w terminalu), bo chciałam szybko oglądać wynik jako stronę. Prompt w skrócie:

```
Zrób redesign Instagrama dla [klient, link]. Pokaż profil przed i po w dwóch telefonach obok
siebie. Te same zdjęcia, zmienia się tylko oprawa: jedna typografia, jeden kolor akcentu,
jeden sposób podpisywania realizacji. Do tego: szablony okładek rolek, karuzela poradnikowa,
okładki wyróżnionych relacji bez rysunkowych ikon, diagnoza "co dziś obniża odbiór" w tabeli
teraz / po zmianie. Zasady siatki: najwyżej jedna grafika z tekstem w rzędzie, tekst tylko
w polu, które Instagram pokazuje w siatce.
```

Co sprawdzić: w porównaniu przed/po widać różnicę od razu, bez tłumaczenia. Jeśli trzeba tłumaczyć, oprawa jest za słaba.

**Po etapie A masz:** trzy foldery z plikami i, co ważniejsze, wiedzę, co w tych trzech rzeczach jest powtarzalne (układy, formaty, kolejność scen), a co wymaga Twojej oceny (kierunek marki, słowa, zdjęcia). To jest fundament generatora.

---

## Etap B: generator (1 dzień)

### B1. Brainstorming: decyzje przed kodem (30 minut)

Nowe okno Claude Code. Jeden długi prompt, w którym mówisz, co masz i czego chcesz:

```
Mam teraz trzy terminale, w których zrobiliśmy dla jednego klienta ze studia detailingu trzy
rzeczy: interaktywny landing, logo z brandingiem i redesign Instagrama.

Jako właściciel niszowej agencji dla studiów detailingu chcę to zamknąć w jeden system,
który będzie moim aktywem i który będę skalować. Chcę kompletny generator tych trzech rzeczy,
gdzie jedno korzysta z drugiego.

Chcę działać tak: wpisuję link do Instagrama klienta albo jego dane, system go zaczytuje
i przygotowuje propozycję brandingu, potem redesign Instagrama, potem interaktywny landing
na wybraną przeze mnie usługę z jego oferty. System ma zmapować, jakie klient ma usługi,
a ja w panelu wybieram, na którą robimy landing.

Ważne: landing zawsze skupia się na jednej usłudze, bo będziemy na niego puszczać reklamy.
I zawsze celujemy w ofertę wejściową, nie w najdroższą usługę. Chcemy przyciągnąć klienta
na coś małego, na przynętę, a nie walić dużymi cenami.

Najpierw skup się na zaprojektowaniu tego systemu do masowego generowania. Użyj skilla
brainstorming, jeśli uznasz, że jest pomocny.
```

Claude nie zacznie pisać kodu. Zada pytania, po jednym. Moje odpowiedzi (możesz odpowiedzieć inaczej, ale wiedz, co z czego wynika):

| Pytanie Claude | Moja odpowiedź | Co to zmienia |
|---|---|---|
| W jakiej formie obsługujesz system: komenda w terminalu, panel w przeglądarce czy hybryda? | hybryda | generowanie robi Claude, decyzje klikasz w panelu |
| Próbka dla prospekta czy realizacja dla płacącego klienta? | oba, dwa tryby | ten sam klient przechodzi z próbki we wdrożenie |
| Jak masowo? | kolejka linków, płatne kroki dopiero po moich decyzjach | nie wydajesz na słabych prospektów |
| Kto używa? | najpierw ja, potem kursanci | branża od początku jako wymienny plik |
| Ile kierunków brandingu? | 3 do wyboru | tanie szkice, drogie rzeczy po wyborze |

Potem Claude pokazał trzy możliwe architektury. Wybrałam "silnik szablonów + Claude jako mózg": Claude robi to, co wymaga oceny (zwiad, kierunki marki, słowa), skrypty robią to, co ma być powtarzalne (pliki, grafiki, strony). Dzięki temu dwudziesty klient wygląda równie dobrze jak pierwszy.

Mój prompt zatwierdzający:

```
tak, działaj i daj mi link do dashboardu
```

### B2. Budowa (Claude robi sam, Ty oglądasz, 4-6 godzin)

Po zatwierdzeniu Claude buduje kolejno: rdzeń (jeden plik na klienta z wszystkimi danymi), generator logo, pakiet branży (wszystkie teksty o branży w jednym pliku), szablony z Twoich trzech wzorców, panel, skill do zwiadu. Co jakiś czas pokaże Ci zrzut ekranu. Oglądaj i mów, co poprawić.

Nie musisz rozumieć kodu. Musisz rozumieć trzy rzeczy, które Claude Ci zaproponuje i które warto zaakceptować:

1. **Jeden plik na klienta** (`klient.json`), w którym jest wszystko. Każdy etap czyta i pisze ten plik. Nic nie jest "pamiętane" między krokami.
2. **Pewność danych.** Każda informacja o kliencie ma oznaczenie: odczytana ze źródła, zgadnięta, potwierdzona przez Ciebie. System nigdy nie udaje, że wie.
3. **Branża jako plik.** Słowa "auto", "lakier", "studio" nie są w kodzie, tylko w pakiecie branży. Zmiana branży to podmiana pliku.

### B3. Pierwszy prawdziwy test i agent w tle (2 godziny)

Wkleiłam w panelu link do nowego klienta i... nic się nie działo, bo zwiad wymagał wpisania komendy w terminalu. Napisałam:

```
Wkleiłam link do nowego klienta do naszego generatora. Wskoczył na zwiad w kolejce,
ale nic się z tym nie dzieje. Nie wiem, czy Claude już coś robi, czy ruszył agent do zwiadu,
czy co mam zrobić. Możesz to zwizualizować w systemie i sprawdzić?
```

To był błąd projektu, nie mój. Claude przebudował panel tak, że sam uruchamia Claude Code w tle po dodaniu linku i pokazuje na żywo, co robi ("Szukam w Google...", "Czytam stronę...", "Rysuję kierunki marki"). Pierwszy zwiad trwał 8 minut i był lepszy od ręcznego.

**Wniosek, który warto zapamiętać:** gdy mówisz "nic się nie dzieje", to system ma to wykonać sam, a nie Ty masz się nauczyć komendy.

---

## Etap C: dwie warstwy ofert (3 godziny)

Próbki to dopiero połowa. Druga połowa to jak je podać i jak sprzedać współpracę. To zrobiłam najpierw ręcznie w osobnym oknie (dla tego samego klienta), potem dopięłam do generatora.

### C1. Prototyp ręczny

```
Chcę zaprojektować bardzo doświadczalny proces ofertowania tego prospekta. Dwie warstwy.

Pierwsza warstwa: wysłanie mu próbek w formie naszego konia trojańskiego, czyli landingu,
brandingu i redesignu Instagrama, tak żeby chciał umówić się na rozmowę sprzedażową.
Zaproponuj, w jakiej formie to przygotować. Pewnie to będzie strona, ale jak to opakować
i pokazać, jak te rzeczy się spajają, żeby naprawdę chciał z nami współpracować i żeby było
to doświadczenie, nie dokument.

Druga warstwa: proces ofertowania już naszej pełnej współpracy, czyli obsługi marketingowej
i całej reszty.

Zaproponuj najlepsze możliwe pomysły. Możesz użyć fal.ai, jeśli to konieczne.
```

Claude zapytał, czy klient mnie zna. Odpowiedź:

```
buduj to. Nie zna mnie, nie wie, że coś robię, pierwszy kontakt będzie na zimno.
```

A po warstwie pierwszej:

```
działaj z warstwą 2. Zrób 3 najmocniejsze przykładowe pakiety i wyceny tego, co możemy
zrobić jako agencja marketingowa i vibecodingowa dla studiów detailingu.
```

Co powstało: pokaz prywatny (jedna strona: animacja znaku, suwak Instagrama dziś i po zmianie, landing na żywo z kartą zapytania, przełącznik koloru, kalkulator, zaproszenie na rozmowę) i oferta współpracy (cele klienta jego słowami, mapa 90 dni, trzy pakiety z dodatkami, miesiąc treści, podglądy narzędzi, próg zwrotu, akceptacja).

### C2. Dopięcie do generatora

W oknie generatora:

```
Dorzuć do generatora te dwie warstwy ofert: pokaz na próbkę i ofertę po rozmowie sprzedażowej.
Zrobiliśmy je w innym oknie czatu, więc znajdź tamto okno i jego kontekst. Zbierz proces
generowania tych stron dla tego klienta i dołóż do generatora tak, żeby na końcu, po
wygenerowaniu wszystkich próbek, te dwie warstwy budowały się automatycznie tym samym
procesem.
```

Claude odnalazł tamtą sesję w historii, odczytał pliki i przerobił je na szablony. Ważne: Claude Code ma dostęp do historii Twoich innych okien, więc możesz łączyć pracę z kilku rozmów.

---

## Etap D: dokręcanie (2 godziny)

Wzorcowy klient zawsze wygląda dobrze, bo system był pisany pod niego. Prawdziwy test to nowy klient.

```
Dokręć to. Podszlifuj już to, co jest, dopracuj.
```

Z tak krótkiego polecenia Claude zrobił: kopię nowego klienta przez wszystkie etapy, zrzuty każdej strony na komputerze i telefonie, testy formularzy skryptem. Wyszło kilkanaście rzeczy do poprawy (łamanie słów w kaflach, nieczytelny tekst na jasnych zdjęciach, nieuczciwe etykiety). Jeśli chcesz, żeby to zadziałało tak samo u Ciebie, dodaj do promptu: "przepuść świeżego klienta przez wszystkie etapy, obejrzyj każdy wynik na zrzutach, przetestuj formularze".

Potem zapytałam:

```
Co teraz dalej można ulepszyć w tym generatorze?
```

Claude dał listę z rekomendacją kolejności. Pierwsza pozycja: publikacja i śledzenie, bo "najlepsza próbka jest bezwartościowa, jeśli zostaje na dysku". Wybrałam:

```
Dodaj publikację jednym kliknięciem i śledzenie prospekta. Tylko kursanci muszą móc wpisać
coś w Claude, żeby Claude wiedział, jak zainstalować się na ich domenie i serwerze.
Do tego koszt i czas per klient w panelu oraz cennik agencji w ustawieniach.
```

---

## Etap E: paczka dla innych (1 godzina)

```
Czy możesz wyeksportować to jako open source, żeby kursanci mogli to zainstalować
i rozwijać u siebie, pod swoje nisze?
```

Claude: skrypt eksportu (repozytorium bez klientów i sekretów), instalator, licencja, skill `/nowa-nisza` do tworzenia pakietu innej branży rozmową, walidator pakietu. Potem:

```
wepchnij na GitHub i daj link
```

Tu Claude potrzebował mojego klucza do GitHuba (dodałam go raz w ustawieniach GitHuba). Potem każda publikacja idzie bez pytania.

---

## Dziewięć zasad, które z tego wyszły

1. **Wzorzec ręcznie, potem generator.** Generator bez wzorca produkuje przeciętność.
2. **Jeden plik na klienta.** Wszystko o kliencie w jednym miejscu, każdy etap z niego czyta.
3. **Claude ocenia, skrypty powtarzają.** Zwiad, kierunki marki, słowa do klienta to Claude. Pliki, grafiki, strony to deterministyczny kod.
4. **Branża to plik.** Kod nie zna słowa "auto".
5. **Ty decydujesz w dwóch miejscach** (kierunek marki, usługa), reszta leci sama. Płatne kroki tylko po decyzji.
6. **System nie udaje, że wie.** Każda dana ma pewność, każda cena jest orientacyjna, dopóki ktoś jej nie potwierdzi.
7. **Weryfikacja zrzutem, nie zaufaniem.** Każdy etap kończy się obejrzeniem wyniku.
8. **Gdy mówisz "nic się nie dzieje", wina jest w projekcie.** System ma to zrobić sam.
9. **Pamięć między oknami.** Po każdej sesji proś Claude o notatkę: co powstało, gdzie leży, jakie pułapki. Bez tego trzy okna to trzy osobne projekty.

---

## Skrót: sześć promptów, żeby zbudować własny system

1. `Zrób ręcznie landing, logo i redesign Instagrama dla jednego prawdziwego klienta z mojej branży. Zapisz, co zadziałało.`
2. `Użyj skilla brainstorming. Chcę system, który robi to masowo z linku do Instagrama. Pytaj po jednym, zaproponuj architektury, nie pisz kodu bez mojej akceptacji.`
3. `Zbuduj rdzeń: jeden plik na klienta jako jedyne źródło prawdy, etapy, pakiet branży jako plik z całą treścią branżową.`
4. `Przerób moje trzy wzorce na szablony zasilane z pliku klienta. Każdy etap sprawdzaj zrzutem.`
5. `Zbuduj panel do decyzji i skill do zwiadu. Panel ma sam uruchamiać Claude w tle i pokazywać, co robi.`
6. `Dokręć: świeży klient przez wszystkie etapy, zrzuty, testy formularzy. Potem publikacja na serwer i śledzenie, czy prospekt otworzył.`

Każdy z tych promptów to kilka godzin pracy z Claude Code. Jeśli nie chcesz budować od zera, zainstaluj gotowego Konia Trojańskiego IA z tego repozytorium i zacznij od `/nowa-nisza`.
