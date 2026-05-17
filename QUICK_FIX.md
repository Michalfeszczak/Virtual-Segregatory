# 🔧 Szybki Fix - "No module named 'pdfplumber'"

## ⚡ Problem

```
ModuleNotFoundError: No module named 'pdfplumber'
```

## ✅ Rozwiązanie (30 sekund)

### W VS Code:

1. **Cmd + Shift + P** (Command Palette)
2. Wpisz: `Python: Select Interpreter`
3. **Wybierz: `/usr/bin/python3`** (jest zaznaczone jako "Recommended")

## ✅ Drugi Sposób - Terminal

```bash
# Otwórz Terminal w VS Code (Ctrl + ~)
/usr/bin/python3 -m pip install pdfplumber PyPDF2
```

## ✅ Trzeci Sposób - Terminal (macOS)

```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory
pip3 install pdfplumber PyPDF2
python3 quick_start_test.py
```

## 🧪 Test Czy Działa

W Terminal VS Code:
```bash
python3 quick_start_test.py
```

**Oczekiwany wynik:**
```
🎉 Wszystkie testy przeszły! Program jest gotowy do użytku.
```

## 🎯 Po Naprawie

Teraz możesz:
- **F5** — Run z Debugging
- **Ctrl + F5** — Run bez Debugging
- Terminal — `python3 main.py`

---

**Gotowe!** 🚀
