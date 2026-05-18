import sqlite3
from pathlib import Path
import json
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        self._transaction_depth = 0

    def connect(self):
        """Połączenie z bazą"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Błąd połączenia: {e}")
            return False

    def disconnect(self):
        """Zamknięcie połączenia"""
        if self.connection:
            self.connection.close()

    def execute(self, query, params=None):
        """Wykonanie zapytania"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if self._transaction_depth == 0:
                self.connection.commit()
            return cursor
        except Exception as e:
            print(f"❌ Błąd SQL: {e}")
            if self._transaction_depth == 0:
                self.connection.rollback()
                return None
            raise

    def begin(self):
        """Rozpocznij transakcję zbiorczą."""
        if self._transaction_depth == 0:
            self.connection.execute("BEGIN")
        self._transaction_depth += 1

    def commit(self):
        """Zatwierdź transakcję zbiorczą."""
        if self._transaction_depth == 0:
            return
        self._transaction_depth -= 1
        if self._transaction_depth == 0:
            self.connection.commit()

    def rollback(self):
        """Wycofaj aktywną transakcję zbiorczą."""
        self._transaction_depth = 0
        self.connection.rollback()

    @contextmanager
    def transaction(self):
        """Context manager dla jednej większej transakcji."""
        self.begin()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

    def fetch_one(self, query, params=None):
        """Pobierz jeden wiersz"""
        cursor = self.execute(query, params)
        return cursor.fetchone() if cursor else None

    def fetch_all(self, query, params=None):
        """Pobierz wszystkie wiersze"""
        cursor = self.execute(query, params)
        return cursor.fetchall() if cursor else []

    def init_database(self):
        """Inicjalizacja bazy - tworzenie tabel"""
        schema = """
        CREATE TABLE IF NOT EXISTS binders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS source_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            binder_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT,
            file_hash TEXT,
            page_count INTEGER,
            extracted_text BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (binder_id) REFERENCES binders(id)
        );

        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            page_number INTEGER,
            text_content TEXT,
            page_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES source_files(id)
        );

        CREATE TABLE IF NOT EXISTS land_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kw_full TEXT NOT NULL UNIQUE,
            kw_district TEXT,
            kw_number TEXT,
            kw_checksum TEXT,
            property_address TEXT,
            owner_manual TEXT,
            geoportal_url TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS land_register_occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kw_id INTEGER NOT NULL,
            page_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            context_before TEXT,
            context_after TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kw_id) REFERENCES land_registers(id),
            FOREIGN KEY (page_id) REFERENCES pages(id),
            FOREIGN KEY (file_id) REFERENCES source_files(id)
        );

        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_value TEXT NOT NULL,
            normalized_value TEXT,
            validated INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_type, normalized_value)
        );

        CREATE TABLE IF NOT EXISTS entity_occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            page_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            position_x INTEGER,
            position_y INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_id) REFERENCES entities(id),
            FOREIGN KEY (page_id) REFERENCES pages(id),
            FOREIGN KEY (file_id) REFERENCES source_files(id)
        );

        CREATE TABLE IF NOT EXISTS search_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            search_text TEXT,
            FOREIGN KEY (page_id) REFERENCES pages(id)
        );

        CREATE TABLE IF NOT EXISTS user_dictionaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original TEXT NOT NULL,
            replacement TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(original, replacement)
        );

        CREATE TABLE IF NOT EXISTS ocr_corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            original_text TEXT,
            corrected_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES pages(id)
        );

        CREATE TABLE IF NOT EXISTS cooccurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id_1 INTEGER NOT NULL,
            entity_id_2 INTEGER NOT NULL,
            page_id INTEGER NOT NULL,
            FOREIGN KEY (entity_id_1) REFERENCES entities(id),
            FOREIGN KEY (entity_id_2) REFERENCES entities(id),
            FOREIGN KEY (page_id) REFERENCES pages(id),
            UNIQUE(entity_id_1, entity_id_2, page_id)
        );

        CREATE TABLE IF NOT EXISTS document_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES source_files(id),
            UNIQUE(file_id, tag)
        );

        CREATE INDEX IF NOT EXISTS idx_source_files_binder ON source_files(binder_id);
        CREATE INDEX IF NOT EXISTS idx_pages_file ON pages(file_id);
        CREATE INDEX IF NOT EXISTS idx_land_registers_district ON land_registers(kw_district);
        CREATE INDEX IF NOT EXISTS idx_land_register_occurrences_kw ON land_register_occurrences(kw_id);
        CREATE INDEX IF NOT EXISTS idx_entity_occurrences_entity ON entity_occurrences(entity_id);
        CREATE INDEX IF NOT EXISTS idx_search_index_text ON search_index(search_text);

        CREATE VIEW IF NOT EXISTS view_land_registers_summary AS
        SELECT
            lr.id,
            lr.kw_full,
            lr.kw_district,
            lr.kw_number,
            lr.kw_checksum,
            COUNT(DISTINCT lro.file_id) as files_count,
            COUNT(DISTINCT lro.page_id) as pages_count,
            lr.property_address,
            lr.owner_manual,
            lr.geoportal_url
        FROM land_registers lr
        LEFT JOIN land_register_occurrences lro ON lr.id = lro.kw_id
        GROUP BY lr.id;
        """

        for statement in schema.split(';'):
            if statement.strip():
                self.execute(statement)

        print("✅ Baza danych zainicjalizowana")
        return True

    def add_binder(self, name, description=""):
        """Dodaj segregator"""
        query = "INSERT OR IGNORE INTO binders (name, description) VALUES (?, ?)"
        self.execute(query, (name, description))
        return self.fetch_one("SELECT id FROM binders WHERE name = ?", (name,))['id']

    def add_source_file(self, binder_id, filename, filepath, file_hash, page_count):
        """Dodaj plik PDF"""
        query = """
        INSERT INTO source_files (binder_id, filename, filepath, file_hash, page_count)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(query, (binder_id, filename, filepath, file_hash, page_count))
        return self.fetch_one(
            "SELECT id FROM source_files WHERE file_hash = ?",
            (file_hash,)
        )['id']

    def add_page(self, file_id, page_number, text_content):
        """Dodaj stronę"""
        query = """
        INSERT INTO pages (file_id, page_number, text_content, page_hash)
        VALUES (?, ?, ?, ?)
        """
        page_hash = str(hash(text_content))
        cursor = self.execute(query, (file_id, page_number, text_content, page_hash))
        return cursor.lastrowid if cursor else None

    def add_land_register(self, kw_full, kw_district, kw_number, kw_checksum, address=""):
        """Dodaj księgę wieczystą"""
        query = """
        INSERT OR IGNORE INTO land_registers
        (kw_full, kw_district, kw_number, kw_checksum, property_address)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(query, (kw_full, kw_district, kw_number, kw_checksum, address))
        return self.fetch_one("SELECT id FROM land_registers WHERE kw_full = ?", (kw_full,))['id']

    def add_land_register_occurrence(self, kw_id, page_id, file_id, context_before="", context_after=""):
        """Dodaj wystąpienie księgi wieczystej na stronie"""
        query = """
        INSERT INTO land_register_occurrences
        (kw_id, page_id, file_id, context_before, context_after)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(query, (kw_id, page_id, file_id, context_before, context_after))

    def get_statistics(self):
        """Pobierz statystyki"""
        stats = {
            'binders': self.fetch_one("SELECT COUNT(*) as count FROM binders")['count'],
            'files': self.fetch_one("SELECT COUNT(*) as count FROM source_files")['count'],
            'pages': self.fetch_one("SELECT COUNT(*) as count FROM pages")['count'],
            'land_registers': self.fetch_one("SELECT COUNT(*) as count FROM land_registers")['count'],
        }
        return stats

    def get_land_registers_by_district(self, district):
        """Pobierz księgi wieczyste dla okręgu"""
        query = "SELECT * FROM land_registers WHERE kw_district = ? ORDER BY kw_number"
        return self.fetch_all(query, (district,))

    def get_all_land_registers(self):
        """Pobierz wszystkie księgi wieczyste"""
        query = "SELECT * FROM view_land_registers_summary ORDER BY kw_district, kw_number"
        return self.fetch_all(query)
