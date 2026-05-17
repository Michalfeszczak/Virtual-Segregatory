# 💻 Terminal Commands - Kopiuj & Wklej

## 🚀 Podstawowe Setup

### 1. Przejdź do folderu projektu
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory
```

### 2. Zainstaluj zależności (raz na początku)
```bash
pip3 install pdfplumber PyPDF2
```

### 3. Sprawdź czy wszystko działa (uruchom testy)
```bash
python3 quick_start_test.py
```

---

## ▶️ Uruchamianie Programu

### Uruchom główny program
```bash
python3 main.py
```

### Uruchom program z debugiem
```bash
python3 -m pdb main.py
```

---

## 🧪 Testowanie

### Uruchom wszystkie testy
```bash
python3 quick_start_test.py
```

### Uruchom testy w verbose mode
```bash
python3 -m pytest quick_start_test.py -v 2>/dev/null || python3 quick_start_test.py
```

---

## 📁 Zarządzanie Plikami

### Pokaż zawartość folderu
```bash
ls -la
```

### Pokaż strukturę projektu
```bash
find . -type f -name "*.py" | sort
```

### Pokaż rozmiar bazy danych
```bash
ls -lh virtual_segregatory.db
```

### Usuń bazę danych (start od nowa)
```bash
rm virtual_segregatory.db
```

---

## 🔍 Python Info

### Sprawdź wersję Pythona
```bash
python3 --version
```

### Sprawdź gdzie jest Python
```bash
which python3
```

### Sprawdź zainstalowane pakiety
```bash
pip3 list | grep -E "pdfplumber|PyPDF2"
```

### Aktualizuj pip
```bash
pip3 install --upgrade pip
```

---

## 📊 Baza Danych

### Sprawdź bazę SQLite (zainstaluj jeśli brakuje)
```bash
which sqlite3
```

### Otwórz bazę w interactive mode
```bash
sqlite3 virtual_segregatory.db
```

### W SQLite terminal (`.quit` aby wyjść):
```sql
-- Pokaż wszystkie tabele
.tables

-- Pokaż schemat
.schema

-- Pokaż liczę KW
SELECT COUNT(*) FROM land_registers;

-- Pokaż wszystkie KW
SELECT * FROM land_registers;

-- Wyjdź
.quit
```

---

## 🔧 VS Code

### Otwórz projekt w VS Code
```bash
code /Users/michalfeszczak/Desktop/virtual-segregatory
```

### Lub
```bash
open -a "Visual Studio Code" /Users/michalfeszczak/Desktop/virtual-segregatory
```

---

## 📝 Edycja Plików

### Edytuj main.py w Nano
```bash
nano main.py
```

### Edytuj config.py w Nano
```bash
nano config.py
```

(Aby wyjść z Nano: `Ctrl + X`, `Y`, `Enter`)

---

## 🗑️ Czyszczenie

### Usuń cache Python
```bash
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
```

### Usuń pliki .pyc
```bash
find . -name "*.pyc" -delete
```

### Usuń bazę danych i start od nowa
```bash
rm virtual_segregatory.db && python3 main.py
```

---

## 📊 Monitorowanie

### Obserwuj pliki (jeśli się zmieniają)
```bash
ls -l *.py | head -10
```

### Pokaż ostatnie 20 linii z output
```bash
python3 main.py 2>&1 | tail -20
```

---

## 🔗 Przydatne One-Liners

### Uruchom testy i pokaż wynik
```bash
python3 quick_start_test.py && echo "✅ Sukces!" || echo "❌ Błąd!"
```

### Import PDF + statystyki
```bash
python3 -c "from main import import_pdf, show_statistics; import_pdf('test.pdf'); show_statistics()"
```

### Pokaż liczbę linii kodu
```bash
find . -name "*.py" -type f | xargs wc -l | tail -1
```

### Pokaż wszystkie KW z bazy
```bash
sqlite3 virtual_segregatory.db "SELECT kw_full, property_address, owner_manual FROM land_registers;"
```

---

## 📦 Git Commands (opcjonalnie)

### Inicjalizuj git
```bash
git init
```

### Dodaj wszystkie pliki
```bash
git add .
```

### Commit
```bash
git commit -m "Initial Virtual Segregatory setup"
```

### Sprawdź status
```bash
git status
```

---

## 🎯 Szybkie Komendy do Copy-Paste

**Setup (wykonaj raz):**
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory && pip3 install pdfplumber PyPDF2
```

**Test (sprawdzenie czy działa):**
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory && python3 quick_start_test.py
```

**Run program (uruchomienie):**
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory && python3 main.py
```

**Otwórz w VS Code:**
```bash
open -a "Visual Studio Code" /Users/michalfeszczak/Desktop/virtual-segregatory
```

**Otwórz bazę danych:**
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory && sqlite3 virtual_segregatory.db
```

---

## 📌 Najczęściej Używane

| Co Chcę Zrobić | Komenda |
|---|---|
| Uruchomić program | `python3 main.py` |
| Uruchomić testy | `python3 quick_start_test.py` |
| Zainstalować pakiety | `pip3 install pdfplumber PyPDF2` |
| Otwórz w VS Code | `code .` |
| Pokaż bazę | `sqlite3 virtual_segregatory.db` |
| Usuń bazę (reset) | `rm virtual_segregatory.db` |
| Pokaż pliki | `ls -la` |
| Edytuj plik | `nano plik.py` |

---

**Happy Coding!** 🚀
