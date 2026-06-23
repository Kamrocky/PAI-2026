# ADR

Projekt: aplikacja budżetowa / finanse osobiste z dashboardem.

Poniżej zapisujemy najważniejsze decyzje techniczne. Nie opisujemy tutaj każdej biblioteki, tylko rzeczy, które realnie wpływają na architekturę projektu.

---

## 1. Backend w Django

**Decyzja:**  
Backend aplikacji robimy w Django.

**Kontekst:**  
Aplikacja będzie przechowywać dane użytkowników, konta, kategorie i transakcje. Potrzebujemy logowania, bazy danych, migracji oraz podstawowej logiki po stronie serwera. Projekt nie jest bardzo duży, ale musi być spójny i łatwy do uruchomienia.

**Rozważane alternatywy:**
- FastAPI
- Node.js, np. Express albo NestJS

**Dlaczego Django:**  
Django daje od razu dużo rzeczy, których potrzebujemy: ORM, migracje, obsługę użytkowników, panel admina i sensowną strukturę projektu. Dzięki temu nie musimy składać backendu z wielu osobnych bibliotek. Dla aplikacji budżetowej, gdzie większość danych jest relacyjna, Django pasuje naturalnie.

FastAPI też byłoby dobrym wyborem, szczególnie dla samego API, ale wymagałoby osobnego dobrania większej liczby elementów. Node.js odrzucamy, bo w tym projekcie nie potrzebujemy pełnego stosu JavaScript/TypeScript, a Django pozwoli szybciej dojść do działającej wersji.

**Konsekwencje:**  
Django jest większe i cięższe niż FastAPI. Część mechanizmów może być dla nas nadmiarowa. W zamian dostajemy stabilną strukturę i mniej decyzji konfiguracyjnych na początku projektu.

---

## 2. API w Django Ninja

**Decyzja:**  
Do stworzenia API używamy Django Ninja.

**Kontekst:**  
Frontend musi pobierać i zapisywać dane, np. transakcje, kategorie, konta oraz dane do dashboardu. Potrzebujemy też walidacji danych wejściowych, bo w aplikacji finansowej nie chcemy przyjmować błędnych kwot, dat albo typów transakcji.

**Rozważane alternatywy:**
- Django REST Framework
- FastAPI
- backend w Node.js z innym podejściem do API

**Dlaczego Django Ninja:**  
Django Ninja dobrze pasuje do Django, a jednocześnie jest prostsze i lżejsze niż Django REST Framework. Pozwala szybko opisać endpointy i schematy danych. Dodatkowo automatycznie generuje dokumentację API, co przyda się przy prezentacji i testowaniu projektu.

DRF ma większy ekosystem, ale na potrzeby tej aplikacji byłby trochę cięższy. FastAPI byłoby podobne pod względem wygody pisania API, ale oznaczałoby zmianę głównego frameworka backendowego.

**Konsekwencje:**  
Django Ninja ma mniejszy ekosystem niż DRF. Musimy sami pilnować spójnej struktury endpointów i schematów. Zyskujemy za to prostszy kod API.

---

## 3. PostgreSQL jako baza danych

**Decyzja:**  
Jako główną bazę danych wybieramy PostgreSQL.

**Kontekst:**  
Dane w aplikacji są relacyjne: użytkownik ma konta, konta mają transakcje, transakcje mają kategorie. Dashboard będzie pokazywał podsumowania, np. wydatki według kategorii albo bilans miesiąca. Potrzebujemy bazy, która dobrze radzi sobie z relacjami i agregacjami.

**Rozważane alternatywy:**
- MySQL
- SQLite
- MongoDB

**Dlaczego PostgreSQL:**  
PostgreSQL dobrze współpracuje z Django i sprawdza się przy danych relacyjnych. Daje transakcje, klucze obce, indeksy i dobre możliwości agregacji. To ważne, bo dane finansowe powinny być spójne, a raporty na dashboardzie będą oparte na zapytaniach do bazy.

MySQL też byłby możliwy, ale PostgreSQL daje nam większy komfort przy bardziej złożonych zapytaniach. SQLite zostawiamy ewentualnie do prostych testów lokalnych, ale nie jako główną bazę projektu. MongoDB nie pasuje tak dobrze, bo nasze dane mają dużo relacji.

**Konsekwencje:**  
Musimy dobrze zaplanować schemat bazy i migracje. Baza relacyjna jest mniej elastyczna przy częstych zmianach modelu niż baza dokumentowa, ale w zamian lepiej pilnuje spójności danych.

---

## 4. HTMX 

**Decyzja:**  
Do dynamicznych elementów interfejsu używamy HTMX, a nie Reacta.

**Kontekst:**  
Aplikacja będzie miała formularze, listy transakcji, filtry i dashboard. Potrzebujemy odświeżać fragmenty strony, np. listę transakcji po dodaniu nowej pozycji albo podsumowanie po zmianie zakresu dat. Nie planujemy bardzo rozbudowanego SPA.

**Rozważane alternatywy:**
- React
- Vue albo Svelte
- zwykłe szablony Django bez HTMX

**Dlaczego HTMX:**  
HTMX pozwala dodać interaktywność bez budowania osobnej aplikacji frontendowej. Większość logiki zostaje po stronie Django, a frontend jest prostszy. Dla naszego projektu to wystarczy, bo nie mamy bardzo skomplikowanego stanu po stronie klienta.

React byłby dobry, gdyby aplikacja miała dużo złożonych komponentów, drag and drop, tryb offline albo bardzo rozbudowany stan klienta. U nas byłoby to raczej zwiększenie złożoności bez dużej korzyści.

**Konsekwencje:**  
Frontend będzie mocniej związany z backendem i szablonami Django. HTMX nie daje takiej swobody jak React przy bardzo interaktywnych widokach. Za to mamy mniej JavaScriptu, mniej konfiguracji i prostsze uruchamianie projektu.

---

## 5. Tailwind CSS do stylowania

**Decyzja:**  
Interfejs stylujemy przy pomocy Tailwind CSS.

**Kontekst:**  
Aplikacja będzie miała dashboard, tabele, formularze, filtry i karty z podsumowaniami. Chcemy szybko zrobić czytelny interfejs, bez pisania dużej ilości własnego CSS od zera.

**Rozważane alternatywy:**
- Bootstrap
- zwykły CSS albo SCSS
- gotowe biblioteki komponentów frontendowych

**Dlaczego Tailwind:**  
Tailwind dobrze pasuje do szablonów Django i HTMX, bo style można wpisywać bezpośrednio w HTML. Łatwo dzięki temu budować responsywne widoki, tabele i karty dashboardu. Nie jesteśmy też ograniczeni wyglądem gotowych komponentów z Bootstrapa.

Bootstrap byłby szybszy na samym początku, ale trudniej uniknąć typowego wyglądu bootstrapowej aplikacji. Czysty CSS dałby pełną kontrolę, ale wymagałby więcej czasu i pilnowania spójności.

**Konsekwencje:**  
HTML może mieć dużo klas i przez to być mniej czytelny. Musimy pilnować, żeby nie tworzyć przypadkowych, niespójnych styli. W zamian szybciej składamy widoki i mamy dużą kontrolę nad wyglądem.

---

## 6. Monolit Django zamiast osobnego frontendu i backendu

**Decyzja:**  
Budujemy aplikację jako monolit w Django: backend, szablony, HTMX i API są w jednym projekcie.

**Kontekst:**  
Projekt robimy w małym zespole i w ograniczonym czasie. Zakres aplikacji jest dość jasny: użytkownicy, konta, kategorie, transakcje i dashboard. Nie potrzebujemy mikroserwisów ani osobnego frontendu SPA.

**Rozważane alternatywy:**
- osobny backend API + React SPA
- mikroserwisy
- backend w Node.js i osobny frontend

**Dlaczego monolit:**  
Monolit jest prostszy do zbudowania, testowania i uruchomienia przez Docker Compose. W naszym przypadku jedna aplikacja Django wystarczy do obsługi logowania, widoków, API i logiki finansowej. Taki podział jest adekwatny do skali projektu i nie komplikuje go na siłę.

Osobny React i osobne API miałyby sens przy większym produkcie albo gdybyśmy planowali wielu klientów, np. aplikację mobilną i osobny panel webowy. Mikroserwisy byłyby tutaj zdecydowanym over-engineeringiem.

**Konsekwencje:**  
Aplikacja będzie mniej elastyczna, jeśli w przyszłości chcielibyśmy niezależnie skalować frontend i backend. Frontend jest też bardziej zależny od Django. Na potrzeby projektu ważniejsza jest jednak prostota i spójność.

---

## 7. Django Session do uwierzytelniania

**Decyzja:**  
Do uwierzytelniania użytkowników używamy wbudowanego mechanizmu sesji Django, a nie tokenów JWT.

**Kontekst:**  
Aplikacja wymaga logowania: użytkownik musi mieć dostęp tylko do swoich kont, kategorii i transakcji. Potrzebujemy prostego i bezpiecznego sposobu na identyfikację zalogowanego użytkownika przy każdym żądaniu.

**Rozważane alternatywy:**
- JWT (np. przez djangorestframework-simplejwt)
- Token-based auth z Django REST Framework
- OAuth2 / logowanie przez zewnętrznego dostawcę

**Dlaczego Django Session:**  
Django Session jest wbudowane w framework i nie wymaga żadnych dodatkowych bibliotek. Sesja jest przechowywana po stronie serwera, a przeglądarka dostaje tylko cookie z identyfikatorem sesji. Dobrze współpracuje z HTMX i szablonami Django, bo każde żądanie HTMX automatycznie wysyła cookie sesji. Nie musimy też samodzielnie obsługiwać odświeżania tokenów ani przechowywania JWT po stronie klienta.

JWT sprawdziłoby się lepiej przy osobnym frontendzie SPA albo przy API konsumowanym przez aplikacje mobilne. W naszym monolicie Django z HTMX byłoby to zbędna komplikacja.

**Konsekwencje:**  
Sesje są przechowywane w bazie danych, co oznacza dodatkowe zapytania przy każdym żądaniu. Rozwiązanie jest też mniej przenośne — gdybyśmy w przyszłości chcieli udostępnić API dla zewnętrznych klientów, musielibyśmy dodać osobny mechanizm uwierzytelniania. Na potrzeby obecnej aplikacji webowej sesje są wystarczające i bezpieczne.
