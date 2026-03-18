# FinServe PoC - Credit Application Data Extraction

Ten projekt to Proof of Concept (PoC) automatyzujący ekstrakcję danych z formularzy kredytowych w formacie PDF. Skrypt wyciąga z dokumentów najważniejsze pola, normalizuje je, waliduje i zapisuje do lokalnej bazy SQLite.

## Czego używa projekt

- `pdfplumber` — do ekstrakcji tekstu ze stron PDF
- Lokalny serwer Ollama (np. Llama 3) — do parsowania nieustrukturyzowanego tekstu i konwersji na strukturę JSON
- `sqlite3` — lekka baza danych do przechowywania wyników

## Co robi skrypt

1. Otwiera podany PDF i przetwarza go stronami.
2. Dla każdej strony wyciąga surowy tekst za pomocą `pdfplumber`.
3. Wysyła tekst do lokalnego modelu LLM (Ollama), który według zdefiniowanego promptu zwraca JSON z polami:
   - `first_name`, `last_name`, `company_name`, `tax_id`, `requested_loan_amount`, `email`, `phone_number`.
4. Skrypt wykonuje podstawową walidację i normalizację pól (np. usuwanie spacji, formatowanie numerów, parsowanie kwot).
5. Wynik zapisywany jest w tabeli `applications` w lokalnej bazie `finserve.db` razem z nazwą pliku źródłowego i numerem strony.

## Schemat bazy danych

Tabela `applications`:

- `id` INTEGER PRIMARY KEY
- `source_pdf` TEXT — nazwa pliku źródłowego
- `page_number` INTEGER — numer strony w PDF
- `first_name` TEXT
- `last_name` TEXT
- `company_name` TEXT
- `tax_id` TEXT
- `requested_loan_amount` REAL
- `email` TEXT
- `phone_number` TEXT
- `created_at` TEXT — znaczek czasu w UTC

## Wymagania

- Python 3.8+
- Ollama (lokalny serwer/model)
- Zainstalowane zależności z `requirements.txt` (np. `pdfplumber`, `requests` lub inny klient HTTP do Ollama, `python-dotenv` jeśli używasz .env)

## Instalacja

1. Utwórz i aktywuj wirtualne środowisko (zalecane):

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows cmd
.\.venv\Scripts\activate.bat
```

2. Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

3. Uruchom Ollama (jeśli jeszcze nie działa):

- Uruchom serwer Ollama (desktop app lub CLI). Aby uruchomić serwer przez CLI:

```bash
ollama serve
```

- Upewnij się, że masz pobrany model, np.:

```bash
ollama pull llama3.1:8b
```

## Uruchomienie skryptu

Podstawowa komenda uruchamiająca (z katalogu projektu):

```bash
python main.py --pdf "ścieżka/do/formularza.pdf"
```

Dostępne opcje (przykładowe, zależne od implementacji w `main.py`):

- `--pdf` — ścieżka do pliku PDF (wymagane)
- `--model` — nazwa modelu Ollama (domyślnie `llama3.1:8b` lub wartość z `OLLAMA_MODEL`)
- `--db` — ścieżka do pliku SQLite (domyślnie `finserve.db`)

Przykład z dodatkowymi opcjami:

```bash
# użycie niestandardowego modelu i bazy
python main.py --pdf "applications.pdf" --model "llama3.1:8b" --db "data/finserve.db"
```

## Zmienne środowiskowe

- `OLLAMA_MODEL` — jeśli ustawione, skrypt użyje tej nazwy modelu jako domyślnej.

Przykład (Windows PowerShell):

```powershell
$env:OLLAMA_MODEL = "llama3.1:8b"
```

## Walidacja danych i normalizacja

Skrypt powinien (i w PoC zwykle robi):

- Usunąć nadmiarowe białe znaki
- Rozpoznać i usunąć znaki formatowania w `tax_id`
- Parsować kwoty do formatu liczbowego (float)
- Prosty regex dla `email` i `phone_number` aby wykryć oczywiste błędy

(Jeśli chcesz, mogę dodać rozszerzoną walidację, np. biblioteki do walidacji numerów telefonu lub CPF/NIP zależnie od kraju.)

## Obsługa błędów i troubleshooting

- Jeśli otrzymujesz błąd połączenia z Ollama: sprawdź, czy `ollama serve` działa i czy model jest pobrany (`ollama list`).
- Jeśli model zwraca nieprawidłowy JSON: sprawdź prompt wysyłany do modelu i ewentualnie zwiększ nadzór (więcej przykładów w promptcie) albo wymuś schemat JSON w promptcie.
- Jeśli PDF jest zaszyfrowany/chroniony: odszyfruj go lub sprawdź prawa dostępu.

## Dalsze kroki (opcjonalne usprawnienia)

- Logging operacji do pliku/logu (np. `logging` z rotacją)
- Mapowanie pól z różnymi wariantami formularzy (regelarne wyrażenia przed wywołaniem LLM)
- Testy jednostkowe dla funkcji parsujących i walidujących
- Konteneryzacja (Docker) z zainstalowanym Ollama klienckim lub specyficznymi konfiguracjami

## Pliki w repozytorium

- `main.py` — punkt wejścia skryptu
- `requirements.txt` — zależności Pythona
- `README.md` — ten plik (opis projektu i instrukcje)

## Kontakt / Uwagi

Jeśli chcesz, rozbuduję instrukcję o przykładowy prompt używany do przetwarzania tekstu przez LLM oraz pokażę przykładowe fragmenty JSON zwracane przez model.
