# Pakiet niszy: schemat `nisze/<id>/nisza.json`

Wzorzec: `nisze/detailing/nisza.json`. Wszystkie teksty są po polsku, dla klienta końcowego branży. W tekstach `*słowo*` oznacza słowo w kolorze akcentu, a `{nazwa}`, `{nazwa_krotka}`, `{miasto}`, `{cena_tekst}`, `{liczba_opinii}`, `{oferta_nazwa}`, `{oferta_biernik}`, `{kierunek}` są podstawiane danymi klienta.

| Klucz | Co zawiera |
|---|---|
| `id`, `nazwa`, `nazwa_klienta` | identyfikator, nazwa branży, jak nazywać klienta agencji (np. "salon fryzjerski") |
| `zasada_oferty` | jedno zdanie, dlaczego landing sprzedaje ofertę wejściową |
| `uslugi_slownik[]` | usługi branży: `id`, `nazwa`, `skrot` (do 10 znaków, na okładkę relacji), `typ` (premium / srednia / wejsciowa), `slowa[]` (do rozpoznania usługi w bio i na stronie), `cena_rynek` |
| `oferty_wejsciowe[]` | przynęty z niskim progiem ceny, patrz niżej |
| `branding.archetypy[]`, `branding.zasady[]` | wskazówki dla Claude przy projektowaniu trzech kierunków |
| `instagram.diagnoza_typowa[]`, `haslo`, `lead`, `poradniki{}` | domyślna diagnoza profilu i treści karuzel per usługa (`domyslny` obowiązkowy) |
| `pokaz{}` | teksty pokazu prywatnego: `kurtyna`, `znak` (per motyw logo + `fakty`, `uwaga_wiz`), `instagram`, `strona`, `system`, `liczby`, `rozmowa`, `stopka`, `styl_wizualizacji`, `wizualizacje[]` |
| `oferta{}` | oferta agencji po rozmowie: `pakiety[3]`, `dodatki[]`, `mapa[3]`, `tresci_wzor[24]`, `tresci_tytuly{}`, `narzedzia{}`, `zasady{}`, `start_14[]`, `cele_przykladowe[3]`, `polecany`, `budzet_reklamowy`, `start`, `intro`, `naglowek` |
| `slownik{}` | słowa zależne od branży używane przez silnik |
| `zwiad_podpowiedzi[]` | na co Claude ma zwrócić uwagę w zwiadzie tej branży |

## Oferta wejściowa

```
id, nazwa, krotko, dla_uslug[] (id usług klienta, przy których ta oferta pasuje),
prowadzi_do[] (id usług premium, do których prowadzi), dlaczego, cena_od, cena_tekst, czas,
fraza: {mianownik, biernik},
tresc: {
  title, opis_meta, eyebrow, nav_cta, menu[[etykieta, #kotwica]],
  sceny[6]: {naglowek, tekst, podpis?, cta?[1-2]},
  realizacje: {etykieta, naglowek, lead},
  pakiety: {etykieta, naglowek, lead, lista[3]: {nazwa, etykieta, punkty[], cena, wyrozniony?}, uwaga},
  proces: {etykieta, naglowek, lead, kroki[4]: {czas, tytul, tekst, kadr (numer kadru 1-6)}},
  dowod: {naglowek, lead, naglowek_bez_ocen, lead_bez_ocen},
  formularz: {etykieta, naglowek, lead, korzysci[3][2], kroki[4]: {nazwa, pytanie, podpowiedz, pola[]}, prog_priorytetu, dzialania{priorytet, standard}},
  faq[[pytanie, odpowiedz]], zamkniecie{naglowek, cta}, stopka_opis
},
storyboard[6]: {plik, tytul, prompt (EN, z {auto} i {akcent}), ruch}
```

Pola formularza: `{typ: "tekst", id, etykieta, przyklad, min, blad}`, `{typ: "lista"|"wybor", id, etykieta, blad, opcje[[etykieta, punkty, dopisek?]]}`. Suma punktów wybranych opcji porównana z `prog_priorytetu` decyduje o ocenie PRIORYTET / STANDARD. Krok "Kontakt" (imię, telefon, zgoda) silnik dodaje sam.

## Sprawdzenie

`.venv/bin/python -m silnik nisza-sprawdz <id>` wypisuje błędy struktury. Potem przepuść klienta testowego przez wszystkie etapy i obejrzyj wyniki.
