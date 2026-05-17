import os
from pathlib import Path

# Ścieżki
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
IMPORTS_DIR = BASE_DIR / "imports"
EXPORTS_DIR = BASE_DIR / "exports"

# Tworzy katalogi jeśli nie istnieją
for directory in [DATA_DIR, DATABASE_DIR, IMPORTS_DIR, EXPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Baza danych
DB_PATH = BASE_DIR / "virtual_segregatory.db"

# Konfiguracja
CONFIG = {
    'db_path': str(DB_PATH),
    'imports_dir': str(IMPORTS_DIR),
    'exports_dir': str(EXPORTS_DIR),
    'encoding': 'utf-8',
}

# Słowniki i reguły
POLISH_FIRST_NAMES_MALE = [
    'Jan', 'Piotr', 'Zdzisław', 'Andrzej', 'Krzysztof', 'Stanisław',
    'Jerzy', 'Tadeusz', 'Wojciech', 'Zbigniew', 'Kazimierz', 'Michał',
    'Henryk', 'Franciszek', 'Ignacy', 'Bolesław', 'Edmund', 'Eugeniusz',
    'Ryszard', 'Konrad', 'Roman', 'Marian', 'Czesław', 'Mieczysław',
    'Zygmunt', 'Józef', 'Adam', 'Jarosław', 'Grzegorz', 'Marek',
    'Dariusz', 'Tomasz', 'Paweł', 'Lech', 'Sławomir', 'Benedykt',
    'Ludwik', 'Cyprian', 'Alistair', 'Arkadiusz', 'Bartłomiej', 'Bogdan',
]

POLISH_FIRST_NAMES_FEMALE = [
    'Anna', 'Maria', 'Barbara', 'Katarzyna', 'Marta', 'Joanna',
    'Ewa', 'Halina', 'Wanda', 'Danuta', 'Helena', 'Irena',
    'Zofia', 'Stanisława', 'Krystyna', 'Aniela', 'Urszula', 'Lucyna',
    'Iga', 'Grażyna', 'Elżbieta', 'Aleksandra', 'Jadwiga', 'Monika',
    'Lidia', 'Bogna', 'Bronisława', 'Celina', 'Dorota', 'Ewa',
]

INSTITUTIONS = {
    'Sąd': ['Sąd Rejonowy', 'Sąd Okręgowy', 'Sąd Apelacyjny', 'Sąd Najwyższy'],
    'Urząd': ['Urząd Gminy', 'Urząd Miasta', 'Urząd Wojewódzki', 'Urząd Skarbowy'],
    'Bank': ['Bank PKO', 'Bank Santander', 'ING Bank', 'Alior Bank', 'PKN Bank'],
}

# Wzorce dla Ksiąg Wieczystych
KW_PATTERN = r'([A-Z]{2}\d{1,2}[A-Z]{1,2})[/\s\-]?(\d{8})[/\s\-]?(\d)'
