---
name: nowa-nisza
description: Tworzy nowy pakiet niszowy dla Konia Trojańskiego IA (nisze/<id>/nisza.json) rozmową z użytkownikiem. Używaj, gdy padnie "nowa nisza", "dodaj niszę", "chcę robić to dla fryzjerów / klinik / studiów tatuażu / restauracji", "przerób generator pod moją branżę".
---

# Nowa nisza dla Konia Trojańskiego IA

Folder systemu: katalog, w którym jest `panel.sh` (zwykle `~/generator-agencji`). Wzorzec: `nisze/detailing/nisza.json`. Schemat z objaśnieniami: `docs/nisza-schemat.md`. Sprawdzenie: `.venv/bin/python -m silnik nisza-sprawdz <id>`.

## Rozmowa (jedno pytanie naraz)

1. **Branża i klient końcowy.** Kto jest klientem agencji (np. salon fryzjerski) i kto jest klientem tego klienta (osoba, która przychodzi do salonu). Zapisz po polsku bez odmian trudnych do podstawienia.
2. **Usługi w branży.** Poproś o 8-13 typowych usług z podziałem: premium (drogie, sprzedawane po zaufaniu), średnia półka, wejściowe (tanie, szybka decyzja). Jeśli użytkownik nie zna cen rynkowych, zrób WebSearch i podaj widełki jako orientacyjne.
3. **Oferty wejściowe.** Zaproponuj 3-4 przynęty z niskim progiem ceny, które prowadzą do usług premium. Dla każdej: nazwa, cena od, czas, do jakich usług prowadzi, dlaczego działa. Użytkownik wybiera i poprawia.
4. **Słownik.** Jak nazywać firmę klienta (studio / salon / klinika / restauracja) i obiekt pracy (auto / włosy / uśmiech / danie). Zapytaj o formy: mianownik i dopełniacz obu.
5. **Pakiety agencji.** Zapytaj, czy pakiety z detailingu (Instagram i strona / Zapytania co miesiąc / Pełna obsługa) pasują, czy zmienić nazwy i ceny. Narzędzia w pakiecie 3 (panel klienta, karta gwarancyjna, kalkulator) przetłumacz na realia branży (np. karta zabiegu, przypomnienie o wizycie).

## Pisanie pakietu

Skopiuj `nisze/detailing/nisza.json` do `nisze/<id>/nisza.json` i przepisz wszystkie teksty. Nie zostawiaj słów z detailingu (lakier, auto, folia, studio) poza polami, gdzie tak zdecydował użytkownik. Zasady:

- `id` niszy = małe litery i myślniki, bez polskich znaków.
- Każda oferta wejściowa ma 6 scen (pierwsza z dwoma CTA, ostatnia z jednym), 3 pakiety (jeden `wyrozniony`), 4 kroki procesu, formularz z 4 krokami (pierwszy z polem `tekst`, punktacja w opcjach), 4 pytania FAQ, 6 kadrów storyboardu z promptami po angielsku z `{auto}` zamienionym na obiekt branży i `{akcent}` jako kolorem światła. Kadry 1 i 6 zostawiają pustą przestrzeń na tekst (kadr 1 po lewej, kadr 6 po prawej).
- `fraza.mianownik` i `fraza.biernik` oferty: użyte w zdaniach "zapytania o ..." i "strona: ...". Sprawdź odmianę.
- `pokaz.znak`: pięć opowieści o motywie logo (refleks, belka, punkt, rama, ciecie) w języku branży. Refleks to smuga światła, belka to linia, punkt to zakończenie, rama to tabliczka, cięcie to precyzja.
- `pokaz.wizualizacje`: 7 nośników znaku typowych dla branży (szyld, wizytówka, strój, opakowanie, drobiazg dla klienta, detal). Prompty po angielsku, z "the exact logo from the reference image".
- `pokaz.liczby`: suwaki kalkulatora z sensownymi zakresami dla branży (średnia wartość klienta w roku).
- `oferta.tresci_wzor`: 24 typy publikacji w miesiącu. `oferta.tresci_tytuly`: tytuły poradników z `*słowem*` w akcencie.
- `oferta.narzedzia`: przykładowe nazwy klientów końcowych (zamiast modeli aut), etapy realizacji (6), wielkości/warianty do kalkulatora (3).
- `slownik`: firma, firmy, firmie, obiekt, obiektu, obiektem, realizacja_opis, split_podpis, probka_tytulu, probka_posta, brak_zdjec, przyklad_klienta.
- Styl tekstów: krótkie zdania, bez półpauz (tylko "-"), bez obietnic liczbowych, formy neutralne płciowo.

## Sprawdzenie

1. `.venv/bin/python -m silnik nisza-sprawdz <id>` musi zwrócić "OK".
2. Załóż klienta testowego z tą niszą: `.venv/bin/python -m silnik dodaj "Test <branża>"`, wpisz w `klient.json` `"nisza": "<id>"`, kilka usług i trzy kierunki (skopiuj z Imperial), wgraj 3-4 zdjęcia do `zwiad/zdjecia/`, uruchom `branding-final`, `instagram`, `landing <slug> <oferta>`, `pokaz`. Obejrzyj zrzuty. Usuń klienta testowego po sprawdzeniu.
3. Powiedz użytkownikowi, które teksty są Twoim domysłem (ceny, nazwy usług) i co ma potwierdzić.
