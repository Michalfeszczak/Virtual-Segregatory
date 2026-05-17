# 🌐 Virtual Segregatory - Web UI

Teraz możesz używać aplikacji przez przeglądarke zamiast terminalu!

## 🚀 Uruchomienie

### Krok 1: Otwórz Terminal

```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory
```

### Krok 2: Uruchom aplikację

```bash
python3 app.py
```

### Krok 3: Otwórz przeglądarkę

Kliknij: **http://localhost:5000**

LUB wklej w przeglądarkę: `http://localhost:5000`

---

## 📖 Funkcjonalność

### 📤 Import PDF
1. Przeciągnij PDF na szare pole (lub kliknij aby wybrać)
2. Podaj nazwę segregatora (np. "Nieruchomości 2024")
3. Kliknij "Importuj PDF"
4. Program automatycznie:
   - Czyta PDF
   - Szuka Ksiąg Wieczystych
   - Zapisuje do bazy

### 📖 Księgi Wieczyste
- Wyświetla wszystkie znalezione KW
- Edycja właściciela (kliknij "Edytuj")
- Usuwanie wpisów
- Eksport do Excel

### 🔍 Szukaj
- Szukaj po numerze KW (np. SZ1S/00012345/6)
- Szukaj po adresie lub nazwie

### 📊 Statystyki
- Liczba segregatorów
- Liczba plików PDF
- Liczba stron
- Liczba Ksiąg Wieczystych

### 📥 Eksport
- Eksportuj wszystkie KW do Excel
- Plik zostanie pobrany automatycznie

---

## 🎨 Design

Interfejs jest:
- ✅ Prosty i intuicyjny
- ✅ Responsywny (działa na telefonie)
- ✅ Szybki i nowoczesny
- ✅ Bez komplikacji

---

## ⌨️ Skróty

| Co | Gdzie |
|---|---|
| Importuj PDF | Zakładka "Import PDF" |
| Pokaż wszystkie KW | Zakładka "Księgi Wieczyste" |
| Szukaj | Zakładka "Szukaj" |
| Statystyki | Zakładka "Statystyki" |

---

## 🛑 Zatrzymanie

Aby zatrzymać aplikację:
- W terminalu: **Ctrl + C**

---

## 💡 Szybkie Komendy

### Uruchom web UI
```bash
cd /Users/michalfeszczak/Desktop/virtual-segregatory && python3 app.py
```

### Otwórz przeglądarkę (opcjonalne)
```bash
open http://localhost:5000
```

---

**Gotowe!** Przejdź do przeglądarki i ciesz się! 🚀
