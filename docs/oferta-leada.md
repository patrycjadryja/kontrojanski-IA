# Oferta leada (oferta osobista)

Strona, którą osoba z reklamy dostaje zaraz po wypełnieniu formularza na landingu: zakres ochrony na rysunku auta, pakiety, cena, wizualizacja ze zdjęcia, wybór dnia.

## Polecenia

```
.venv/bin/python -m silnik.oferta_leada buduj <slug>     # buduje klienci/<slug>/oferta-leada/strona/
.venv/bin/python -m silnik.oferta_leada serwer 8901      # podgląd + wizualizacja ze zdjęcia + zapis zdarzeń
.venv/bin/python -m silnik landing <slug>                # po pierwszym "buduj": landing dostaje link do oferty
```

Podgląd: `http://localhost:8901/k/<slug>/oferta-leada/strona/index.html`
Parametry do testów: `?nadwozie=suv&kolor=bialy&pakiet=full-front`

## Pliki

| Plik | Rola |
|---|---|
| `nisze/<nisza>/oferta_leada.json` | strefy, pakiety, dodatki, ceny orientacyjne, teksty, prompty wizualizacji |
| `klient.json -> oferta_leada` | nadpisania klienta (realny cennik); listy podmieniają się w całości |
| `szablony/oferta-leada/index.html`, `_styl.css` | strona oferty (styl dziedziczy z kierunku brandingu) |
| `szablony/oferta-leada/_hak.html` | dokładka do landingu, wczytywana jedną linią `include` na końcu `landing/index.html` |
| `klienci/<slug>/oferta-leada/demo/` | `przed.jpg` + `po-<efekt>.jpg` = przykład wizualizacji dla strony bez serwera |
| `klienci/<slug>/oferta-leada/zdarzenia.csv` | otwarcia, zmiany zakresu, prośby o termin |

## Jak płyną dane

Formularz landingu -> link `index.html#o=<base64url JSON>` (imię, auto, rocznik, zakres, plany, termin; bez telefonu) -> strona oferty czyta kotwicę. Bez kotwicy pokazuje przykład z `oferta_leada.json -> przyklad`.

Typ nadwozia zgadywany z nazwy modelu (słownik `modele`), osoba może go zmienić. Ceny = cena bazowa x mnożnik nadwozia, zaokrąglone do 10 zł.

## Wizualizacja ze zdjęcia

Działa, gdy serwer ma klucz fal.ai: zmienna `FAL_KEY` albo plik `.fal_key` w folderze generatora. Model `fal-ai/nano-banana/edit`, około 0,04 USD i 10 s na obraz, limit 20 na godzinę. Bez klucza strona pokazuje przykład z folderu `demo/`.

## Przed wdrożeniem u klienta

- realny cennik studia w `klient.json -> oferta_leada` (strefy, pakiety, dodatki),
- gwarancja i trwałość folii wg karty produktu, której używa studio,
- stały adres serwera dla wizualizacji i zdarzeń (teraz tylko localhost),
- wysyłka SMS z linkiem (teraz link pokazuje się po formularzu, SMS jest tylko pokazany jako przykład).
