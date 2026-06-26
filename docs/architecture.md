# Architektura

Dokument opisuje architekturę aplikacji CoinZen: warstwy, przepływ żądania, podział na
API JSON i warstwę HTMX oraz renderowany interfejs.

## Przegląd

CoinZen jest **monolitem Django**, który serwuje jednocześnie:

1. **REST API (JSON)** - pełnoprawny, udokumentowany interfejs zasobów.
2. **Warstwę UI (HTMX)** - endpointy zwracające fragmenty HTML renderowane po stronie serwera.

Obie warstwy są zbudowane na **Django Ninja** i zamontowane pod wspólnym prefiksem `/api`
w [`finance/api.py`](../backend/finance/api.py). Współdzielą tę samą logikę domenową
(serwisy i funkcje pomocnicze), więc nie ma duplikacji reguł biznesowych.

```
Przeglądarka (HTMX + Tailwind + ApexCharts)
        │
        │  HTTP
        │   ├─ GET /                      → pełna strona (shell HTML)
        │   ├─ GET/POST /api/ui/...       → fragmenty HTML  (warstwa UI)
        │   └─ POST /api/auth/...         → logowanie / sesja
        ▼
┌─────────────────────────────────────────────────────────┐
│ Django                                                   │
│                                                          │
│  views.py ──── renderuje "shell" strony (layout + tabs)  │
│                                                          │
│  api.py ─────── montuje routery Django Ninja pod /api    │
│   ├─ api_*.py      REST JSON  (/api/accounts, ...)       │
│   ├─ ui_*.py       fragmenty HTML (/api/ui/...)          │
│   └─ api_auth.py   sesje (/api/auth/...)                 │
│                                                          │
│  *_service.py - logika domenowa (salda, statystyki...)   │
│  *_forms.py ─── walidacja formularzy (Pydantic)          │
│  schemas.py ─── schematy Pydantic dla API                │
│  models.py ──── modele ORM                               │
└─────────────────────────────────────────────────────────┘
        │
        ▼
   PostgreSQL  (Django ORM + migracje)
```

## Dwie warstwy API

Pod jednym prefiksem `/api` istnieją **dwie równoległe warstwy**,
obie jako routery Django Ninja.

| Warstwa | Endpointy | Zwraca | Konsument |
|---|---|---|---|
| **REST JSON** | `/api/accounts`, `/api/categories`, `/api/transactions` | JSON | testy, Swagger, zewnętrzne integracje |
| **UI / HTMX** | `/api/ui/home`, `/api/ui/categories`, `/api/ui/stats`, `/api/ui/profile` | fragmenty HTML | przeglądarka (HTMX) |
| **Auth** | `/api/auth/...` | HTML / sesja | przeglądarka (HTMX) |

### REST JSON API
Czysty interfejs CRUD na zasobach, walidowany schematami Pydantic, zwracający JSON
(oraz `422` przy błędnych danych). Jest **wystawiony, działający oraz przetestowany**
(`finance/tests/test_api.py`) i udokumentowany automatycznie w Swaggerze pod `/api/docs`.
Stanowi API-first kontrakt aplikacji.

### Warstwa UI (HTMX)
Endpointy `ui_*.py` nie zwracają JSON, lecz **gotowe fragmenty HTML**. One są prezentowane w
przeglądarce. Interaktywność (dodawanie, edycja, usuwanie, filtrowanie, przełączanie kont)
realizują atrybuty `hx-get` / `hx-post` / `hx-delete`, a HTMX podmienia zwrócony fragment
w drzewie DOM, bez przeładowania strony i bez budowania frontendu.

### Współdzielona logika
Obie warstwy korzystają z tych samych funkcji domenowych - `ui_home.py` i `ui_categories.py`
importują `get_user_account`, `get_user_category`, `get_user_transaction` z modułów `api_*.py`,
a operacje na transakcjach przechodzą przez `transaction_service.py`.
Dzięki temu REST API nie jest "martwym kodem", a reguły biznesowe nie są zduplikowane.


## Przepływ żądania

### Pełne wejście na stronę (np. `/stats/`)
1. Przeglądarka żąda `GET /stats/`.
2. `views.py` sprawdza, czy użytkownik jest zalogowany. Jeśli nie, renderuje shell logowania.
3. Jeśli tak, renderuje „shell" strony (layout, zakładki, nagłówek), w którym treść jest doczytywana: `<div hx-get="/api/ui/stats" hx-trigger="load">`.
4. HTMX natychmiast wykonuje `GET /api/ui/stats`, który zwraca fragment z danymi, wykresami i wstawia go na miejsce.

### Akcja użytkownika (np. dodanie kategorii)
1. Formularz z `hx-post="/api/ui/categories"`.
2. Endpoint `ui_categories.py` waliduje dane (`category_forms.py` -> Pydantic). Błąd -> fragment
   z komunikatem. Sukces -> zapis przez ORM.
3. Zwracany jest zaktualizowany fragment listy kategorii, który HTMX podmienia w DOM.

### Renderowanie
Renderowanie jest **server-side**, endpoint UI woła `render_to_string()` na szablonie Django
i zwraca HTML. Przeglądarka nie buduje widoku z JSON, a dostaje gotowy fragment.

## Warstwy logiczne

- **Widoki stron - `views.py`**
  Renderują „shell" strony dla zalogowanych, a dla niezalogowanym pokazują ekran logowania.
- **Routery API - `api.py` + `api_*.py` / `ui_*.py`**
  Warstwa HTTP. `api_*.py` zwracają JSON, `ui_*.py` zwracają fragmenty HTML.
- **Serwisy - `*_service.py`**
  Logika domenowa odseparowana od HTTP: `transaction_service`,
  `home_service`, `stats_service`, `profile_service`, `categories_service`.
- **Walidacja - `schemas.py` + `*_forms.py`**
  Schematy Pydantic. API waliduje automatycznie, warstwa UI używa tych samych schematów
  przez moduły `*_forms.py` i zwraca czytelne komunikaty.
- **Modele - `models.py`**
  `Account`, `Category`, `Transaction`, wbudowany `User`.


## Model danych

```
User (1) ──< (N) Account (1) ──< (N) Transaction (N) >── (1) Category
```

- `User -> Account` - konto należy do użytkownika (CASCADE).
- `Account -> Transaction` - transakcja należy do konta (CASCADE).
- `Transaction -> Category` - opcjonalna kategoria (`SET NULL` przy usunięciu kategorii).

Saldo konta jest utrzymywane przez `transaction_service` przy każdej operacji na transakcji.
Pełny opis: [`database-schema.md`](database-schema.md).

## Autentykacja i izolacja danych

- **Sesje Django.** Logowanie / rejestracja / wylogowanie w `api_auth.py`.
- **Ochrona endpointów.** `get_authenticated_user` (`auth_utils.py`) odrzuca niezalogowanych
  (HTTP `401`), a widoki stron pokazują ekran logowania zamiast treści.
- **Izolacja per użytkownik (per-row).** Każde zapytanie filtruje po właścicielu:
  `filter(user=user)` dla kont/kategorii, `filter(account__user=user)` dla transakcji.
  Pobrania pojedynczych rekordów zwracają `404` dla cudzych zasobów. Brak wycieku danych
  między użytkownikami jest weryfikowany testami integracyjnymi.

## Decyzje architektoniczne

- **HTMX zamiast SPA.** Brak osobnego frontendu i kroku budowania - szybszy development,
  jeden język po stronie serwera, prosty deployment. Interaktywność realizowana przez wymianę
  fragmentów HTML.
- **API-first mimo HTMX.** REST API jest utrzymywane jako pełnoprawny kontrakt (testowany,
  dokumentowany), niezależny od warstwy prezentacji. Umożliwia to przyszłe integracje bez zmiany logiki domenowej.
- **Serwisy oddzielone od HTTP.** Logika biznesowa w `*_service.py` jest niezależna od tego,
  czy wywołał ją router JSON, czy endpoint HTMX - łatwiejsze testowanie i brak duplikacji.

### Powody decyzji

Server-side rendering z HTMX jest **trafniejszym wyborem dla tego konkretnego problemu i ograniczeń**:

1. **Dobór narzędzia do problemu.** To aplikacja CRUD-owo-analityczna (konta, kategorie,
   transakcje, dashboard, statystyki), a nie edytor czasu rzeczywistego, app offline czy gra. HTMX jest najlepiej    przystosowany do takiej architektury.
2. **Bezpieczeństwo aplikacji finansowej.** Cała logika i walidacja zostają na serwerze,
   reguły biznesowe (salda, zgodność znaku kwoty z typem kategorii) nie trafiają do przeglądarki.
   Mniejsza powierzchnia ataku, auth na sesjach, brak tokenów w JS.
3. **Jedno źródło informacji.** Walidacja (Pydantic) i agregacje (`stats_service`) istnieją raz,
   blisko bazy. W modelu SPA część logiki formatowania/walidacji trzeba by duplikować w JS
   i pilnować, by się nie rozjechała.
4. **Prostota operacyjna.** Jeden język po stronie serwera, brak kroku budowania, brak Node ani osobnego serwisu frontendu, całość jest uruchamiana jednym `docker compose up`.
5. **Wydajność klienta.** Przeglądarka dostaje małe fragmenty HTML zamiast pobierać i parsować
   duży bundle JS, co daje szybki pierwszy render, dobrze działa też na słabszym sprzęcie.
6. **Testowalność tego, co widzi użytkownik.** Render server-side sprawia, że smoke testy UI
   sprawdzają realny HTML trafiający do użytkownika.
7. **Elastyczność bez kosztu SPA.** Utrzymujemy pełne, udokumentowane i przetestowane REST API jako kontrakt pod przyszłe integracje.
   
**Znane trade-offy (świadomie akceptowane).** HTMX słabiej nadaje się do wysoko interaktywnych,
offline lub real-time interfejsów, a złożone interakcje czysto klienckie i tak wymagają trochę JS.
Żaden z tych przypadków nie dotyczy aplikacji budżetowej, więc te ograniczenia nas nie kosztują.


Szczegóły uruchomienia: [README](../README.md).
