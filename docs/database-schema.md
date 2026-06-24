# Schemat bazy danych

Projekt używa bazy danych PostgreSQL. Definicje tabel znajdują się w `backend/finance/models.py`. Tworzone są poprzez migrację z odpowiednimi nazwami <nazwa_aplikacji>_<nazwa_modelu> w `backend/finance/migrations/0001_initial.py`

## Diagram

```mermaid
%%{init: {"er": {"layoutDirection": "LR"}}}%%
erDiagram
    auth_user {
        bigint id PK
        varchar username
        varchar email
        varchar password
        boolean is_active
        datetime date_joined
    }

    finance_account {
        bigint id PK
        bigint user_id FK
        varchar name
        decimal balance
        varchar currency
    }

    finance_category {
        bigint id PK
        bigint user_id FK
        varchar name
        varchar color
        boolean is_income
    }

    finance_transaction {
        bigint id PK
        bigint account_id FK
        bigint category_id FK
        decimal amount
        varchar title
        text description
        datetime date
    }

    auth_user ||--o{ finance_account : "posiada"
    auth_user ||--o{ finance_category : "posiada"
    finance_account ||--o{ finance_transaction : "zawiera"
    finance_category ||--o{ finance_transaction : "klasyfikuje"
```

## Tabele

### auth_user

Wbudowana tabela Django, nie jest definiowana w projekcie, pochodzi z `django.contrib.auth`.

| Pole | Typ | Opis |
|---|---|---|
| id | bigint (PK) | Klucz główny |
| username | varchar | Nazwa użytkownika |
| email | varchar | Adres e-mail |
| password | varchar | Hasło |
| is_active | boolean | Aktywność konta |
| date_joined | datetime | Data rejestracji |

---

### finance_account

Konto finansowe użytkownika, zdefiniowane w `backend/finance/models.py`.

| Pole | Typ | Opis |
|---|---|---|
| id | bigint (PK) | Klucz główny |
| user_id | bigint (FK) | Właściciel konta -> auth_user (CASCADE) |
| name | varchar(50) | Nazwa konta |
| balance | decimal(12,2) | Aktualne saldo, aktualizowane przez serwis przy każdej transakcji |
| currency | varchar(3) | Waluta, domyślnie PLN. Dozwolone wartości są w `backend/finance/constants.py` |

---

### finance_category

Kategoria transakcji przypisana do użytkownika, zdefiniowane w `backend/finance/models.py`.

| Pole | Typ | Opis |
|---|---|---|
| id | bigint (PK) | Klucz główny |
| user_id | bigint (FK) | Właściciel kategorii -> auth_user (CASCADE) |
| name | varchar(50) | Nazwa kategorii |
| color | varchar(7) | Kolor w formacie HEX, wybierany z palety z `backend/finance/constants.py` |
| is_income | boolean | True - przychód, False - wydatek |

---

### finance_transaction

Pojedyncza transakcja finansowa, zdefiniowane w `backend/finance/models.py`.

| Pole | Typ | Opis |
|---|---|---|
| id | bigint (PK) | Klucz główny |
| account_id | bigint (FK) | Konto transakcji -> finance_account (CASCADE) |
| category_id | bigint (FK) | Kategoria -> finance_category |
| amount | decimal(12,2) | Kwota: ujemna - wydatek, dodatnia - przychód |
| title | varchar(200) | Tytuł transakcji |
| description | text | Opis |
| date | datetime | Data transakcji |

## Relacje

| Relacja | Typ | Zachowanie przy usunięciu |
|---|---|---|
| auth_user → finance_account | 1:N | CASCADE - usunięcie użytkownika usuwa jego konta |
| auth_user → finance_category | 1:N | CASCADE - usunięcie użytkownika usuwa jego kategorie |
| finance_account → finance_transaction | 1:N | CASCADE - usunięcie konta usuwa jego transakcje |
| finance_category → finance_transaction | 1:N | SET NULL - usunięcie kategorii pozostawia transakcje bez kategorii |
