# CoinZen - aplikacja budżetowa

Aplikacja internetowa do zarządzania finansami osobistymi. Użytkownik może dodawać konta
(w różnych walutach), kategorie przychodów i wydatków oraz transakcje, a następnie analizować
swoje finanse na dashboardzie i stronie statystyk z interaktywnymi wykresami.

## Stack technologiczny

- **Backend:** Python 3.12, Django 5.2, Django Ninja (REST API)
- **Baza danych:** PostgreSQL 15 + Django ORM / migrations
- **Frontend:** HTMX + Tailwind CSS (server-rendered, bez budowania), ApexCharts (wykresy)
- **Autentykacja:** sesje Django
- **Konteneryzacja:** Docker Compose

## Uruchomienie

Wymagany jest tylko **Docker** (z Docker Compose). Przy **pierwszym** uruchomieniu budujemy obraz:

```
docker compose up --build
```

Przy **kolejnych** uruchomieniach (gdy nie zmieniał się `Dockerfile` ani `requirements.txt`)
budowanie nie jest potrzebne:

```
docker compose up
```

Compose podnosi dwa serwisy:

- `db` - PostgreSQL (z healthcheckiem),
- `web` - serwer Django, który po starcie automatycznie wykonuje migracje i uruchamia aplikację.

Po uruchomieniu, aplikacja jest dostępna pod:

```
http://localhost:8000
```

Aby zatrzymać aplikację:

```
docker compose down
```

(dane bazy są trwałe - przechowywane w wolumenie `postgres_data`; aby je wyczyścić,
używamy `docker compose down -v`).

### Pierwsze uruchomienie

1. Wchdzimy na `http://localhost:8000` - zostaniemy przekierowani do ekranu logowania.
2. Podajemy adres e-mail; jeśli konto nie istnieje, aplikacja zaproponuje rejestrację
   (imię + hasło). Po rejestracji nie jest wymagane logowanie.

### Dane demo

Aby szybko wypełnić bazę przykładowymi danymi (konta w różnych walutach, kategorie,
kilkadziesiąt transakcji), musimy uruchomić komendę zarządzania dla swojego adresu e-mail:

```
docker compose exec web python manage.py seed_demo --email=twoj@email.pl
```

Komenda jest idempotentna, wszystkie dane będą świeże, przy okazji resetujac konto.

### Testy

```
docker compose exec web python manage.py test finance.tests
```

## Architektura

Aplikacja jest monolitem Django serwującym zarówno **REST API**, jak i **interfejs HTMX**.
Frontend nie jest osobnym serwisem - HTML jest renderowany po stronie serwera, a interaktywność
zapewnia HTMX (fragmenty HTML wymieniane bez przeładowania strony). Dzięki temu nie ma konieczności
budowania frontendu.

```
Przeglądarka (HTMX + Tailwind + ApexCharts)
        │  HTTP / fragmenty HTML / JSON
        ▼
Django  ├─ core/            ustawienia, routing URL
        └─ finance/
           ├─ views.py            widoki stron (shell HTML dla zalogowanych)
           ├─ api.py              montaż routerów Django Ninja
           ├─ api_*.py            REST API (accounts, categories, transactions, auth)
           ├─ ui_*.py             endpointy HTMX zwracające fragmenty HTML
           ├─ *_service.py        logika domenowa (salda, statystyki, home, profil)
           ├─ *_forms.py          walidacja formularzy (Pydantic)
           ├─ schemas.py          schematy Pydantic dla API
           ├─ models.py           modele ORM
           ├─ templates/          szablony Django (HTMX)
           └─ management/commands seed_demo (dane demo)
        │
        ▼
PostgreSQL (Django ORM + migracje)
```

### Warstwy

- **Modele (`models.py`)** - `Account`, `Category`, `Transaction`, wbudowany `User`.
  Relacje: `User -> Account -> Transaction`, `Transaction -> Category`.
- **API (`api_*.py`)** — REST przez Django Ninja, walidacja danych schematami Pydantic
  (`schemas.py`), automatyczne 422 przy błędnych danych.
- **UI / HTMX (`ui_*.py`)** — endpointy zwracające fragmenty HTML, ta sama walidacja Pydantic
  co API (`*_forms.py`).
- **Serwisy (`*_service.py`)** — logika domenowa odseparowana od warstwy HTTP
  (`transaction_service` aktualizuje saldo konta atomowo, `stats_service` agreguje dane
  do wykresów).
- **Autentykacja** — sesje Django, chronione endpointy odrzucają niezalogowanych (HTTP 401),
  a widoki stron pokazują ekran logowania.

### Kluczowe zasoby API

| Zasób         | Endpoint bazowy        | Relacje                         |
|---------------|------------------------|---------------------------------|
| Konta         | `/api/accounts`        | należą do użytkownika           |
| Kategorie     | `/api/categories`      | należą do użytkownika           |
| Transakcje    | `/api/transactions`    | konto (FK), kategoria (FK)      |
| Autentykacja  | `/api/auth`            | logowanie / rejestracja / wylogowanie |

Interaktywna dokumentacja API (OpenAPI) jest dostępna pod 
```
http://localhost:8000/api/docs
```


## Realizacja wymagań podstawowych

### R1 - Backend API
REST API zbudowane na **Django Ninja**. Routery są montowane w [`finance/api.py`](backend/finance/api.py)
pod prefiksem `/api`. Każdy zasób ma osobny moduł z operacjami CRUD:
- [`api_accounts.py`](backend/finance/api_accounts.py) - `/api/accounts`
- [`api_categories.py`](backend/finance/api_categories.py) - `/api/categories`
- [`api_transactions.py`](backend/finance/api_transactions.py) - `/api/transactions`
- [`api_auth.py`](backend/finance/api_auth.py) - `/api/auth`

Minimum 3 zasoby powiązane relacjami: `User -> Account -> Transaction` oraz `Transaction -> Category`.
Relacje są egzekwowane w zapytaniach (transakcja pobierana przez `account__user=user`).

### R2 - Baza danych
**PostgreSQL 15** (serwis `db` w `docker-compose.yml`), dostęp przez **Django ORM**.
Modele w [`finance/models.py`](backend/finance/models.py): `Account`, `Category`, `Transaction`.
Schemat zarządzany **migracjami Django** ([`finance/migrations/`](backend/finance/migrations/)),
uruchamianymi automatycznie przy starcie kontenera (`command: python manage.py migrate`).
Trwałość zapewnia wolumen `postgres_data`. Pełny opis: [`docs/database-schema.md`](docs/database-schema.md).

### R3 - Frontend
Interfejs w **HTMX + Tailwind**. Widoki w [`finance/views.py`](backend/finance/views.py) renderują
„shell" strony, a właściwa treść doczytywana jest fragmentami z endpointów `ui_*.py`
(np. [`ui_home.py`](backend/finance/ui_home.py), [`ui_categories.py`](backend/finance/ui_categories.py),
[`ui_stats.py`](backend/finance/ui_stats.py)). Interaktywność (dodawanie, edycja, filtrowanie,
przełączanie kont) działa przez `hx-get`/`hx-post`/`hx-delete` z wymianą fragmentów HTML, bez
przeładowania strony i bez kroku budowania frontendu. Wykresy na stronie statystyk renderuje ApexCharts.

### R4 - Autentykacja
**Sesje Django**. Rejestracja / logowanie / wylogowanie w [`api_auth.py`](backend/finance/api_auth.py).
Funkcja `get_authenticated_user` w [`auth_utils.py`](backend/finance/auth_utils.py) chroni endpointy -
niezalogowane żądania API dostają **HTTP 401**, a widoki stron pokazują ekran logowania zamiast treści.

### R5 - Konteneryzacja
[`docker-compose.yml`](docker-compose.yml) podnosi całość jedną komendą `docker compose up`.
Serwis `web` buduje się z [`backend/Dockerfile`](backend/Dockerfile), czeka na bazę, wykonuje migracje i startuje serwer.
Frontend nie wymaga osobnego serwisu (HTMX serwowany przez Django).

### R6 - Repozytorium
Publiczne repo na GitHub z historią commitów oraz pełną dokumentacją z instrukcją uruchomienia i opisem architektury.


## Elementy dodatkowe

### Walidacja danych (Pydantic)
Schematy w [`finance/schemas.py`](backend/finance/schemas.py) (`CategoryIn`, `AccountIn`,
`TransactionIn` i warianty `*Update`) z regułami w `@field_validator`. Walidacja działa dwutorowo:
- **API** — Django Ninja waliduje wejście automatycznie i zwraca `422` przy błędnych danych.
- **UI (HTMX)** — moduły `*_forms.py` ([`category_forms.py`](backend/finance/category_forms.py),
  [`account_forms.py`](backend/finance/account_forms.py),
  [`transaction_forms.py`](backend/finance/transaction_forms.py),
  [`profile_forms.py`](backend/finance/profile_forms.py)) wołają te same schematy i zwracają
  czytelne komunikaty błędów do fragmentów HTML.

Przykładowe reguły: nazwa niepusta, kolor wyłącznie z predefiniowanej palety, waluta z dozwolonej
listy, zgodność znaku kwoty z typem kategorii (przychód `+` i wydatek `-`), minimalna długość hasła.

### Dokumentacja API (OpenAPI)
Django Ninja generuje dokumentację automatycznie z sygnatur i schematów. Interaktywny Swagger UI
jest dostępny pod **`http://localhost:8000/api/docs`**, a surowa specyfikacja pod `/api/openapi.json`.

### Testy
**Testy** w [`finance/tests/`](backend/finance/tests/) Pokrywają kluczową logikę:
- **jednostkowe** — modele i salda (`test_models.py`, `test_transaction_service.py`),
  logika home/statystyk (`test_home_service.py`), walidacja formularzy (`test_transaction_forms.py`),
- **integracyjne** — pełne przepływy i izolacja danych (`test_integration.py`, `test_api.py`),
- **smoke UI** — render widoków HTMX (`test_ui_views.py`, `test_categories_ui.py`, `test_profile_ui.py`).

Uruchamiane lokalnie (`manage.py test finance.tests`) oraz automatycznie w CI.

### CI/CD (GitHub Actions)
Workflowy w [`.github/workflows/`](.github/workflows/). Główny [`ci.yml`](.github/workflows/ci.yml)
wyzwala się **przy każdym pushu do `main` oraz każdym pull requeście** i uruchamia trzy workflowy:
- `lint.yml` — **flake8**,
- `django-test.yml` — **testy** na świeżej bazie PostgreSQL,
- `migrations-check.yml` — kontrola braku migracji.

### Seed data
Komenda zarządzania [`seed_demo`](backend/finance/management/commands/seed_demo.py)
(`python manage.py seed_demo --email=...`). Generuje 4 konta w różnych walutach, 12 kategorii
oraz kilkadziesiąt transakcji rozłożonych na 5 miesięcy. Jest **idempotentna**, **atomowa** i **deterministyczna**, daje powtarzalny stan przy każdym odpaleniu.


## Dokumentacja

- [Architektura](docs/architecture.md) — warstwy, przepływ żądania, dwie warstwy API (JSON + HTMX)
- [Architecture Decision Record (ADR)](docs/ADR.md) — kluczowe decyzje projektowe
- [Schemat bazy danych](docs/database-schema.md) — diagram ER i opis tabel
- [Specyfikacja UI/UX](docs/ui-ux-spec.md)
