# Specyfikacja UI/UX — aplikacja finansowa

Dokument opisuje docelowy wygląd i zachowanie interfejsu. Służy jako punkt odniesienia przy kolejnych iteracjach frontendu i API.

**Status:** wersja robocza (v0.2)  
**Zastępuje:** obecny układ „wszystko na jednej stronie” z sekcjami CRUD pod dashboardem.

---

## 1. Tożsamość wizualna

| Element | Wymaganie |
|--------|-----------|
| **Nazwa aplikacji** | Inna niż „Budget App” / „Budżetówka” — nazwa robocza do ustalenia z zespołem (np. w README i `<title>`). |
| **Motyw** | **Ciemny (nocny)** — tło, karty, tekst i akcenty dopasowane do dark mode. |
| **Styl** | Nowoczesny, czytelny; HTMX + Tailwind (zgodnie z ADR). Bez osobnego SPA. |

---

## 2. Nawigacja — trzy główne widoki

Po zalogowaniu użytkownik porusza się między **trzema stronami** (np. dolny pasek lub górne zakładki):

| # | Widok | Opis skrócony |
|---|--------|----------------|
| 1 | **Strona główna** | Konta, transakcje, dodawanie transakcji, edycja kont |
| 2 | **Kategorie** | Zarządzanie kategoriami (bez ikon) |
| 3 | **Statystyki** | Wykresy i analizy dla wybranego konta (ew. zbiorczo) |

Strona logowania/rejestracji jest **osobna** — poza nawigacją aplikacji.

---

## 3. Logowanie i rejestracja (jeden przepływ, email)

Jeden ekran, **krok po kroku** — bez osobnych formularzy „Zaloguj” / „Zarejestruj”.

### Krok 1 — email

- Widoczne jest **tylko pole email**.
- Użytkownik wpisuje adres i przechodzi dalej (Enter / przycisk).

### Krok 2a — konto istnieje

- Pojawia się **pole hasła**.
- Logowanie po poprawnym haśle.

### Krok 2b — konto nie istnieje

- Pojawiają się pola:
  - **Imię** (wyświetlane w aplikacji, np. powitanie),
  - **Hasło**,
  - **Powtórz hasło**.
- Rejestracja po walidacji (zgodność haseł, reguły bezpieczeństwa Django).

### Uwagi techniczne (do implementacji później)

- Identyfikacja użytkownika po **emailu**, nie po `username`.
- Backend: endpoint sprawdzający istnienie konta po emailu + osobne kroki login/register (HTMX partials).

---

## 4. Strona główna

### 4.1. Pasek kont (u góry)

- **Lista kont** użytkownika w poziomym przewijaniu.
- **Strzałki** w lewo / prawo do przesuwania, gdy kont nie mieści się na ekranie.
- Dla **aktywnego (wybranego) konta** widoczne:
  - **Nazwa konta**
  - **Saldo** (waluta konta)
  - **Krótkie podsumowanie** za **bieżący miesiąc kalendarzowy** *lub* **ostatnie 30 dni** (do ustalenia w implementacji — domyślnie proponujemy *ostatnie 30 dni*):
    - suma **wpływów** (przychody),
    - suma **wypływów** (wydatki).
- **Porównanie miesięczne** na tym koncie:
  - wydatki i przychody z **bieżącego** okresu vs **poprzedniego** miesiąca (np. „−12% wydatków względem poprzedniego miesiąca”).

### 4.2. Edycja konta (na stronie głównej)

- Przy każdym koncie: **mała ikona ołówka**.
- Po kliknięciu — panel / modal edycji:
  - zmiana **nazwy** konta,
  - **usunięcie konta** (z potwierdzeniem; **CASCADE** — usuwa wszystkie powiązane transakcje).
- **Waluty konta nie edytujemy** po utworzeniu (unikamy problemów z przeliczeniami i historią).

### 4.3. Transakcje (pod aktywnym kontem)

- Domyślnie: **ostatnie transakcje** (skrócona lista).
- **Rozwinięcie**: pełna lista z **paginacją**.
- **Kliknięcie w transakcję** → widok szczegółów:
  - wszystkie pola,
  - **edycja**,
  - **usunięcie** (z aktualizacją salda).

### 4.4. Dodawanie transakcji

- **Jedyny punkt wejścia:** mały przycisk **„+”** nad listą transakcji.
- Otwiera **modal** (okno) z polami:

| Pole | Zachowanie |
|------|------------|
| **Konto** | Select; domyślnie **aktualnie przeglądane** konto. |
| **Rodzaj** | Przychód / wydatek — powiązany ze znakiem kwoty (patrz niżej). |
| **Kwota** | Liczba; znak `+` / `−` zsynchronizowany z rodzajem. |
| **Data i godzina** | Domyślnie **teraz**; edytowalne. |
| **Kategoria** | Tylko kategorie **zgodne z rodzajem** (przychód → kategorie przychodów, wydatek → wydatków). |

#### Synchronizacja rodzaju ↔ kwota

- Wpisanie kwoty **ujemnej** → rodzaj **wydatek**; dodatniej → **przychód**.
- Zmiana rodzaju w selectcie → **dostosowanie znaku** przed kwotą (np. wydatek wymusza `−`).

#### Nowa kategoria w trakcie dodawania transakcji

- W selectcie kategorii: opcja **„+ Nowa kategoria”** → proste **pole tekstowe** (nazwa).
- Kategoria **nie zapisuje się od razu** — tworzy się **dopiero przy zatwierdzeniu transakcji**.
- Typ nowej kategorii = aktualny **rodzaj transakcji** (przychód/wydatek).
- Kolor nowej kategorii: **automatyczny wybór z palety** (patrz §8) — pierwszy wolny kolor lub domyślny; użytkownik **nie wpisuje** kodu hex/RGB.

---

## 5. Strona „Kategorie”

Osobny widok — **bez** zarządzania kategoriami na stronie głównej (poza szybkim dodaniem w modalu transakcji).

### Funkcje

- Lista wszystkich kategorii użytkownika (podział na przychody / wydatki).
- **Dodawanie** kategorii (nazwa, typ przychód/wydatek, **kolor z palety**).
- **Edycja** (nazwa, **kolor z palety**; typ zwykle stały po utworzeniu — do ustalenia).
- **Usuwanie** (transakcje: `SET NULL` lub blokada jeśli kategoria używana — zgodnie z modelem).

### Usunięte z obecnej wersji

- **Ikony kategorii** — nie implementujemy; pole `icon` do usunięcia z modelu/UI w przyszłej migracji.
- **Ręczne wpisywanie koloru** (hex, RGB, color picker z dowolną wartością) — zastąpione **paletą predefiniowaną** (patrz §8).

### Wybór koloru w UI

- Zamiast pola tekstowego `#RRGGBB`: **siatka kolorowych kółek / kafelków** do kliknięcia.
- Kolory już przypisane innym kategoriom mogą być wizualnie oznaczone (np. przyciemnione + tooltip „używane”), ale **ten sam kolor u dwóch kategorii jest dozwolony** — do ustalenia przy implementacji.
- Na liście kategorii i w transakcjach: kolor jako mały **znacznik** (kropka / pasek), spójny z wykresami na stronie Statystyki (kolory z §8).

---

## 6. Strona „Statystyki”

Trzeci widok analityczny.

### Wejście

- **Wybór konta** do analizy (select lub ten sam karuzelowy pasek co na głównej).
- Opcjonalnie (faza późniejsza): **zbiorcze zestawienie wszystkich kont** — uwaga na **różne waluty** (patrz §9).

### Zakres czasu

- Wybór okresu (np. bieżący miesiąc, ostatnie 30 dni, własny zakres) — szczegóły UI do doprecyzowania.

### Wykresy i metryki

| Wizualizacja | Treść |
|--------------|--------|
| **Kołowy — przychody vs wydatki** | Udział wpływów i wypływów w wybranym okresie (dla konta). |
| **Kołowy — kategorie wydatków** | % struktury wydatków wg kategorii (kolory z palety §8). |
| **Kołowy — kategorie przychodów** | % struktury przychodów wg kategorii (kolory z palety §8). |
| **Słupkowy — miesiąc do miesiąca** | Porównanie np. sum wydatków/przychodów M vs M−1. |
| **Słupkowy — rok do roku** | Porównanie tego samego miesiąca rok wcześniej vs bieżący. |

Biblioteka wykresów: do wyboru (np. Chart.js przez CDN, Alpine + canvas) — poza zakresem tego dokumentu.

---

## 7. Waluty

- **Stała lista** ~**20 najpopularniejszych** walut (ISO 4217), np. PLN, EUR, USD, GBP, CHF, CZK, …
- Przy **tworzeniu konta**: wybór z listy (select), **bez** dowolnego wpisywania trzyliterowego kodu.
- **Brak zmiany waluty** po utworzeniu konta.

---

## 8. Paleta kolorów kategorii

Kolor kategorii wybiera się **wyłącznie z ustalonej palety** — tak jak walutę z listy. Użytkownik **nie wpisuje** kodów hex ani RGB; brak natywnego color pickera z dowolnym kolorem.

### Zasady

| Zasada | Opis |
|--------|------|
| **Stała lista** | Ograniczona liczba kolorów (propozycja: **12–16** odcieni). |
| **Dark mode** | Odcienie **nasycone, ale nie neonowe** — dobra czytelność na ciemnym tle (`#1a1a2e`–`#2d2d44` itd.). |
| **Spójność** | Paleta zaprojektowana **jako całość** — kolory harmonizują ze sobą i z wykresami kołowymi. |
| **Kontrast** | Przy kropce kategorii obok jasnego tekstu: wystarczający kontrast; unikać bardzo ciemnych tonów zlewających się z tłem. |
| **Backend** | W bazie nadal przechowujemy hex (np. `#7C9EB2`), ale API **akceptuje tylko wartości z palety** — walidacja po stronie serwera. |

### UI wyboru koloru

- **Strona Kategorie** (dodawanie / edycja): rząd lub siatka **klikalnych próbek**; zaznaczenie ramką / checkmarkiem.
- **Modal transakcji** (nowa kategoria): jeśli użytkownik podaje tylko nazwę — kolor **domyślny z palety** (np. pierwszy nieużywany lub stały domyślny per typ przychód/wydatek).
- **Brak** pola `<input type="color">` z pełnym spektrum i **brak** ręcznego wpisywania `#...`.

### Paleta robocza (v0.2 — do ewentualnej korekty przy wdrożeniu dark theme)

Kolory dobrane pod **ciemny motyw** (stonowane, rozróżnialne na wykresach):

| Nazwa (wewn.) | Hex | Użycie wizualne |
|---------------|-----|-----------------|
| `slate` | `#7C9EB2` | neutralny, domyślny |
| `teal` | `#4DB6A0` | przychody / oszczędności |
| `mint` | `#6BC9A8` | przychody |
| `sky` | `#5B9BD5` | ogólne |
| `indigo` | `#7B8CDE` | ogólne |
| `violet` | `#9B7ED9` | rozrywka |
| `rose` | `#D97B8C` | zakupy / wydatki osobiste |
| `coral` | `#E8956A` | jedzenie |
| `amber` | `#E0B252` | transport |
| `lime` | `#A8C66C` | zdrowie / sport |
| `sand` | `#C4A77D` | rachunki |
| `mauve` | `#B48EAD` | subskrypcje |

*Implementacja: jedna stała `CATEGORY_COLOR_PALETTE` w backendzie + ten sam zestaw w szablonach.*

---

## 9. Ograniczenia i decyzje otwarte

| Temat | Uwaga |
|-------|--------|
| **Agregacja wielu walut** | Sumowanie sald / wykresów ze wszystkich kont naraz jest **problematyczne** — na razie statystyki **per konto**; zbiorczy widok jako opcja późniejsza (np. tylko w PLN po kursie NBP). |
| **Okres „miesiąc” vs „30 dni”** | Na głównej: ustalić jedną domyślną definicję i ewentualny przełącznik. |
| **Nazwa aplikacji** | Do ustalenia z zespołem przed wdrożeniem brandingui. |
| **Data transakcji** | Model ma dziś `auto_now_add` — docelowo **edytowalna data/godzina** wymaga zmiany modelu (`date` bez `auto_now_add` lub osobne pole). |
| **Auth po emailu** | Wymaga zmian backendu (User.email jako login, flow krokowy). |
| **Powtórzenie koloru** | Czy dwie kategorie mogą mieć ten sam kolor z palety — do ustalenia (wpływ na czytelność wykresów). |

---

## 10. Mapowanie: obecny stan → docelowy

| Obecnie | Docelowo |
|---------|----------|
| Jedna strona: dashboard + 3 sekcje CRUD | 3 widoki + modal transakcji |
| Login + rejestracja obok siebie | Jeden flow email → hasło / rejestracja |
| `username` | Email + imię |
| Jasny motyw (Tailwind gray/white) | Ciemny motyw |
| Ikona kategorii | Usunąć |
| Dowolny kod waluty w formularzu | Select z listy ~20 walut |
| Wszystkie kategorie w jednym formularzu transakcji | Filtrowanie po typie przychód/wydatek |
| Edycja konta w sekcji „Konta” | Ołówek przy koncie na stronie głównej |
| Dowolny hex kategorii (`#RRGGBB` w formularzu) | Paleta 12 kolorów, wybór kliknięciem w siatce |
| Brak wykresów | Strona Statystyki |

---

## 11. Kolejność implementacji (sugestia)

1. **Dark theme** + nowa nazwa + szkielet 3 stron (nawigacja).
2. **Auth email-first** (backend + HTMX).
3. **Strona główna** — karuzela kont, podsumowanie 30 dni, lista transakcji + modal `+`.
4. **Model:** edytowalna data transakcji; usunięcie `icon` z kategorii; lista walut; **paleta kolorów** + walidacja w API.
5. **Strona kategorii** — CRUD z wyborem koloru z palety (siatka kafelków).
6. **Strona statystyk** — zapytania agregujące + wykresy.
7. Porównania miesiąc do miesiąca na głównej i w statystykach.

---

## 12. Kryteria akceptacji (skrót)

- [ ] Ciemny motyw na wszystkich widokach.
- [ ] Logowanie zaczyna się od emaila; rejestracja bez osobnej zakładki.
- [ ] Główna: przewijane konta, podsumowanie wpływów/wypływów, transakcje z paginacją i szczegółami.
- [ ] Transakcje dodawane tylko przez `+` w modalu; sync kwota ↔ rodzaj; kategorie filtrowane po typie.
- [ ] Nowa kategoria z modala transakcji zapisuje się razem z transakcją.
- [ ] Kategorie: osobna strona; bez ikon; **kolor tylko z predefiniowanej palety** (bez wpisywania hex/RGB).
- [ ] Paleta: kolory czytelne na ciemnym tle i spójne z wykresami.
- [ ] Edycja/usunięcie konta z ołówka na głównej; bez zmiany waluty.
- [ ] Statystyki: wybór konta + wykresy kołowe i słupkowe.
- [ ] Waluta konta z predefiniowanej listy.

---

*Ostatnia aktualizacja: paleta kolorów kategorii (v0.2).*
