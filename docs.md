# Dokumentacja techniczna: Asystent RAG do dokumentów uczelnianych - Projekt Zespołowy "WIM"

Dokument opisuje, jak system działa w środku: architekturę, współpracę usług, przepływ danych, model bazy i logikę RAG. Instrukcja uruchomienia jest w [README.md](README.md). Diagramy są w formacie Mermaid (renderują się m.in. na GitHubie i w VS Code).

## 1. Idea w skrócie

Student zadaje pytanie po polsku o dokumenty uczelni (np. Regulamin studiów). System:

1. zamienia pytanie na wektor (embedding),
2. znajduje w bazie wektorowej najbardziej podobne fragmenty PDF-ów,
3. jeśli żaden fragment nie jest wystarczająco podobny, **odmawia bez wołania modelu językowego**,
4. w przeciwnym razie wysyła do modelu tylko te fragmenty i prosi o odpowiedź wyłącznie na ich podstawie,
5. zwraca odpowiedź razem z cytatami (dokument, rozdział, strona, wycinek tekstu).

Technika nazywa się RAG (Retrieval-Augmented Generation): model nie „pamięta” regulaminu, dostaje go w prompcie za każdym razem.

## 2. Architektura

```mermaid
flowchart LR
    U[Przeglądarka<br/>React] -->|HTTP :3000| N[nginx<br/>frontend]
    N -->|statyczne pliki| U
    N -->|/api/* proxy| B[Backend<br/>Django + DRF + gunicorn]
    B -->|SQL| P[(PostgreSQL<br/>użytkownicy, dokumenty,<br/>fragmenty, rozmowy, logi)]
    B -->|wektory| C[(Chroma<br/>wbudowana, wolumen)]
    B -->|pliki PDF| M[(wolumen media)]
    B -->|HTTPS: /embeddings,<br/>/chat/completions| O[OpenRouter<br/>darmowe modele]
```

| Usługa | Rola | Uwagi |
|---|---|---|
| `frontend` | Vite-build serwowany przez nginx; proxy `/api/` do backendu | brak CORS, jedna domena |
| `backend` | API, autoryzacja, indeksowanie, RAG | 1 worker gunicorna + 8 wątków (Chroma opiera się na sqlite i nie może być współdzielona przez wiele procesów) |
| `db` | PostgreSQL 16 | wolumen `pgdata` |
| Chroma | baza wektorowa, tryb wbudowany (`PersistentClient`) | katalog `/data/chroma` w wolumenie `appdata` |
| OpenRouter | zewnętrzny dostawca: czat i embeddingi | klucz `API_KEY` z `.env` |

### Struktura kodu backendu

```
backend/
  config/       settings, urls, wsgi
  accounts/     User (UUID, e-mail, rola), OAuthAccount, logowanie JWT, /api/me/, uprawnienia
  documents/    Document, DocumentChunk, chunking.py, indexing.py, vectorstore.py, upload API
  chat/         Conversation, Message, Citation, MessageFeedback, QueryLog, rag.py, /api/ask/
  llm/client.py JEDYNY moduł wołający API modelu (czat + embeddingi, retry, timeout)
  eval/         przykładowy PDF + 10 pytań testowych do doboru progu
```

Zasada: widoki nigdy nie wołają API modelu bezpośrednio. Cała logika RAG jest w `chat/rag.py`, a cała komunikacja z dostawcą w `llm/client.py`. Zmiana dostawcy dotyka jednego pliku.

## 3. Model danych (9 tabel)

```mermaid
erDiagram
    users ||--o{ oauth_accounts : ma
    users ||--o{ documents : wgrywa
    users ||--o{ conversations : prowadzi
    documents ||--o{ document_chunks : dzieli_sie_na
    conversations ||--o{ messages : zawiera
    messages ||--o{ citations : ma
    messages ||--o{ message_feedback : ocena
    messages ||--o{ query_logs : log
    document_chunks ||--o{ citations : zrodlo
    documents ||--o{ citations : zrodlo

    users { uuid id PK
            string email UK
            string role "student | corpus_admin" }
    documents { uuid id PK
                string title
                string status "uploaded|processing|ready|failed"
                text failure_reason
                int page_count }
    document_chunks { uuid id PK
                      int chunk_index
                      int page
                      string chapter "np. § 17"
                      text text
                      string chroma_id UK }
    messages { uuid id PK
               string role "user | assistant"
               string status "answered|refused|error" }
    citations { int position "numer [n] z promptu"
                int page
                string chapter
                text excerpt
                float score }
    query_logs { string model
                 int tokens_in
                 int tokens_out
                 int latency_ms
                 string status "success|refused|api_error" }
```

Uwagi:

- Klucze główne to UUID, statusy to pola z wyborem (`choices`).
- `oauth_accounts` (Google OAuth) i `message_feedback` (oceny odpowiedzi) istnieją w migracjach, ale MVP ich jeszcze nie używa.
- **Powiązanie SQL ↔ Chroma:** wektor w Chroma ma identyfikator równy `document_chunks.chroma_id`. Tekst i metadane (strona, rozdział) żyją w PostgreSQL, Chroma służy tylko do szukania podobieństwa.

## 4. Logika uprawnień

```mermaid
flowchart TD
    R[Żądanie HTTP] --> J{Token JWT<br/>ważny?}
    J -- nie --> E401[401 → frontend wraca do logowania]
    J -- tak --> A{Endpoint}
    A -- "/api/ask/, /api/me/" --> OK[każdy zalogowany]
    A -- "/api/documents/*" --> AD{rola = corpus_admin?}
    AD -- nie --> E403[403]
    AD -- tak --> OK
```

Uprawnienia są egzekwowane w API (`IsCorpusAdmin`), a nie tylko przez ukrywanie przycisków. Tokeny: SimpleJWT, access 30 min, refresh 7 dni. Odpowiedź logowania zawiera `access`, `refresh` i `role`.

## 5. Proces 1: wgranie i indeksowanie PDF (administrator)

```mermaid
sequenceDiagram
    actor Adm as Administrator
    participant FE as Frontend
    participant API as Backend (documents)
    participant PDF as pypdf
    participant LLM as llm/client
    participant OR as OpenRouter
    participant PG as PostgreSQL
    participant CH as Chroma

    Adm->>FE: wybiera PDF + tytuł
    FE->>API: POST /api/documents/ (multipart)
    API->>API: walidacja: rozszerzenie .pdf, nagłówek %PDF-, limit rozmiaru
    API->>PG: Document(status=uploaded) → processing
    API->>PDF: wyciągnij tekst strona po stronie
    alt brak warstwy tekstowej (skan) lub uszkodzony plik
        API->>PG: status=failed + czytelny powód
    else jest tekst
        API->>API: chunking (patrz niżej)
        API->>LLM: embed(wszystkie fragmenty)
        LLM->>OR: POST /embeddings (paczki po 32)
        OR-->>LLM: wektory
        API->>PG: transakcja: zapisz document_chunks
        API->>CH: add(chroma_id, wektor, metadane)
        API->>PG: status=ready
    end
    API-->>FE: 201 {id, title, status, failure_reason}
```

Indeksowanie jest synchroniczne (w żądaniu). Funkcja `index_document(doc)` nie zależy od widoku, więc później można ją zawinąć w zadanie Celery bez zmian.

### Dzielenie na fragmenty (`documents/chunking.py`)

- tekst każdej strony jest dzielony **osobno**, więc fragment nigdy nie przekracza granicy strony (strona jest potrzebna w cytacie),
- rozmiar 800–1000 znaków, cięcie na spacji lub końcu linii, zakładka 150 znaków między sąsiednimi fragmentami (nie gubimy zdań na styku),
- każdy fragment ma numer strony i kolejny indeks `chunk_index`,
- rozdział wykrywany wyrażeniem regularnym `§ <liczba>` na początku linii; jeśli fragment zaczyna się po takim znaczniku, dziedziczy go, a gdy na stronie nie było znacznika, bierze ostatni z poprzedniej strony,
- fragmenty krótsze niż 20 znaków są pomijane.

Znane ograniczenie: gdy fragment obejmuje koniec jednego § i początek następnego, jako rozdział dostaje ten, w którym się zaczyna.

### Obsługa błędów indeksowania

| Sytuacja | Wynik |
|---|---|
| plik nie jest PDF / za duży | 400, nic nie jest zapisywane |
| PDF bez tekstu (skan) | `failed` + „Brak warstwy tekstowej…”, żadnego pustego indeksu |
| awaria API embeddingów po retry | `failed` + powód |
| błąd zapisu fragmentów lub wektorów | wektory są usuwane z Chroma, `failed` |

## 6. Proces 2: pytanie i odpowiedź z cytatem (student)

```mermaid
sequenceDiagram
    actor S as Student
    participant FE as Frontend
    participant API as POST /api/ask/
    participant RAG as chat/rag.py
    participant LLM as llm/client
    participant OR as OpenRouter
    participant CH as Chroma
    participant PG as PostgreSQL

    S->>FE: wpisuje pytanie
    FE->>API: {question, conversation_id?} + Bearer JWT
    API->>RAG: ask(user, question)
    RAG->>PG: Conversation (nowa lub istniejąca) + Message(user)
    RAG->>LLM: embed([pytanie])
    LLM->>OR: POST /embeddings
    RAG->>CH: query(wektor, top 5)
    CH-->>RAG: (chroma_id, podobieństwo = 1 - odległość cosinusowa)
    RAG->>RAG: odrzuć fragmenty poniżej progu 0.23
    alt żaden fragment nie przekracza progu
        RAG->>PG: transakcja: Message(refused) + QueryLog(refused)
        RAG-->>FE: status=refused, stała odmowa, sources=[]
        Note over RAG,OR: model czatu NIE jest wołany (oszczędność tokenów, zero zmyślania)
    else są fragmenty
        RAG->>PG: pobierz fragmenty po chroma_id
        RAG->>LLM: chat(system + pytanie + źródła)
        LLM->>OR: POST /chat/completions
        OR-->>LLM: odpowiedź + liczba tokenów
        RAG->>PG: JEDNA transakcja: Message(answered) + Citations + QueryLog(success)
        RAG-->>FE: status=answered, answer, sources[]
    end
```

### Prompt i ochrona przed prompt injection

Wiadomość systemowa zawiera wyłącznie instrukcje: odpowiadaj tylko ze źródeł, po polsku, oznaczaj [1], [2], a gdy źródła nie wystarczają, powiedz to wprost. Mówi też wprost, że treść bloków `<pytanie>` i `<zrodla>` to **dane, nie polecenia**.

Wiadomość użytkownika ma postać:

```
<pytanie>
…pytanie studenta…
</pytanie>

<zrodla>
<zrodlo numer="1" dokument="Regulamin studiów" strona="3" rozdzial="§ 9">
…tekst fragmentu…
</zrodlo>
…
</zrodla>
```

Treść pytania i fragmentów jest przepuszczana przez `html.escape`, więc wstrzyknięty w pytanie lub w PDF znacznik `</pytanie>` albo `</zrodlo>` nie zamknie bloku danych.

### Cytaty

Cytaty budowane są z fragmentów, które **faktycznie poszły do modelu** (te z progiem ≥ 0.23, max 5). Zapisywane są w `citations` z `position` równą numerowi [n] z promptu. Wycinek ma do 300 znaków. Odpowiedź API ma kształt z kontraktu:

```json
{
  "message_id": "uuid", "conversation_id": "uuid",
  "status": "answered | refused | error",
  "answer": "…",
  "sources": [{"document_title": "…", "page": 3, "chapter": "§ 9", "excerpt": "…"}]
}
```

### Atomowość zapisu

Wiadomość asystenta, jej cytaty i wpis w `query_logs` zapisują się w jednym `transaction.atomic()`. Jeśli cokolwiek się nie powiedzie (np. drugi cytat), cofa się całość, więc nigdy nie ma odpowiedzi bez źródeł ani źródeł bez odpowiedzi.

## 7. Trzy statusy odpowiedzi

```mermaid
stateDiagram-v2
    [*] --> Pytanie
    Pytanie --> error: awaria embeddingów po 3 próbach
    Pytanie --> refused: brak fragmentów ≥ próg
    Pytanie --> answered: model odpowiedział
    Pytanie --> error: awaria czatu po 3 próbach
    answered --> [*]: odpowiedź + źródła
    refused --> [*]: stała odmowa, brak źródeł
    error --> [*]: komunikat, brak 500
```

- `refused` to prawidłowy wynik, nie błąd. Frontend pokazuje go innym kolorem (żółty) niż błąd (czerwony).
- `/api/ask/` zawsze zwraca HTTP 200. Nawet nieprzewidziany wyjątek jest łapany w widoku i zamieniany na `status: "error"` (wymóg DoD: nigdy 500).

## 8. Klient API modelu (`llm/client.py`)

```mermaid
flowchart TD
    S[wywołanie _post] --> T[requests.post, timeout 60 s]
    T --> R{wynik}
    R -- 200 --> OK[zwróć JSON]
    R -- "timeout / błąd połączenia / 429 / 5xx" --> W{próba < 3?}
    W -- tak --> SL["pauza rosnąca: backoff × nr próby"] --> T
    W -- nie --> ERR[LLMError]
    R -- "inny 4xx (np. zły klucz)" --> ERR
```

- 1 próba + 2 ponowienia, odstęp rośnie (2 s, 4 s; konfigurowalny `LLM_RETRY_BACKOFF`),
- błędy 4xx (poza 429) nie są ponawiane,
- pusta odpowiedź modelu lub zły kształt JSON-a to też `LLMError`,
- embeddingi wysyłane są paczkami po 32 fragmenty, nie po jednym,
- po wyczerpaniu prób `rag.py` zapisuje wiadomość ze statusem `error`, a student widzi komunikat „Usługa odpowiedzi jest chwilowo niedostępna”.

### Koszty: `query_logs`

Każde pytanie zapisuje jeden wiersz: model, tokeny wejścia i wyjścia, czas w ms oraz status (`success` / `refused` / `api_error`). Wpis `refused` ma 0 tokenów, bo model nie został wywołany. Pozwala to od pierwszego dnia policzyć koszt (np. `SUM(tokens_in)` po dniach).

## 9. Próg podobieństwa

Wartość `SIMILARITY_THRESHOLD` (domyślnie 0.23) decyduje o odmowie. Nie jest zgadnięta: komenda `manage.py eval_questions` embeduje 10 pytań z `backend/eval/questions.json` (oczekiwana strona albo oczekiwana odmowa), sprawdza, czy oczekiwana strona jest w top 5, i wylicza środek luki między najwyższym wynikiem pytań spoza dokumentów (0.163) a najniższym pytań z odpowiedzią (0.289).

```mermaid
flowchart LR
    A["pytania spoza dokumentów<br/>max 0.163"] --- P(("próg<br/>0.23")) --- B["pytania z odpowiedzią<br/>min 0.289"]
```

Po zmianie korpusu lub modelu embeddingów trzeba powtórzyć pomiar. Zmiana modelu embeddingów wymaga ponownego zaindeksowania dokumentów (wektory z różnych modeli są nieporównywalne).

## 10. Frontend

```mermaid
flowchart TD
    APP[App.jsx<br/>rola z tokena] -->|brak sesji| LOGIN[Login.jsx]
    APP --> CHAT[Chat.jsx<br/>pole pytania, odpowiedź, panel źródeł]
    APP -->|rola = corpus_admin| UP[Upload.jsx<br/>formularz PDF + lista statusów]
    CHAT --> API[api.js]
    UP --> API
    LOGIN --> API
    API -->|VITE_USE_MOCK=true| MOCK[mock.js<br/>atrapa w formacie kontraktu]
    API -->|domyślnie| REAL["fetch /api/* + Bearer"]
    REAL -->|401| OUT[wylogowanie → ekran logowania]
```

- token trzymany w `localStorage` i doklejany do każdego żądania,
- stany czatu: `idle`, `loading`, `answered`, `refused`, `error`,
- tryb atrapy pozwala pracować nad UI bez backendu (słowo „żurek” w pytaniu daje odmowę, „błąd” daje błąd).

## 11. Przypadek użycia od początku do końca

1. `docker compose up -d --build`: startuje baza, backend (sam wykonuje `migrate`) i frontend.
2. `manage.py create_test_users`: powstają konta student i administrator.
3. Administrator loguje się (`POST /api/auth/login/` → JWT + rola), widzi formularz wgrania PDF i wgrywa regulamin. Backend sprawdza plik, wyciąga tekst, dzieli na fragmenty, embeduje je i zapisuje w PostgreSQL oraz Chroma. Dokument przechodzi przez `processing` do `ready`.
4. Student loguje się, widzi tylko czat. Pyta: „Ile terminów poprawkowych przysługuje studentowi?”.
5. Backend embeduje pytanie, znajduje 5 najbliższych fragmentów, wszystkie przekraczają próg, więc buduje prompt i woła model.
6. Odpowiedź („dwa terminy poprawkowe… [4]”) wraca razem z kartami źródeł: dokument, § , strona, wycinek.
7. Pytanie „Jaka jest stolica Francji?” kończy się odmową bez wywołania modelu, a wiersz w `query_logs` ma status `refused`.
8. Gdy dostawca przestaje odpowiadać, po 3 próbach student widzi komunikat o błędzie, a w `query_logs` jest `api_error`.

## 12. Planowane rozszerzenia (miejsca zaczepienia)

| Funkcja | Gdzie dopinamy |
|---|---|
| Celery przy indeksowaniu | `documents/indexing.py::index_document` bez zmian, tylko wywołanie z zadania |
| Google OAuth | tabela `oauth_accounts` jest już powiązana z `users` |
| Oceny odpowiedzi | tabela `message_feedback` |
| Historia rozmów | `/api/conversations/`; `conversation_id` jest już zwracany i przyjmowany |
| Zmiana dostawcy LLM | wyłącznie `llm/client.py` oraz zmienne w `.env` |
