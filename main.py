#!/usr/bin/env python3
import sys
from pathlib import Path
from database import DatabaseManager
from modules import PDFReader, KWExtractor
from config import CONFIG

def init_database():
    """Inicjalizacja bazy danych"""
    print("📊 Inicjalizacja bazy danych...")
    db = DatabaseManager(CONFIG['db_path'])
    db.connect()
    db.init_database()
    db.disconnect()
    print("✅ Baza danych gotowa!\n")

def import_pdf(pdf_path, binder_name="Default"):
    """Import i przetwarzanie PDF"""
    print(f"📄 Importowanie PDF: {pdf_path}")

    # Inicjalizacja
    reader = PDFReader()
    extractor = KWExtractor()
    db = DatabaseManager(CONFIG['db_path'])

    if not db.connect():
        return False

    # Odczyt PDF
    pdf_data = reader.read_pdf(pdf_path)
    if not pdf_data:
        db.disconnect()
        return False

    print(f"  ✓ Stron: {pdf_data['page_count']}")

    # Dodaj segregator
    binder_id = db.add_binder(binder_name)
    print(f"  ✓ Segregator ID: {binder_id}")

    # Dodaj plik
    file_id = db.add_source_file(
        binder_id,
        pdf_data['filename'],
        pdf_data['filepath'],
        pdf_data['file_hash'],
        pdf_data['page_count']
    )
    print(f"  ✓ Plik ID: {file_id}")

    # Przetwórz strony i ekstrahuj KW
    all_kws = {}
    for page_data in pdf_data['pages']:
        page_num = page_data['page_number']
        text = page_data['text']

        # Dodaj stronę do bazy
        page_id = db.add_page(file_id, page_num, text)

        # Ekstrahuj KW
        kws = extractor.extract_from_text(text, page_num)
        for kw in kws:
            kw_full = kw['kw_full']
            if kw_full not in all_kws:
                all_kws[kw_full] = kw.copy()
                all_kws[kw_full]['pages'] = []
            all_kws[kw_full]['pages'].append(page_num)

            # Dodaj do bazy
            kw_id = db.add_land_register(
                kw_full,
                kw['kw_district'],
                kw['kw_number'],
                kw['kw_checksum']
            )
            db.add_land_register_occurrence(
                kw_id,
                page_id,
                file_id,
                kw['context_before'],
                kw['context_after']
            )

    # Podsumowanie
    print(f"\n📖 Księgi Wieczyste znalezione: {len(all_kws)}")
    if all_kws:
        print("  Znalezione KW:")
        for kw_full, data in sorted(all_kws.items()):
            pages_str = ', '.join(map(str, data['pages']))
            status = "✓" if data['valid_checksum'] else "?"
            print(f"    {status} {kw_full} (str. {pages_str})")

    db.disconnect()
    print("✅ Import zakończony!\n")
    return True

def show_statistics():
    """Pokaż statystyki"""
    db = DatabaseManager(CONFIG['db_path'])
    if not db.connect():
        return

    stats = db.get_statistics()
    print("\n📊 Statystyki:")
    print(f"  Segregatory: {stats['binders']}")
    print(f"  Pliki PDF: {stats['files']}")
    print(f"  Strony: {stats['pages']}")
    print(f"  Księgi Wieczyste: {stats['land_registers']}")

    # Pokaż wszystkie KW
    print("\n📖 Księgi Wieczyste w bazie:")
    land_registers = db.get_all_land_registers()
    if land_registers:
        for lr in land_registers:
            owner = lr['owner_manual'] or "—"
            print(f"  {lr['kw_full']} (okręg: {lr['kw_district']}) | Właściciel: {owner} | W {lr['files_count']} plikach, {lr['pages_count']} stronach")
    else:
        print("  Brak wpisów")

    db.disconnect()

def list_land_registers():
    """Lista Ksiąg Wieczystych"""
    db = DatabaseManager(CONFIG['db_path'])
    if not db.connect():
        return

    print("\n📖 Wszystkie Księgi Wieczyste w bazie:\n")
    land_registers = db.get_all_land_registers()

    if not land_registers:
        print("Brak wpisów w bazie.")
        db.disconnect()
        return

    for lr in land_registers:
        owner = lr['owner_manual'] or "—"
        print(f"KW: {lr['kw_full']}")
        print(f"  Okręg: {lr['kw_district']}")
        print(f"  Adres: {lr['property_address'] or '—'}")
        print(f"  Właściciel: {owner}")
        print(f"  Znaleziono w: {lr['files_count']} plikach, {lr['pages_count']} stronach")
        print()

    db.disconnect()

def main():
    print("🏛️  Virtual Segregatory v1.0\n")

    # Tworzenie katalogów
    for dir_path in [CONFIG['imports_dir'], CONFIG['exports_dir']]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Inicjalizacja bazy (jeśli nie istnieje)
    db_path = Path(CONFIG['db_path'])
    if not db_path.exists():
        init_database()

    # Menu
    print("Co chcesz zrobić?")
    print("  1. Importuj PDF")
    print("  2. Pokaż Księgi Wieczyste")
    print("  3. Pokaż statystyki")
    print("  4. Exit")
    print()

    choice = input("Wybór (1-4): ").strip()

    if choice == "1":
        pdf_path = input("Ścieżka do PDF: ").strip()
        binder = input("Nazwa segregatora (domyślnie 'Default'): ").strip() or "Default"
        import_pdf(pdf_path, binder)

    elif choice == "2":
        list_land_registers()

    elif choice == "3":
        show_statistics()

    elif choice == "4":
        print("Dziękuję! 👋")
        sys.exit(0)

    else:
        print("❌ Nieprawidłowy wybór!")

if __name__ == "__main__":
    main()
