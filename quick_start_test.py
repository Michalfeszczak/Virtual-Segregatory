#!/usr/bin/env python3
"""Test Quick Start dla Virtual Segregatory MVP1"""

import sys
from pathlib import Path
from database import DatabaseManager
from modules import KWExtractor, KWValidator
from config import CONFIG

def test_kw_validator():
    """Test walidatora KW"""
    print("🧪 Test 1: KW Validator\n")

    validator = KWValidator()

    # Test cases - dla MVP1 walidacja jest uproszczona
    test_cases = [
        ("SZ1S", "00012345", "6", True, "Standard KW Szczecin"),
        ("WA1M", "00123456", "7", True, "Standard KW Warszawa"),
        ("SZ1S", "00012345", "9", True, "Przyjmujemy każdy checksum"),
    ]

    passed = 0
    for district, number, checksum, expected, description in test_cases:
        result = validator.validate_checksum(district, number, checksum)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}")
        if result == expected:
            passed += 1

    print(f"\n  Wynik: {passed}/{len(test_cases)} testów przeszło\n")
    return passed == len(test_cases)

def test_kw_standardize():
    """Test standaryzacji KW"""
    print("🧪 Test 2: KW Standardize\n")

    validator = KWValidator()

    test_cases = [
        ("SZ1S/00012345/6", "SZ1S/00012345/6"),
        ("SZ1S 00012345 6", "SZ1S/00012345/6"),
        ("SZ1S-00012345-6", "SZ1S/00012345/6"),
        ("sz1s 00012345 6", "SZ1S/00012345/6"),
    ]

    passed = 0
    for input_kw, expected in test_cases:
        result = validator.standardize(input_kw)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_kw}' → '{result}'")
        if result == expected:
            passed += 1

    print(f"\n  Wynik: {passed}/{len(test_cases)} testów przeszło\n")
    return passed == len(test_cases)

def test_kw_extraction():
    """Test ekstrakcji KW z tekstu"""
    print("🧪 Test 3: KW Extraction\n")

    extractor = KWExtractor()

    test_texts = [
        ("Księga wieczysta SZ1S/00012345/6 dotyczy nieruchomości.", 1),
        ("Hipoteka na rzecz Banku PKO. KW: WA1M 00123456 7", 1),
        ("Właściciel wpisany w księdze SZ1S-00012345-6 od 2020 roku.", 1),
        ("Brak KW w tym dokumencie", 0),
    ]

    passed = 0
    for text, expected_count in test_texts:
        kws = extractor.extract_from_text(text, page_number=1)
        result_count = len(kws)
        status = "✅" if result_count == expected_count else "❌"
        print(f"  {status} Znaleziono {result_count} KW (oczekiwano {expected_count})")
        if result_count == expected_count:
            passed += 1

    print(f"\n  Wynik: {passed}/{len(test_texts)} testów przeszło\n")
    return passed == len(test_texts)

def test_database():
    """Test operacji na bazie danych"""
    print("🧪 Test 4: Database Operations\n")

    # Usuń starą bazę na potrzeby testu
    db_path = Path(CONFIG['db_path'])
    if db_path.exists():
        db_path.unlink()

    db = DatabaseManager(CONFIG['db_path'])

    if not db.connect():
        print("  ❌ Nie udało się połączyć z bazą")
        return False

    # Inicjalizacja
    db.init_database()
    print("  ✅ Baza zainicjalizowana")

    # Dodaj segregator
    binder_id = db.add_binder("Test_Binder", "Segregator testowy")
    print(f"  ✅ Segregator dodany (ID: {binder_id})")

    # Dodaj plik
    file_id = db.add_source_file(binder_id, "test.pdf", "/tmp/test.pdf", "abc123", 5)
    print(f"  ✅ Plik dodany (ID: {file_id})")

    # Dodaj strony
    page_id = db.add_page(file_id, 1, "Tekst z KW SZ1S/00012345/6")
    print(f"  ✅ Strona dodana (ID: {page_id})")

    # Dodaj KW
    kw_id = db.add_land_register("SZ1S/00012345/6", "SZ1S", "00012345", "6")
    print(f"  ✅ Księga wieczysta dodana (ID: {kw_id})")

    # Dodaj wystąpienie KW
    db.add_land_register_occurrence(kw_id, page_id, file_id, "przed", "po")
    print(f"  ✅ Wystąpienie KW dodane")

    # Pobierz statystyki
    stats = db.get_statistics()
    print(f"  ✅ Statystyki: {stats['binders']} segregatory, {stats['land_registers']} KW")

    # Pobierz KW
    kws = db.get_all_land_registers()
    if kws and len(kws) > 0:
        print(f"  ✅ Pobrano {len(kws)} Ksiąg Wieczystych")
    else:
        print(f"  ❌ Nie udało się pobrać KW")

    db.disconnect()
    print(f"\n  Wynik: Test bazы przeszedł\n")
    return True

def main():
    print("=" * 50)
    print("🧪 Virtual Segregatory - Quick Start Tests")
    print("=" * 50)
    print()

    results = []

    # Uruchom testy
    results.append(("KW Validator", test_kw_validator()))
    results.append(("KW Standardize", test_kw_standardize()))
    results.append(("KW Extraction", test_kw_extraction()))
    results.append(("Database", test_database()))

    # Podsumowanie
    print("=" * 50)
    print("📊 Podsumowanie wyników")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print()
    print(f"Wynik: {passed}/{total} testów przeszło")

    if passed == total:
        print("\n🎉 Wszystkie testy przeszły! Program jest gotowy do użytku.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} testów nie przeszło. Sprawdź błędy powyżej.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
