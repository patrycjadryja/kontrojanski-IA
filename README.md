# Koń Trojański IA

Generator próbek dla agencji marketingowej. Nazwa bierze się z metody: zamiast oferty wysyłasz prospektowi gotową próbkę jego nowej marki, a ta otwiera rozmowę od środka.

Z linku do Instagrama firmy powstają trzy rzeczy w jednym stylu: branding (3 kierunki do wyboru), redesign Instagrama i landing pod jedną ofertę wejściową. Na końcu dwie warstwy ofert: pokaz prywatny do wysłania na zimno i oferta współpracy po rozmowie. Wszystko z panelu w przeglądarce, zwiad robi Claude Code w tle.

Pierwsza nisza: studia detailingu. Własną branżę dodajesz rozmową z Claude (`/nowa-nisza`).

## Wymagania

- Mac albo Linux (Windows nietestowany)
- Python 3.9 lub nowszy
- Google Chrome (eksport grafik)
- [Claude Code](https://claude.com/claude-code) z aktywnym planem (zwiad w tle, kierunki marki, teksty)
- Opcjonalnie: konto fal.ai (film do landingu, wizualizacje znaku), hosting z SSH i PHP (publikacja pokazów), bot Telegram (powiadomienia)

## Instalacja

```
git clone https://github.com/patrycjadryja/kontrojanski-IA.git generator-agencji
cd generator-agencji
bash instaluj.sh
./panel.sh
```

Panel otwiera się pod `http://localhost:8900`. Instalator kopiuje skille do `~/.claude/skills/`, dzięki czemu Claude Code zna polecenia `/generator-agencji` i `/nowa-nisza`.

## Pierwszy klient

1. W panelu kliknij **Dodaj** i wklej link do Instagrama firmy.
2. Claude robi zwiad w tle (5-10 minut): dane, usługi, zdjęcia, diagnoza profilu, trzy kierunki marki. Postęp widać w panelu.
3. Wybierz kierunek marki. Pliki logo i paczka grafik na Instagram powstają same.
4. Wybierz ofertę wejściową. Landing, pokaz prywatny i oferta współpracy powstają same.
5. Ustawienia agencji: podpis, link do kalendarza, serwer, Telegram, pakiety i ceny.
6. **Wyślij pokaz na serwer** i skopiuj link dla prospekta. Panel pokazuje, co z nim zrobił.

Instagram nie oddaje zdjęć bez logowania. Claude próbuje przez Twojego Chrome'a (można wyłączyć w ustawieniach), potem przez stronę www firmy. Zdjęcia możesz też wgrać ręcznie w panelu.

## Przepływ

| Etap | Kto | Wynik |
|---|---|---|
| 1. Zwiad | Claude w tle | dane firmy, mapa usług, zdjęcia, diagnoza |
| 2. Branding | Claude, wybór w panelu | 3 kierunki, po wyborze komplet logo i księga znaku |
| 3. Instagram | silnik | strona propozycji przed/po, paczka PNG, ZIP |
| 4. Usługa | wybór w panelu | jedna oferta wejściowa z niskim progiem ceny |
| 5. Landing | silnik, film przez Claude | strona pod kampanię z formularzem oceniającym zapytania |
| 6. Pokaz prywatny | silnik | warstwa 1: strona spinająca próbki, wysyłana na zimno |
| 7. Oferta współpracy | silnik, dane z panelu | warstwa 2: interaktywna oferta po rozmowie |
| 8. Wdrożenie | panel + Claude | potwierdzone dane, formularz, piksel |

## Publikacja

Pokaz trafia na Twój serwer pod `<adres>/<klient>/`. Konfiguracja: Ustawienia agencji w panelu albo w Claude Code `podłącz serwer` (Claude przeprowadza przez SSH, klucz, katalog i instalację). Serwer musi mieć PHP, inaczej strony działają, ale liczniki wizyt i Telegram nie.

## Własna nisza

W Claude Code: `/nowa-nisza`. Claude pyta o branżę, usługi, oferty wejściowe i słownik, pisze `nisze/<id>/nisza.json` i sprawdza go: `.venv/bin/python -m silnik nisza-sprawdz <id>`. Schemat pakietu: `docs/nisza-schemat.md`. Nisza to wyłącznie plik JSON, silnik i szablony zostają bez zmian.

## Struktura

```
silnik/      skrypty (.venv/bin/python -m silnik pomoc)
panel/       serwer i interfejs panelu, agent w tle
szablony/    branding, instagram, landing, pokaz, oferta, pliki na serwer
nisze/       pakiety niszowe
skill/       skille dla Claude Code (instalator kopiuje je do ~/.claude/skills)
klienci/     folder na klienta, klient.json = jedno źródło prawdy (poza repozytorium)
docs/        specyfikacja i schemat niszy
```

`silnik/oferta_leada.py` to moduł opcjonalny: oferta osobista dla leada po formularzu (włączany per klient w karcie Landing, dziś tylko dla oferty PPF na strefy w niszy detailing). Wizualizacja ze zdjęcia przez fal.ai wymaga jego własnego serwera (`python -m silnik.oferta_leada serwer`), na hostingu PHP działa wersja statyczna z przykładem.

## Koszty

Zwiad jednego klienta to kilka minut pracy Claude Code (liczone w limicie Twojego planu). Film do landingu ok. 2 USD i wizualizacje znaku ok. 1 USD na fal.ai, oba tylko na zamówienie. Panel pokazuje koszt per klient.

## Rozwijanie

Pull requesty mile widziane. Zasady: polskie nazwy w kodzie i tekstach, bez półpauz (tylko "-"), formy neutralne płciowo, teksty do klienta bez obietnic liczbowych. Teksty branżowe trzymaj w pakiecie niszy, nie w kodzie.

Licencja: MIT.
