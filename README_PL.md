# 🏛️ Virtual Segregatory - Kompletny System Zarządzania Dokumentami

**Polskie Wydanie | Pełny System | Gotowy do Użytku**

---

## 🎯 Co to Jest?

**Virtual Segregatory** to lokalny system do:
- ✅ Indeksowania i archiwizacji skanów (PDF)
- ✅ Automatycznego rozpoznawania tekstu (OCR)
- ✅ Wyszukiwania w dokumentach
- ✅ Zarządzania Księgami Wieczyste
- ✅ Raporów i eksportu do Excel

**Bez chmury. Bez abonamentu. Lokalnie na Twoim Maku.**

---

## 🚀 Szybki Start (5 minut)

### 1️⃣ Uruchom Aplikację
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory
python3 app.py
```

### 2️⃣ Otwórz Przeglądarkę
```
http://localhost:5001
```

### 3️⃣ Wgraj PDFy i Czekaj na OCR
- Kliknij 📤 Import PDF
- Przeciągnij/wybierz PDF
- Czekaj ~ 1-2 min na OCR

### 4️⃣ Szukaj, Edytuj, Eksportuj
- 🔍 Szukaj tekstu
- ✏️ Edytuj błędy OCR
- 📥 Eksportuj do Excel

---

## 📋 Co Masz

### Główne Funkcjonalności
| Funkcja | Opis | Status |
|---------|------|--------|
| 📤 Import PDF | Wgrywanie dokumentów | ✅ |
| 🤖 OCR | Automatyczne skanowanie tekstu | ✅ |
| 📄 PDF Viewer | Przeglądanie w przeglądarce | ✅ |
| 📖 Księgi Wieczyste | Zarządzanie KW | ✅ |
| 🔍 Szukanie | Wyszukiwanie globalne | ✅ |
| ✏️ Edycja | Poprawianie OCR | ✅ |
| 📚 Słownik | User Dictionary | ✅ |
| 📊 Raporty | KW + Coverage | ✅ |
| 📥 Eksport | Excel/CSV | ✅ |
| 📁 Batch Import | Import folderów | ✅ |

---

## 📊 Interfejs

### 7 Zakładek w Przeglądarce

1. **📤 Import PDF**
   - Przeciągnij PDF tutaj
   - Auto-OCR
   - Batch import z folderu

2. **📁 Pliki PDF**
   - Lista wszystkich PDFów
   - Pełny OCR scan
   - Otwieranie w viewerze

3. **📖 Księgi Wieczyste**
   - Lista KW (SZ1S/00012345/6)
   - Edycja właściciela
   - Dodawanie ręczne

4. **🔍 Szukaj**
   - Wyszukiwanie we wszystkich dokumentach
   - Wyniki z numerami stron
   - Kontekst znalezonego tekstu

5. **📚 Słownik**
   - Dodawanie poprawek
   - WM → Wspólnota Mieszkaniowa
   - Auto-zastępowanie

6. **📊 Raporty**
   - Raport Ksiąg Wieczystych
   - Coverage (% zindeksowanych)
   - Eksport CSV

7. **📈 Statystyki**
   - Liczba segregatorów
   - Liczba plików
   - Liczba stron
   - Liczba KW

---

## 🎯 Praktyczne Scenariusze

### Scenariusz 1: Skan Segregatora
```
1. Skanuj segregator: ScanSnap iX1600
   ↓
2. PDFy trafiają do folderu imports/
   ↓
3. Kliknij "📁 Batch Import"
   ↓
4. OCR skanuje wszystkie automatycznie
   ↓
5. Wyniki w Plikach PDF
```

### Scenariusz 2: Szukanie Dokumentu
```
1. Wpisz: "Jan Kowalski"
2. System szuka we wszystkich dokumentach
3. Pokazuje strony i kontekst
4. Kliknij → PDF Viewer → czytaj
```

### Scenariusz 3: Edycja Błędów OCR
```
1. Otwórz PDF
2. Kliknij "✏️ Edytuj tekst"
3. Popraw: "Zdzistaw" → "Zdzisław"
4. Kliknij "Zapisz poprawki"
5. Dalsze szukania będą dokładne
```

### Scenariusz 4: Export do Excel
```
1. Przejdź do 📖 Księgi Wieczyste
2. Kliknij "📥 Eksport Excel"
3. Pobiera się plik z wszystkimi KW
4. Otwórz w Excelu
```

---

## 💾 Gdzie Są Dane?

```
/Users/michalfeszczak/Desktop/virtual-segregatory/

├── virtual_segregatory.db    ← BAZA DANYCH
├── imports/                  ← PDFy DO WGRANIA
├── exports/                  ← POBIERANE PLIKI
└── templates/index.html      ← INTERFEJS
```

### Rozmiar
- **6000 stron A4** → ~100MB na dysku
- Baza: ~10-20MB
- PDFy: ~80-90MB

---

## ⚙️ Wymagania

- **Mac** (tested na macOS Monterey+)
- **Python 3.9+**
- **Tesseract** (dla OCR)

### Instalacja Tesseracta
```bash
brew install tesseract
```

---

## 🔧 Troubleshooting

### Problem: "Port 5001 in use"
```bash
# Przycisk aplikacji w tle
lsof -i :5001 | grep python3 | awk '{print $2}' | xargs kill -9

# Restart
python3 app.py
```

### Problem: "No module named 'flask'"
```bash
pip3 install Flask Flask-CORS pdfplumber pytesseract openpyxl
python3 app.py
```

### Problem: OCR nie działa
```bash
# Sprawdź Tesseract
which tesseract

# Jeśli nie ma:
brew install tesseract

# Restart aplikacji
python3 app.py
```

---

## 📚 Zawartość

```
📦 virtual-segregatory/
├── 🐍 Python
│   ├── app.py                 ← APLIKACJA
│   ├── config.py              ← KONFIGURACJA
│   ├── main.py                ← CLI (opcjonalnie)
│   └── requirements.txt        ← ZALEŻNOŚCI
│
├── 🗄️ Database
│   ├── database/
│   │   ├── db_manager.py      ← BAZA DANYCH
│   │   └── schema.sql         ← SCHEMAT
│   └── virtual_segregatory.db ← DANE
│
├── 📦 Modules
│   ├── modules/
│   │   ├── pdf_reader.py      ← CZYTANIE PDF
│   │   ├── kw_extractor.py    ← KW PARSING
│   │   └── __init__.py
│   └── search/searcher.py     ← WYSZUKIWANIE
│
├── 🌐 Frontend
│   ├── templates/
│   │   └── index.html         ← INTERFEJS
│   └── static/ (optional)
│
├── 📂 Data
│   ├── imports/               ← NOWE PDFy
│   ├── exports/               ← POBIERANE
│   └── data/                  ← CONFIG
│
├── .vscode/                   ← VS CODE
│   ├── settings.json
│   ├── launch.json
│   └── extensions.json
│
└── 📖 Documentation
    ├── README.md              ← ENG
    ├── README_PL.md           ← PL (ten plik)
    ├── MVP1_SUMMARY.md
    ├── MVP2_COMPLETE.md
    ├── SETUP_VSCODE.md
    ├── QUICK_FIX.md
    └── TERMINAL_COMMANDS.md
```

---

## 🧪 Testy

Wszystkie funkcjonalności przesły testy:

```
✅ 10/10 testów MVP2 przeszło
✅ OCR - działa
✅ PDF Viewer - działa
✅ Wyszukiwanie - działa
✅ Edycja - działa
✅ Batch Import - działa
✅ Raporty - działają
✅ Słownik - działa
✅ Export - działa
```

---

## 📖 Dokumentacja

- **README.md** - English version
- **README_PL.md** - Polish (ten plik)
- **MVP2_COMPLETE.md** - Pełny opis MVP2
- **SETUP_VSCODE.md** - VS Code setup
- **QUICK_FIX.md** - Szybkie rozwiązania

---

## 🚨 Ważne

### Bezpieczeństwo
- ✅ Lokalnie na Twoim komputerze
- ✅ Żadne dane do chmury
- ✅ Bez internetu
- ✅ SQLite (nie potrzeba serwera)

### Backup
```bash
# Skopiuj całą bazę
cp virtual_segregatory.db virtual_segregatory_backup.db
```

---

## 🎓 Instrukcja Dla Początkujących

### Krok 1: Otwórz Terminal
```
Applications → Utilities → Terminal
```

### Krok 2: Wklej i Enter
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory && python3 app.py
```

### Krok 3: Czekaj ~10 sekund
```
Powinieneś zobaczyć:
✅ Otwórz przeglądarkę: http://localhost:5001
```

### Krok 4: Otwórz Przeglądarkę
```
Cmd + T (nowa karta)
Wpisz: localhost:5001
Enter
```

### Krok 5: Wgraj PDFy
```
Kliknij: 📤 Import PDF
Przeciągnij PDFy
Czekaj na OCR
```

### Krok 6: Szukaj
```
Kliknij: 🔍 Szukaj
Wpisz imię lub adres
Enter
```

---

## 💡 Porady

1. **Batch Import dla dużo PDFów**
   - Umieść wszystkie w `imports/`
   - Kliknij "📁 Batch Import"
   - Czekaj 5-10 minut

2. **Słownik dla poprawek**
   - Dodaj częste błędy OCR
   - Przy rescan - auto-poprawią się

3. **Export Excel**
   - Zawsze przed ważnym sprawdzeniem
   - Łatwo udostępnić innym

4. **Backup**
   - Co tydzień: `cp virtual_segregatory.db backup.db`

---

## 📞 Co Robić Jeśli...

| Problem | Rozwiązanie |
|---------|-------------|
| Aplikacja nie startuje | `python3 app.py` |
| Port zajęty | `kill -9 PID` (z lsof) |
| Brak pdfplumber | `pip3 install pdfplumber` |
| OCR nie działa | `brew install tesseract` |
| Resetuj bazę | `rm virtual_segregatory.db` |

---

## 🎉 Gotowe!

**Gratuluję! Masz pełny system zarządzania dokumentami.**

Wszystko co potrzebujesz:
- ✅ Skanowanie (OCR)
- ✅ Przechowywanie (SQLite)
- ✅ Wyszukiwanie
- ✅ Edycja
- ✅ Raporty
- ✅ Export

---

## 📌 Podsumowanie

```
🏛️  Virtual Segregatory
├── 6000+ stron A4
├── 100% lokalnie
├── Bez abonamentu
├── Szybkie wyszukiwanie
├── Proste w użytkowaniu
└── GOTOWE! ✅
```

**Powodzenia!** 🚀
