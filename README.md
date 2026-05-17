# 🏛️ Virtual Segregatory MVP1

System indeksowania i wyszukiwania dokumentów PDF lokalnie, ze specjalnym fokusem na **Księgi Wieczyste (KW)**.

## 📋 Funkcjonalność

✅ Czytanie i indeksowanie PDF-ów  
✅ Automatyczne rozpoznawanie **Ksiąg Wieczystych** (SZ1S/00012345/6)  
✅ Obsługa wariantów OCR i formatowania (spacje, myślniki)  
✅ Baza danych SQLite (działą lokalnie)  
✅ Wyszukiwanie stron z KW  
✅ Statystyki i raporty  

## 🚀 Quick Start

### 1. Instalacja

```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory
pip3 install pdfplumber PyPDF2
```

### 2. Testy

```bash
python3 quick_start_test.py
```

Oczekiwany wynik: **4/4 testów przeszło** ✅

### 3. Uruchomienie programu

```bash
python3 main.py
```

## 📂 Struktura Projektu

```
virtual-segregatory/
├── main.py                # Program główny
├── config.py              # Konfiguracja
├── requirements.txt       # Zależności
├── quick_start_test.py    # Testy
│
├── database/
│   ├── __init__.py
│   └── db_manager.py      # SQLite operations
│
├── modules/
│   ├── __init__.py
│   ├── pdf_reader.py      # Czytanie PDF
│   └── kw_extractor.py    # Rozpoznawanie KW
│
├── data/                  # (katalog dla danych)
├── imports/               # (katalog dla nowych PDF-ów)
└── exports/               # (katalog dla eksportów)
```

## 🗄️ Baza Danych

SQLite z 8 głównymi tabelami:

- **binders** — segregatory
- **source_files** — oryginalne PDFy
- **pages** — strony z tekstem
- **land_registers** — Księgi Wieczyste
- **land_register_occurrences** — gdzie się pojawiają KW
- **entities** — osoby, firmy, etc
- **entity_occurrences** — gdzie są encje
- **search_index** — indeks pełnotekstowy

## 🎯 Użycie

### Import PDF

```python
from main import import_pdf

import_pdf("path/to/file.pdf", "Nazwa Segregatora")
```

### Wyszukiwanie KW

```python
from database import DatabaseManager
from config import CONFIG

db = DatabaseManager(CONFIG['db_path'])
db.connect()

# Wszystkie Księgi Wieczyste
kws = db.get_all_land_registers()
for kw in kws:
    print(f"{kw['kw_full']} - {kw['property_address']}")

db.disconnect()
```

## 📖 Moduł KW Extractor

Rozpoznaje Księgi Wieczyste w różnych formatach:

```
✅ SZ1S/00012345/6       Standard
✅ SZ1S 00012345 6       Spacje
✅ SZ1S-00012345-6       Myślniki
✅ SZIS/00012345/6       Błąd OCR (I→1)
```

## 📊 Dostępne Funkcje w CLI

```
1. Importuj PDF      → czytaj i indeksuj
2. Pokaż KW         → lista wszystkich ksiąg
3. Statystyki       → raporty z bazy
4. Exit             → wyjście
```

## 🧪 Testy

MVP1 zawiera 4 suity testów:

| Test | Status |
|------|--------|
| KW Validator | ✅ PASS |
| KW Standardize | ✅ PASS |
| KW Extraction | ✅ PASS |
| Database Operations | ✅ PASS |

## ⚙️ Konfiguracja

Edytuj `config.py`:

```python
KW_PATTERN = r'...'  # Regex dla Ksiąg Wieczystych
POLISH_FIRST_NAMES_MALE = [...]
POLISH_FIRST_NAMES_FEMALE = [...]
```

## 📈 Plan Dalszy (MVP2, MVP3)

**MVP2:**
- ✨ CLI interfejs z menu
- 🔍 Wyszukiwarka tekstu
- 📊 Eksport Excel
- ✏️ Ręczna edycja danych

**MVP3:**
- 🌐 Web interfejs
- 🔗 Relacje (osoba-firma-KW)
- 📈 Zaawansowane raporty
- ⚡ Optimizacja dla 6000+ stron

## 🔍 Folder Bazy Danych

Po uruchomieniu program automatycznie tworzy:

- `virtual_segregatory.db` — baza SQLite
- `imports/` — katalog na nowe PDFy
- `exports/` — katalog na wyniki
- `data/` — konfiguracja i słowniki

## 💡 Jak Zacząć

1. **Rozpakuj projekt** do Mac
2. **Zainstaluj zależności** (`pip3 install -r requirements.txt`)
3. **Uruchom testy** (`python3 quick_start_test.py`)
4. **Importuj PDFy** (`python3 main.py` → opcja 1)
5. **Szukaj KW** (`python3 main.py` → opcja 2)

## ⚠️ Wymagania

- Python 3.9+
- Mac (testowane na macOS)
- ~50MB na dysku (baza + programy)
- ~100MB RAM

## 📝 Notatki

- SQLite działa całkowicie lokalnie — bez chmury
- Wszystkie dane na Twoim komputerze
- Baza jest szybka dla 6000+ stron
- OCR opiera się na tekście z PDF (bez Tesseract)

## 🆘 Pomoc

Jeśli coś nie działa:

1. Sprawdź czy Python 3.9+ (`python3 --version`)
2. Zainstaluj zależności (`pip3 install pdfplumber PyPDF2`)
3. Uruchom testy (`python3 quick_start_test.py`)
4. Sprawdź `virtual_segregatory.db` czy istnieje

---

**Virtual Segregatory MVP1** — Gotowy do użytku! 🚀
