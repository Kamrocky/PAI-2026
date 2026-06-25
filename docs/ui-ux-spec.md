# Specyfikacja UI/UX — CoinZen

Dokument opisuje **zaimplementowany** wygląd i zachowanie interfejsu aplikacji budżetowej. Służy jako punkt odniesienia przy dalszym rozwoju frontendu i API.

**Status:** as-built (v1.0)  
**Aplikacja:** CoinZen  
**Stack UI:** Django Templates + HTMX + Tailwind CSS (CDN)

---

## 1. Tożsamość wizualna

| Element | Stan |
|--------|------|
| **Nazwa** | **CoinZen** — logo w nagłówku, `<title>`, README |
| **Motyw** | Ciemny (nocny): `bg-zinc-950`, karty `border-white/10`, `bg-zinc-950/30` lub `bg-zinc-900/70` |
| **Akcent** | Emerald (`emerald-400` / `emerald-500`) — przyciski primary, aktywne zakładki |
| **Styl** | Nowoczesny, czytelny; bez osobnego SPA |

Tło dekoracyjne na ekranie auth: `partials/coinzen_auth_background.html`.

---

## 2. Nawigacja

### Zakładki główne (po zalogowaniu)

Górne zakładki (`partials/view_tabs.html`): **Home** → **Statystyki** → **Kategorie**.

| Widok | URL | Ładowanie |
|-------|-----|-----------|
| Home | `/` | SSR (Django view) |
| Statystyki | `/stats/` | SSR |
| Kategorie | `/categories/` | SSR |

### Poza zakładkami

| Element | Dostęp |
|---------|--------|
| **Profil** | Link z powitania w navbarze (`nav_greeting.html` → `/profile/`) |
| **Auth** | Shell bez zakładek — formularz email-first na `/` gdy niezalogowany |

### Navbar (zalogowany)

- Powitanie z imieniem (link do profilu)
- Przycisk **Wyloguj** (`POST /api/auth/logout`)
- Po loginie/rejestracji przez HTMX: OOB swap na `#user-info` (placeholder w `auth.html`)

---

## 3. Logowanie i rejestracja

Jeden przepływ **email-first**, krok po kroku (HTMX → `/api/auth/*`).

| Krok | Zachowanie |
|------|------------|
| 1 — email | Tylko pole email; `POST /api/auth/check-email` |
| 2a — istniejące konto | Pole hasła; `POST /api/auth/login` |
| 2b — nowe konto | Imię, hasło, powtórzenie; `POST /api/auth/register` |

**Zaimplementowane szczegóły:**

- Identyfikacja po **emailu** (`username` = email)
- Hasła z ikoną pokaż/ukryj (`password_input.html`, `togglePassword()` w `base.html`)
- Po sukcesie: treść Home w `#page-content`, navbar przez OOB, `HX-Push-Url: /`
- Walidacja: reguły Django + `auth_service` / `profile_forms`

---

## 4. Strona główna (Home)

### 4.1. Karuzela kont

- Konta w poziomej karuzeli ze strzałkami i kropkami (`account_carousel_dots.html`)
- Ostatni slot: **„+”** — utworzenie nowego konta
- Dla aktywnego konta: nazwa, saldo, waluta
- **Podsumowanie:** wpływy i wydatki za **ostatnie 30 dni** (`PERIOD_DAYS = 30`)
- **Porównanie:** bieżący vs poprzedni miesiąc kalendarzowy (komunikat tekstowy)

### 4.2. Edycja konta

- Ikona ołówka przy podsumowaniu konta
- Modal: zmiana nazwy, usunięcie z potwierdzeniem (CASCADE transakcji)
- **Waluty nie można zmienić** po utworzeniu
- Tworzenie konta: modal z wyborem waluty z listy (custom dropdown w `base.html`)

### 4.3. Transakcje

- Skrócona lista (domyślnie 5 pozycji) + **Rozwiń** → paginacja (10/strona)
- Kliknięcie wiersza → modal szczegółów (edycja, usuwanie)
- Saldo aktualizowane przy każdej operacji (`transaction_service`)

### 4.4. Dodawanie / edycja transakcji

Przycisk **„+”** nad listą → modal z polami:

| Pole | Zachowanie (as-built) |
|------|------------------------|
| Konto | Ukryte — zawsze **aktywne konto** z karuzeli (nowa transakcja) |
| Tytuł | Wymagany tekst |
| Kwota | Liczba; **ujemna = wydatek, dodatnia = wpływ** (podpowiedź pod polem) |
| Kategoria | Select; **filtrowany po znaku kwoty** (JS w modalu) |
| Opis | Opcjonalny |
| Data | `type="date"` — edytowalna; przy tworzeniu domyślnie „teraz” (bez osobnego pola godziny w UI) |

**Świadome odstępstwa od wcześniejszego planu:**

- Brak selecta **„Rodzaj”** (przychód/wydatek) — typ wynika ze znaku kwoty
- Brak **„+ Nowa kategoria”** w modalu transakcji — kategorie tylko na stronie Kategorie

---

## 5. Strona Kategorie

Osobny widok `/categories/` — CRUD w modalach HTMX.

| Funkcja | Szczegóły |
|---------|-----------|
| Lista | Podział na **Wydatki** i **Wpływy** (`category_grid.html`) |
| Dodawanie | Modal; przełącznik typu przychód/wydatek |
| Edycja | Nazwa + kolor z palety; **typ niezmienialny** po utworzeniu |
| Usuwanie | Potwierdzenie w modalu; transakcje: `SET NULL` na kategorii |
| Ikony | **Brak** — nie ma pola `icon` w modelu |
| Kolor | Siatka 12 kolorowych kółek (radio), walidacja w API |
| Alerty | Toast sukcesu (`ui_alerts.html`) po operacjach |

---

## 6. Strona Statystyki

Widok `/stats/` — analityka **per konto** (jedna waluta, bez mieszania).

### Wybór konta i okresu

- Karuzela kont (osobna sesja `stats_account_id` — niezależna od Home)
- Okresy: **Ten miesiąc**, **30 dni**, **3 miesiące**, **6 miesięcy**, **Rok** (domyślnie: 30 dni)
- Zmiana konta/okresu: HTMX `POST /api/ui/stats/*` → podmiana `#stats-content`

### KPI i wykresy (ApexCharts 3.49.1, CDN)

| Wykres | Typ | Treść |
|--------|-----|--------|
| Wpływy vs Wydatki | donut | Udział w wybranym okresie |
| Saldo w czasie | area | Saldo konta w czasie |
| Struktura wydatków | donut | % wg kategorii (kolory z palety) |
| Struktura wpływów | donut | % wg kategorii |
| Ostatnie 6 miesięcy | słupki | Wpływy i wydatki M−5…M |
| Rok do roku | słupki | Ten sam miesiąc: rok bieżący vs poprzedni |

Dane: `json_script:"stats-data"` + `stats_charts_script.html` (render przy SSR i po `htmx:afterSwap`).

**Poza zakresem v1.0:** zbiorcze statystyki ze wszystkich kont / przeliczanie walut.

---

## 7. Profil użytkownika

Widok `/profile/` (SSR), poza głównymi zakładkami. Link „Wróć” (`HTTP_REFERER`).

| Sekcja | Zachowanie |
|--------|------------|
| Imię | Edycja; odświeża powitanie w navbarze (OOB) |
| E-mail | **Tylko do odczytu** |
| Hasło | Zmiana z walidacją Pydantic; pola z pokaż/ukryj |
| Wyczyść dane | Usuwa konta, kategorie (transakcje przez CASCADE); konto użytkownika zostaje |
| Usuń konto | Potwierdzenie → wylogowanie + usunięcie użytkownika |

Akcje HTMX: `POST/DELETE /api/ui/profile/*` → podmiana `#profile-section`.

---

## 8. Waluty

- **20 walut** ISO 4217 w `ALLOWED_CURRENCIES` (`constants.py`)
- Przy tworzeniu konta: wybór z listy (dropdown, nie dowolny kod)
- Po utworzeniu: **brak edycji waluty**

---

## 9. Paleta kolorów kategorii

12 kolorów w `CATEGORY_COLOR_PALETTE` — walidacja w API (Pydantic / Ninja schemas).

| # | Hex | Nazwa wewn. |
|---|-----|-------------|
| 1 | `#7C9EB2` | slate (domyślny) |
| 2 | `#4DB6A0` | teal |
| 3 | `#6BC9A8` | mint |
| 4 | `#5B9BD5` | sky |
| 5 | `#7B8CDE` | indigo |
| 6 | `#9B7ED9` | violet |
| 7 | `#D97B8C` | rose |
| 8 | `#E8956A` | coral |
| 9 | `#E0B252` | amber |
| 10 | `#A8C66C` | lime |
| 11 | `#C4A77D` | sand |
| 12 | `#B48EAD` | mauve |

Ten sam kolor u **wielu kategorii jest dozwolony**. Brak natywnego color pickera i ręcznego wpisywania hex.

---

## 10. Wzorzec ładowania stron i API UI

| Warstwa | Rola |
|---------|------|
| Django views (`/`, `/categories/`, `/stats/`, `/profile/`) | Pierwsze wejście — pełny HTML (SSR) |
| HTMX `/api/ui/*` | Akcje użytkownika — podmiana fragmentów (modale, listy, formularze) |
| REST JSON `/api/accounts`, `/categories/`, `/transactions` | Kontrakt API, testy, Swagger (`/api/docs`) — **nie używany bezpośrednio przez szablony** |

Wspólne elementy HTMX: `#home-modal`, OOB swap (`ui_utils.MODAL_CLOSE_HTML`), CSRF w `htmx:configRequest`.

**Uzupełnienia poza czystym HTMX:** vanilla JS (dropdown walut, zamykanie modali, toggle hasła, filtrowanie kategorii w modalu transakcji), ApexCharts na statystykach.

---

## 11. Świadome odstępstwa i przyszłe usprawnienia

| Temat | Stan v1.0 |
|-------|-----------|
| Zbiorcze statystyki wielu walut | Nie zaimplementowane |
| Nowa kategoria z modala transakcji | Nie zaimplementowane |
| Select „Rodzaj” + dwukierunkowy sync z kwotą | Zastąpione znakiem kwoty + filtrem kategorii |
| Godzina w dacie transakcji | Tylko data w UI; model przechowuje `DateTimeField` |
| Przełącznik 30 dni / miesiąc kalendarzowy na Home | Stałe 30 dni + osobne porównanie miesiąc do miesiąca |

---

## 12. Kryteria akceptacji (stan na v1.0)

- [x] Ciemny motyw na wszystkich widokach
- [x] Logowanie email-first; rejestracja bez osobnej zakładki
- [x] Navbar po login/register (imię + wyloguj)
- [x] Home: karuzela kont, podsumowanie 30 dni, transakcje z paginacją i szczegółami
- [x] Transakcje przez `+`; kategorie filtrowane po znaku kwoty
- [ ] Nowa kategoria z modala transakcji *(poza zakresem v1.0)*
- [x] Kategorie: osobna strona; bez ikon; kolor z palety
- [x] Edycja/usunięcie konta z Home; bez zmiany waluty
- [x] Statystyki: wybór konta, okresu, wykresy kołowe, słupkowe i saldo w czasie
- [x] Waluta konta z predefiniowanej listy
- [x] Profil: imię, hasło, wyczyść dane, usuń konto

---

## 13. Dane demo

Komenda `python manage.py seed_demo --email USER [--months 5]` — przykładowe konta (wielowalutowe), kategorie i transakcje do testów UI i statystyk.

---

*Ostatnia aktualizacja: v1.0 as-built — zgodność z gałęzią refactor (SSR, profil, statystyki ApexCharts).*
