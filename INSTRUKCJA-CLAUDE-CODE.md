# Koń Trojański IA - instrukcja dla Claude Code

Ten plik jest dla Claude Code osoby, która dostała paczkę. Przeczytaj go w całości, zanim cokolwiek uruchomisz. Potem przeczytaj `README.md`, `docs/2026-09-29-generator-agencji-spec.md` i `docs/oferta-leada.md`.

## Co to jest

System dla agencji marketingowej obsługującej studia (pierwsza nisza: auto detailing). Z linku do Instagrama studia powstają próbki w jednym stylu:

| Etap | Wynik |
|---|---|
| 1. Zwiad | dane studia, mapa usług, diagnoza profilu |
| 2. Branding | 3 kierunki, po wyborze komplet logo i księga znaku |
| 3. Instagram | strona propozycji przed/po, paczka grafik PNG |
| 4. Oferta wejściowa | jedna usługa z niskim progiem ceny |
| 5. Landing | strona pod kampanię Meta Ads z formularzem kwalifikującym |
| 6. Pokaz prywatny | warstwa 1: strona spinająca próbki, wysyłana prospektowi na zimno, z licznikami wizyt |
| 7. Oferta współpracy | warstwa 2: interaktywna oferta agencji po rozmowie sprzedażowej |
| 8. Wdrożenie | potwierdzone dane, realny cennik, formularz, piksel |

Etapy 6-7 w panelu to dwie warstwy ofert: pokaz prywatny (strona spinająca próbki, wysyłana na zimno) i oferta współpracy (po rozmowie). Moduł "oferta leada" (`silnik/oferta_leada.py`, `docs/oferta-leada.md`) jest eksperymentalny i nie jest wpięty w panel.

## Instalacja i praca

Instalacja: `bash instaluj.sh` (tworzy `.venv`, instaluje zależności, kopiuje skille do `~/.claude/skills/`). Panel: `./panel.sh` -> `http://localhost:8900`.

Pełne instrukcje pracy są w skillach, które instalator kopiuje:
- `skill/generator-agencji/SKILL.md`: zwiad, kierunki marki, Instagram, landing, film, pokaz, publikacja, podłączenie serwera, wdrożenie.
- `skill/nowa-nisza/SKILL.md`: jak zbudować pakiet dla innej branży.

Przeczytaj je przed pierwszym klientem. Wszystkie polecenia silnika: `.venv/bin/python -m silnik pomoc`. Schemat pakietu niszy: `docs/nisza-schemat.md`. Specyfikacja i historia decyzji: `docs/2026-09-29-generator-agencji-spec.md`.

## Zasady, których nie zmieniasz bez pytania

- Landing zawsze sprzedaje jedną ofertę wejściową z niskim progiem ceny, nigdy najdroższą usługę.
- Płatne kroki (fal.ai) tylko na wyraźne zamówienie z panelu.
- Teksty do klienta: bez półpauz (tylko "-"), formy neutralne płciowo, bez obietnic liczbowych, stopka z ujawnieniem projektu koncepcyjnego zostaje.
- Teksty branżowe trzymaj w pakiecie niszy (`nisze/<id>/nisza.json`), nie w kodzie ani szablonach.
