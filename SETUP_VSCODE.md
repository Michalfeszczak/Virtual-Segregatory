# 🚀 Jak Uruchomić Virtual Segregatory w VS Code

## ⚙️ Konfiguracja Projektu

### Krok 1: Otwórz Projekt w VS Code

```bash
# Otwórz folder projektu w VS Code
open -a "Visual Studio Code" /Users/michalfeszczak/Desktop/virtual-segregatory

# LUB przeciągnij folder do VS Code
```

### Krok 2: Zainstaluj Rozszerzenia Python

VS Code pokaże notyfikację: **"Recommended extensions for this workspace"**

Kliknij **"Install All"** lub zainstaluj ręcznie:
- **Python** (ms-python.python) - obowiązkowe
- **Pylance** (ms-python.vscode-pylance) - for IntelliSense
- **Ruff** (charliermarsh.ruff) - linting

### Krok 3: Wybierz Python Interpreter

VS Code powinien automatycznie wybrać `/usr/bin/python3` (już ustawiony w `settings.json`).

Jeśli nie:
1. Naciśnij `Cmd + Shift + P` (Command Palette)
2. Wpisz: `Python: Select Interpreter`
3. Wybierz: `/usr/bin/python3`

### Krok 4: Zainstaluj Zależności

W VS Code, otwórz Terminal (`Ctrl + backtick` lub View → Terminal):

```bash
pip3 install pdfplumber PyPDF2
```

## ▶️ Uruchomienie Programu

### Metoda 1: Debugging (z Breakpoints)

1. Otwórz `main.py`
2. Naciśnij `F5` (Run & Debug)
3. Wybierz: **Virtual Segregatory - Main**
4. Program uruchomi się w debuggingu

### Metoda 2: Run Without Debugging

1. Otwórz `main.py`
2. Naciśnij `Ctrl + F5` (Run Python File)

### Metoda 3: Terminal

```bash
python3 main.py
```

## 🧪 Uruchomienie Testów

### Metoda 1: Debugging

1. Otwórz `quick_start_test.py`
2. Naciśnij `F5`
3. Wybierz: **Virtual Segregatory - Tests**

### Metoda 2: Terminal

```bash
python3 quick_start_test.py
```

## 📂 Struktura Projektu w VS Code

```
virtual-segregatory/
├── 📄 main.py                      # Punkt wejścia
├── ⚙️ config.py                     # Konfiguracja
├── 🧪 quick_start_test.py          # Testy
├── 📋 requirements.txt
├── 📖 README.md
├── 📝 SETUP_VSCODE.md              # Ten plik
│
├── 📁 .vscode/
│   ├── settings.json               # Ustawienia
│   ├── launch.json                 # Debug configurations
│   └── extensions.json             # Rekomendowane rozszerzenia
│
├── 📁 database/
│   ├── __init__.py
│   └── db_manager.py               # SQLite operations
│
└── 📁 modules/
    ├── __init__.py
    ├── pdf_reader.py               # Czytanie PDF
    └── kw_extractor.py             # Rozpoznawanie KW
```

## 🎯 Workflow w VS Code

### 1. **Edycja Kodu**

Otwórz dowolny plik `.py` i edytuj. VS Code automatycznie:
- ✅ Formatuje kod (Black formatter)
- ✅ Pokazuje błędy (Pylance IntelliSense)
- ✅ Sugeruje poprawki

### 2. **Debugowanie**

Ustaw breakpoint (kliknij w lewym marginesie linii):

```python
# Linia 42 - kliknij tutaj aby ustawić breakpoint
db = DatabaseManager(CONFIG['db_path'])
```

Naciśnij `F5` i program zatrzyma się na breakpoincie.

### 3. **Running Tests**

Kliknij **Test Explorer** w lewym panelu (najniżej) lub:

```bash
python3 -m pytest quick_start_test.py -v
```

### 4. **Git Integration**

VS Code ma wbudowany Git. Użyj lewego panelu:
- **Source Control** (Ctrl + Shift + G)
- Commit, Push, Pull bezpośrednio z VS Code

## 🔧 Przydatne Keyboard Shortcuts

| Skrót | Akcja |
|-------|-------|
| `F5` | Start Debugging |
| `Ctrl + F5` | Run Without Debugging |
| `Cmd + Shift + P` | Command Palette |
| `Ctrl + ~` | Toggle Terminal |
| `Cmd + /` | Comment/Uncomment |
| `Cmd + D` | Select Word |
| `F2` | Rename Symbol |
| `Ctrl + Shift + F` | Find in Files |

## 📊 Python Environment

VS Code zobaczył już Python interpreter z `settings.json`:

```json
"python.defaultInterpreterPath": "/opt/homebrew/bin/python3.10"
```

Jeśli coś nie działa, sprawdź:

1. **Terminal:**
```bash
which python3
python3 --version
```

2. **VS Code Settings (Cmd + ,):**
   - Search: "Python: Default Interpreter Path"
   - Ustaw: `/opt/homebrew/bin/python3.10`

## ⚠️ Troubleshooting

### Problem: "No module named 'pdfplumber'"

**Przyczyna:** VS Code używa innego interpretera Pythona

**Rozwiązanie:**
1. **Cmd + Shift + P** → `Python: Select Interpreter`
2. Wybierz: `/usr/bin/python3` (SYSTEM PYTHON)
3. **NIE** wybieraj `/opt/homebrew/...`

LUB w terminalu:
```bash
/usr/bin/python3 -m pip install pdfplumber PyPDF2
```

### Problem: "Python module not found" (config, modules, etc)

**Przyczyna:** Zły interpreter

**Rozwiązanie:**
1. **Cmd + Shift + P** → `Python: Select Interpreter`
2. Wybierz: `/usr/bin/python3`
3. Reload VS Code (Cmd + R) lub zamknij/otwórz projekt

### Problem: "No module named 'config'"

**Rozwiązanie:**
- Otwórz folder `/Users/michalfeszczak/Desktop/virtual-segregatory/` (główny folder projektu)
- Nie otwieraj subfolderu

### Problem: Breakpoints nie działają

**Rozwiązanie:**
1. Zainstaluj debugpy: `pip3 install debugpy`
2. Sprawdź: VS Code → Run and Debug → Select Configuration
3. Upewnij się że Python interpreter to `/usr/bin/python3`

### Szybki Test

Jeśli coś nie działa, otwórz Terminal w VS Code (`Ctrl + ~`) i uruchom:

```bash
python3 quick_start_test.py
```

Jeśli testy przejdą → VS Code będzie działać. Jeśli nie → problem z interpreterem.

## 🚀 To Do Po Otwarciu

- [ ] Zainstaluj Python rozszerzenia
- [ ] Wybierz Python interpreter (`/opt/homebrew/bin/python3.10`)
- [ ] Zainstaluj zależności: `pip3 install pdfplumber PyPDF2`
- [ ] Uruchom testy: `F5` → "Virtual Segregatory - Tests"
- [ ] Uruchom main: `F5` → "Virtual Segregatory - Main"
- [ ] Zaimportuj swój PDF

## 💡 Pro Tips

1. **Workspace Settings** — Projekt ma `.vscode/settings.json` specjalnie dla niego
2. **Debug Console** — Podczas debugowania możesz pisać Python w Debug Console
3. **IntelliSense** — Pylance pokaże autocomplete dla wszystkich modułów
4. **Terminal** — Terminal w VS Code ma dostęp do całego environment
5. **Git** — Można commitować prosto z VS Code

---

**Gotowy do pracy!** Naciśnij `F5` aby zacząć. 🚀
