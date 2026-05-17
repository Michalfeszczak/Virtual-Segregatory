#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime
from database import DatabaseManager
from modules import PDFReader, KWExtractor, EntityExtractor, DocumentTagger
from config import CONFIG
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
CORS(app)

# Inicjalizacja bazy
def init_app():
    db_path = Path(CONFIG['db_path'])
    db = DatabaseManager(CONFIG['db_path'])
    db.connect()
    if not db_path.exists():
        db.init_database()
    db.disconnect()

init_app()

# API ENDPOINTS

@app.route('/')
def index():
    """Strona główna"""
    return render_template('index.html')

@app.route('/api/file/<int:file_id>')
def get_file(file_id):
    """Pobierz plik PDF"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        file_data = db.fetch_one("SELECT filepath FROM source_files WHERE id = ?", (file_id,))
        db.disconnect()

        if not file_data:
            return jsonify({'error': 'Plik nie znaleziony'}), 404

        filepath = file_data['filepath']
        return send_file(filepath, mimetype='application/pdf')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch-import', methods=['POST'])
def batch_import():
    """Batch import PDFów z pełnym auto-process pipeline"""
    try:
        imports_dir = Path(CONFIG['imports_dir'])
        pdf_files = list(imports_dir.glob('*.pdf'))

        if not pdf_files:
            return jsonify({'error': 'Brak plików PDF w folderze imports'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        total = {
            'files_imported': 0,
            'pages_processed': 0,
            'kw_found': 0,
            'persons_found': 0,
            'companies_found': 0,
            'institutions_found': 0,
            'nips_found': 0,
            'regons_found': 0,
            'krs_found': 0,
            'pesels_found': 0,
            'phones_found': 0,
            'emails_found': 0,
            'signatures_found': 0,
            'tags_added': 0,
            'cooccurrences_built': 0
        }

        for pdf_path in pdf_files:
            result = auto_process_pdf(pdf_path, pdf_path.stem, db=db)
            if result and result.get('success'):
                total['files_imported'] += 1
                for key, value in result['stats'].items():
                    if key in total:
                        total[key] += value

        db.disconnect()

        return jsonify({
            'success': True,
            **total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def auto_process_pdf(filepath, binder_name='Default', db=None):
    """
    Pełny auto-process pipeline dla PDF:
    1. OCR / odczyt tekstu
    2. Dodanie do bazy
    3. Ekstrakcja KW
    4. Ekstrakcja encji (osoby, firmy, NIP, REGON, KRS, PESEL, tel, email)
    5. Auto-tagowanie dokumentu
    6. Budowa cooccurrences dla tego pliku
    """
    reader = PDFReader()
    kw_extractor = KWExtractor()
    entity_extractor = EntityExtractor()
    tagger = DocumentTagger()

    own_db = False
    if db is None:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()
        own_db = True

    stats = {
        'pages_processed': 0,
        'kw_found': 0,
        'persons_found': 0,
        'companies_found': 0,
        'institutions_found': 0,
        'nips_found': 0,
        'regons_found': 0,
        'krs_found': 0,
        'pesels_found': 0,
        'phones_found': 0,
        'emails_found': 0,
        'signatures_found': 0,
        'tags_added': 0,
        'cooccurrences_built': 0
    }

    # Krok 1: Odczyt PDF z OCR
    pdf_data = reader.read_pdf(str(filepath))
    if not pdf_data:
        if own_db:
            db.disconnect()
        return None

    # Krok 2: Dodanie do bazy
    binder_id = db.add_binder(binder_name)
    file_id = db.add_source_file(
        binder_id,
        pdf_data['filename'],
        pdf_data['filepath'],
        pdf_data['file_hash'],
        pdf_data['page_count']
    )

    page_ids = []
    page_texts = []

    # Krok 3-4: Przetwarzanie stron - KW + Encje
    for page_data in pdf_data['pages']:
        page_num = page_data['page_number']
        text = page_data['text']

        page_id = db.add_page(file_id, page_num, text)
        page_ids.append(page_id)
        page_texts.append(text)
        stats['pages_processed'] += 1

        if not text or len(text) < 10:
            continue

        # KW extraction
        kws = kw_extractor.extract_from_text(text, page_num)
        for kw in kws:
            kw_id = db.add_land_register(
                kw['kw_full'],
                kw['kw_district'],
                kw['kw_number'],
                kw['kw_checksum']
            )
            db.add_land_register_occurrence(
                kw_id, page_id, file_id,
                kw['context_before'], kw['context_after']
            )
            stats['kw_found'] += 1

        # Entity extraction
        entities = entity_extractor.extract_all(text)

        # Persons
        for person in entities.get('persons', []):
            db.execute("""
                INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                VALUES (?, ?, ?)
            """, ('person', person['full_name'], person['full_name'].upper()))
            entity_row = db.fetch_one(
                "SELECT id FROM entities WHERE entity_type='person' AND entity_value=?",
                (person['full_name'],)
            )
            if entity_row:
                db.execute("""
                    INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                    VALUES (?, ?, ?)
                """, (entity_row['id'], page_id, file_id))
                stats['persons_found'] += 1

        # Companies
        for company in entities.get('companies', []):
            db.execute("""
                INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                VALUES (?, ?, ?)
            """, ('company', company['name'], company['name'].upper()))
            entity_row = db.fetch_one(
                "SELECT id FROM entities WHERE entity_type='company' AND entity_value=?",
                (company['name'],)
            )
            if entity_row:
                db.execute("""
                    INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                    VALUES (?, ?, ?)
                """, (entity_row['id'], page_id, file_id))
                stats['companies_found'] += 1

        # Institutions
        for inst in entities.get('institutions', []):
            db.execute("""
                INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                VALUES (?, ?, ?)
            """, ('institution', inst['name'], inst['name'].upper()))
            entity_row = db.fetch_one(
                "SELECT id FROM entities WHERE entity_type='institution' AND entity_value=?",
                (inst['name'],)
            )
            if entity_row:
                db.execute("""
                    INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                    VALUES (?, ?, ?)
                """, (entity_row['id'], page_id, file_id))
                stats['institutions_found'] += 1

        # NIPs
        for nip in entities.get('nips', []):
            db.execute("""
                INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                VALUES (?, ?, ?)
            """, ('nip', nip['formatted'], nip['nip']))
            entity_row = db.fetch_one(
                "SELECT id FROM entities WHERE entity_type='nip' AND entity_value=?",
                (nip['formatted'],)
            )
            if entity_row:
                db.execute("""
                    INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                    VALUES (?, ?, ?)
                """, (entity_row['id'], page_id, file_id))
                stats['nips_found'] += 1

        # REGONs, KRSs, PESELs, Phones, Emails, Signatures
        for ent_type, ent_list, key in [
            ('regon', entities.get('regons', []), 'regon'),
            ('krs', entities.get('krs', []), 'krs'),
            ('pesel', entities.get('pesels', []), 'pesel'),
            ('phone', entities.get('phones', []), 'phone'),
            ('email', entities.get('emails', []), 'email'),
        ]:
            for item in ent_list:
                value = item.get(key, '')
                if not value:
                    continue
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, (ent_type, value, value))
                entity_row = db.fetch_one(
                    f"SELECT id FROM entities WHERE entity_type='{ent_type}' AND entity_value=?",
                    (value,)
                )
                if entity_row:
                    db.execute("""
                        INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                        VALUES (?, ?, ?)
                    """, (entity_row['id'], page_id, file_id))
                    stats[f'{ent_type}s_found'] += 1

        # Signatures
        for sig in entities.get('signatures', []):
            value = sig.get('value', '')
            if not value:
                continue
            db.execute("""
                INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                VALUES (?, ?, ?)
            """, ('signature', value, value.upper()))
            entity_row = db.fetch_one(
                "SELECT id FROM entities WHERE entity_type='signature' AND entity_value=?",
                (value,)
            )
            if entity_row:
                db.execute("""
                    INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                    VALUES (?, ?, ?)
                """, (entity_row['id'], page_id, file_id))
                stats['signatures_found'] += 1

    # Krok 5: Auto-tagowanie dokumentu
    valid_texts = [t for t in page_texts if t and len(t) > 10]
    if valid_texts:
        tags = tagger.tag_pages_combined(valid_texts)
        db.execute("DELETE FROM document_tags WHERE file_id = ?", (file_id,))
        for tag in tags[:3]:
            db.execute("""
                INSERT OR IGNORE INTO document_tags (file_id, tag, confidence)
                VALUES (?, ?, ?)
            """, (file_id, tag['type'], tag['confidence']))
            stats['tags_added'] += 1

    # Krok 6: Build cooccurrences dla stron tego pliku
    for page_id in page_ids:
        entity_ids_row = db.fetch_one("""
            SELECT GROUP_CONCAT(entity_id) as entity_ids
            FROM entity_occurrences
            WHERE page_id = ?
            GROUP BY page_id
            HAVING COUNT(*) > 1
        """, (page_id,))

        if entity_ids_row and entity_ids_row['entity_ids']:
            entity_ids = [int(x) for x in entity_ids_row['entity_ids'].split(',')]
            for i in range(len(entity_ids)):
                for j in range(i+1, len(entity_ids)):
                    e1, e2 = sorted([entity_ids[i], entity_ids[j]])
                    db.execute("""
                        INSERT OR IGNORE INTO cooccurrences (entity_id_1, entity_id_2, page_id)
                        VALUES (?, ?, ?)
                    """, (e1, e2, page_id))
                    stats['cooccurrences_built'] += 1

    if own_db:
        db.disconnect()

    return {
        'success': True,
        'file_id': file_id,
        'filename': pdf_data['filename'],
        'pages': pdf_data['page_count'],
        'stats': stats
    }


@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """Upload i pełen auto-process pipeline"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Brak pliku'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Plik nie wybrany'}), 400

        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Tylko pliki PDF'}), 400

        imports_dir = Path(CONFIG['imports_dir'])
        imports_dir.mkdir(parents=True, exist_ok=True)
        filepath = imports_dir / file.filename
        file.save(str(filepath))

        binder_name = request.form.get('binder_name', 'Default')

        # Pełen auto-process pipeline
        result = auto_process_pdf(filepath, binder_name)

        if not result:
            return jsonify({'error': 'Błąd odczytywania PDF'}), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/land-registers', methods=['GET'])
def get_land_registers():
    """Pobierz wszystkie Księgi Wieczyste"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        kws = db.get_all_land_registers()
        db.disconnect()

        result = []
        for kw in kws:
            result.append({
                'id': kw['id'],
                'kw_full': kw['kw_full'],
                'district': kw['kw_district'],
                'address': kw['property_address'] or '—',
                'owner': kw['owner_manual'] or '—',
                'files': kw['files_count'],
                'pages': kw['pages_count']
            })

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Pobierz statystyki"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        stats = db.get_statistics()
        db.disconnect()

        return jsonify({'success': True, 'data': stats})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Szukaj KW"""
    try:
        query = request.json.get('query', '').strip().upper()

        if not query:
            return jsonify({'error': 'Wpisz szukaną frazę'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Szukaj KW
        kws = db.fetch_all(
            "SELECT * FROM land_registers WHERE kw_full LIKE ?",
            (f"%{query}%",)
        )

        results = []
        for kw in kws:
            results.append({
                'kw_full': kw['kw_full'],
                'district': kw['kw_district'],
                'address': kw['property_address'] or '—',
                'owner': kw['owner_manual'] or '—'
            })

        db.disconnect()

        return jsonify({'success': True, 'data': results, 'count': len(results)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-owner', methods=['POST'])
def update_owner():
    """Zaktualizuj właściciela KW"""
    try:
        kw_id = request.json.get('kw_id')
        owner = request.json.get('owner', '')

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        db.execute(
            "UPDATE land_registers SET owner_manual = ? WHERE id = ?",
            (owner, kw_id)
        )

        db.disconnect()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-tag-documents', methods=['POST'])
def auto_tag_documents():
    """Auto-tagowanie wszystkich dokumentów"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        tagger = DocumentTagger()

        # Pobierz wszystkie pliki
        files = db.fetch_all("SELECT id, filename FROM source_files")
        total_tagged = 0
        tags_count = {}

        for file in files:
            # Pobierz wszystkie strony pliku
            pages = db.fetch_all(
                "SELECT text_content FROM pages WHERE file_id = ? AND LENGTH(text_content) > 10",
                (file['id'],)
            )

            if not pages:
                continue

            texts = [p['text_content'] for p in pages]
            tags = tagger.tag_pages_combined(texts)

            # Usuń stare tagi
            db.execute("DELETE FROM document_tags WHERE file_id = ?", (file['id'],))

            # Zapisz nowe tagi (top 3)
            for tag in tags[:3]:
                db.execute("""
                    INSERT OR IGNORE INTO document_tags (file_id, tag, confidence)
                    VALUES (?, ?, ?)
                """, (file['id'], tag['type'], tag['confidence']))

                tags_count[tag['type']] = tags_count.get(tag['type'], 0) + 1
                total_tagged += 1

        db.disconnect()

        return jsonify({
            'success': True,
            'files_processed': len(files),
            'tags_added': total_tagged,
            'tags_distribution': tags_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document-tags', methods=['GET'])
def get_document_tags():
    """Pobierz tagi dokumentów"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        result = db.fetch_all("""
            SELECT
                f.id, f.filename,
                GROUP_CONCAT(dt.tag, ', ') as tags,
                MAX(dt.confidence) as max_confidence
            FROM source_files f
            LEFT JOIN document_tags dt ON f.id = dt.file_id
            GROUP BY f.id
            ORDER BY max_confidence DESC NULLS LAST
        """)

        db.disconnect()

        return jsonify({
            'success': True,
            'data': [{
                'file_id': r['id'],
                'filename': r['filename'],
                'tags': r['tags'] or 'brak',
                'confidence': r['max_confidence'] or 0
            } for r in result]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-search-report', methods=['POST'])
def generate_search_report():
    """Generuj raport z wyników wyszukiwania"""
    try:
        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Wpisz szukaną frazę'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Szukaj stron z wynikami
        results = db.fetch_all("""
            SELECT DISTINCT
                f.id, f.filename, b.name as binder, f.page_count,
                COUNT(DISTINCT p.id) as matching_pages,
                GROUP_CONCAT(DISTINCT dt.tag, ', ') as tags
            FROM pages p
            LEFT JOIN source_files f ON p.file_id = f.id
            LEFT JOIN binders b ON f.binder_id = b.id
            LEFT JOIN document_tags dt ON f.id = dt.file_id
            WHERE p.text_content LIKE ?
            GROUP BY f.id
            ORDER BY matching_pages DESC
        """, (f"%{query}%",))

        # Szukaj encji w wynikach
        entities_found = db.fetch_all("""
            SELECT DISTINCT e.entity_type, COUNT(*) as count
            FROM pages p
            LEFT JOIN entity_occurrences eo ON p.id = eo.page_id
            LEFT JOIN entities e ON eo.entity_id = e.id
            WHERE p.text_content LIKE ? AND e.id IS NOT NULL
            GROUP BY e.entity_type
            ORDER BY count DESC
        """, (f"%{query}%",))

        # Szukaj KW w wynikach
        kw_found = db.fetch_all("""
            SELECT DISTINCT lr.kw_full, COUNT(*) as occurrences
            FROM pages p
            LEFT JOIN land_register_occurrences lro ON p.id = lro.page_id
            LEFT JOIN land_registers lr ON lro.kw_id = lr.id
            WHERE p.text_content LIKE ? AND lr.id IS NOT NULL
            GROUP BY lr.id
            ORDER BY occurrences DESC
            LIMIT 20
        """, (f"%{query}%",))

        db.disconnect()

        # Tworzenie raportu w Excel
        wb = openpyxl.Workbook()

        # Sheet 1: Podsumowanie
        ws = wb.active
        ws.title = "Podsumowanie"
        ws['A1'] = "Raport z Wyszukiwania"
        ws['A1'].font = openpyxl.styles.Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = openpyxl.styles.PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        ws.merge_cells('A1:D1')

        ws['A3'] = "Fraza wyszukiwania:"
        ws['B3'] = query
        ws['A4'] = "Dokumenty znalezione:"
        ws['B4'] = len(results)
        ws['A5'] = "Encje znalezione:"
        ws['B5'] = sum([r['count'] for r in entities_found])
        ws['A6'] = "Księgi Wieczyste znalezione:"
        ws['B6'] = len(kw_found)
        ws['A7'] = "Data raportu:"
        ws['B7'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Sheet 2: Dokumenty
        ws2 = wb.create_sheet("Dokumenty")
        ws2.append(['Plik', 'Segregator', 'Strony', 'Dopasowane', 'Tagi'])
        for r in results:
            ws2.append([r['filename'], r['binder'] or '', r['page_count'], r['matching_pages'], r['tags'] or ''])

        # Sheet 3: Encje
        ws3 = wb.create_sheet("Encje")
        ws3.append(['Typ encji', 'Liczba znalezionych'])
        for e in entities_found:
            ws3.append([e['entity_type'], e['count']])

        # Sheet 4: Księgi Wieczyste
        ws4 = wb.create_sheet("Księgi Wieczyste")
        ws4.append(['KW', 'Wystąpienia'])
        for kw in kw_found:
            ws4.append([kw['kw_full'], kw['occurrences']])

        # Styling
        for ws in wb.worksheets:
            for cell in ws[1]:
                cell.fill = openpyxl.styles.PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")

        exports_dir = Path(CONFIG['exports_dir'])
        exports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"Raport_Szukania_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = exports_dir / filename

        wb.save(str(filepath))

        return send_file(str(filepath), as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/smart-search', methods=['POST'])
def smart_search():
    """
    Smart Search z rankingiem - implementuje priorytety ze specyfikacji:
    1. Wszystkie frazy na jednej stronie (najwyższa)
    2. Wszystkie frazy w jednym dokumencie
    3. Częściowe dopasowania
    """
    try:
        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Wpisz szukaną frazę'}), 400

        # Rozdziel frazy
        phrases = [p.strip() for p in query.split() if p.strip()]

        if not phrases:
            return jsonify({'error': 'Brak fraz'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Szukaj stron które zawierają WSZYSTKIE frazy (priorytet 1)
        results_priority_1 = []
        results_priority_2 = []
        results_priority_3 = []

        # Pobierz wszystkie strony i sprawdź
        pages = db.fetch_all("""
            SELECT p.id, p.page_number, p.text_content, p.file_id,
                   f.filename, b.name as binder_name
            FROM pages p
            LEFT JOIN source_files f ON p.file_id = f.id
            LEFT JOIN binders b ON f.binder_id = b.id
            WHERE LENGTH(p.text_content) > 10
        """)

        # Grupowanie po plikach
        files_with_phrases = {}

        for page in pages:
            text = page['text_content'].upper() if page['text_content'] else ''

            # Sprawdź ile fraz znaleziono na stronie
            found_phrases = [p for p in phrases if p.upper() in text]

            if len(found_phrases) == len(phrases):
                # Priorytet 1 - wszystkie na jednej stronie
                # Wyciągnij kontekst z pierwszego pasującego
                idx = text.find(phrases[0].upper())
                start = max(0, idx - 50)
                end = min(len(page['text_content']), idx + 100)
                context = page['text_content'][start:end]

                results_priority_1.append({
                    'priority': 1,
                    'score': 100,
                    'filename': page['filename'],
                    'binder': page['binder_name'] or '',
                    'page': page['page_number'],
                    'context': context,
                    'phrases_found': found_phrases,
                    'why': 'Wszystkie frazy na tej stronie'
                })
            elif len(found_phrases) > 0:
                # Częściowe dopasowanie
                file_key = page['file_id']
                if file_key not in files_with_phrases:
                    files_with_phrases[file_key] = {
                        'filename': page['filename'],
                        'binder': page['binder_name'] or '',
                        'phrases': set(),
                        'pages': []
                    }
                files_with_phrases[file_key]['phrases'].update(found_phrases)
                files_with_phrases[file_key]['pages'].append({
                    'page': page['page_number'],
                    'phrases': found_phrases,
                    'page_id': page['id']
                })

        # Priorytet 2 - wszystkie frazy w jednym dokumencie
        for file_id, data in files_with_phrases.items():
            if len(data['phrases']) == len(phrases):
                # Wszystkie frazy są w tym dokumencie
                results_priority_2.append({
                    'priority': 2,
                    'score': 70,
                    'filename': data['filename'],
                    'binder': data['binder'],
                    'pages': [p['page'] for p in data['pages']],
                    'phrases_found': list(data['phrases']),
                    'why': f'Wszystkie frazy w jednym dokumencie ({len(data["pages"])} stron)'
                })

        # Priorytet 3 - częściowe dopasowanie
        for file_id, data in files_with_phrases.items():
            if 0 < len(data['phrases']) < len(phrases):
                results_priority_3.append({
                    'priority': 3,
                    'score': 30,
                    'filename': data['filename'],
                    'binder': data['binder'],
                    'pages': [p['page'] for p in data['pages'][:5]],
                    'phrases_found': list(data['phrases']),
                    'why': f'Częściowe dopasowanie ({len(data["phrases"])}/{len(phrases)} fraz)'
                })

        db.disconnect()

        # Połącz wyniki w jednej liście (limit 50)
        all_results = (
            results_priority_1[:20] +
            results_priority_2[:15] +
            results_priority_3[:15]
        )

        return jsonify({
            'success': True,
            'query': query,
            'phrases': phrases,
            'data': all_results,
            'count': len(all_results),
            'priority_1_count': len(results_priority_1),
            'priority_2_count': len(results_priority_2),
            'priority_3_count': len(results_priority_3)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/build-cooccurrences', methods=['POST'])
def build_cooccurrences():
    """Buduj indeks współwystąpień encji"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Wyczyść stare
        db.execute("DELETE FROM cooccurrences")

        # Pobierz strony z wieloma encjami
        pages_with_entities = db.fetch_all("""
            SELECT page_id, GROUP_CONCAT(entity_id) as entity_ids
            FROM entity_occurrences
            GROUP BY page_id
            HAVING COUNT(*) > 1
        """)

        cooccurrence_count = 0

        for page_data in pages_with_entities:
            page_id = page_data['page_id']
            entity_ids = [int(x) for x in page_data['entity_ids'].split(',')]

            # Wszystkie pary encji
            for i in range(len(entity_ids)):
                for j in range(i+1, len(entity_ids)):
                    e1, e2 = sorted([entity_ids[i], entity_ids[j]])
                    db.execute("""
                        INSERT OR IGNORE INTO cooccurrences (entity_id_1, entity_id_2, page_id)
                        VALUES (?, ?, ?)
                    """, (e1, e2, page_id))
                    cooccurrence_count += 1

        db.disconnect()

        return jsonify({
            'success': True,
            'cooccurrences_built': cooccurrence_count,
            'pages_analyzed': len(pages_with_entities)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/find-related', methods=['POST'])
def find_related():
    """Znajdź encje powiązane z daną encją"""
    try:
        entity_value = request.json.get('entity_value', '').strip()

        if not entity_value:
            return jsonify({'error': 'Podaj wartość'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Znajdź encję
        entity = db.fetch_one("""
            SELECT id, entity_type FROM entities
            WHERE entity_value LIKE ? LIMIT 1
        """, (f"%{entity_value}%",))

        if not entity:
            db.disconnect()
            return jsonify({'success': True, 'data': [], 'count': 0})

        # Znajdź powiązane
        related = db.fetch_all("""
            SELECT e.entity_value, e.entity_type, COUNT(*) as cnt
            FROM cooccurrences c
            JOIN entities e ON (e.id = c.entity_id_1 OR e.id = c.entity_id_2)
            WHERE (c.entity_id_1 = ? OR c.entity_id_2 = ?) AND e.id != ?
            GROUP BY e.id
            ORDER BY cnt DESC
            LIMIT 50
        """, (entity['id'], entity['id'], entity['id']))

        db.disconnect()

        return jsonify({
            'success': True,
            'entity': entity_value,
            'data': [{
                'value': r['entity_value'],
                'type': r['entity_type'],
                'cooccurrences': r['cnt']
            } for r in related],
            'count': len(related)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entity-relations/<entity_type>/<entity_value>', methods=['GET'])
def get_entity_relations(entity_type, entity_value):
    """Pobierz szczegółowe relacje encji z metadata"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Znajdź encję
        entity = db.fetch_one("""
            SELECT id, entity_value, entity_type FROM entities
            WHERE entity_type = ? AND entity_value LIKE ? LIMIT 1
        """, (entity_type, f"%{entity_value}%"))

        if not entity:
            db.disconnect()
            return jsonify({'success': True, 'entity': None, 'data': [], 'count': 0})

        # Znajdź powiązane z metadata
        related = db.fetch_all("""
            SELECT
                e.id,
                e.entity_value,
                e.entity_type,
                COUNT(*) as strength,
                COUNT(DISTINCT p.id) as pages_count,
                COUNT(DISTINCT p.file_id) as files_count,
                GROUP_CONCAT(DISTINCT p.page_number) as pages
            FROM cooccurrences c
            JOIN entities e ON (e.id = c.entity_id_1 OR e.id = c.entity_id_2)
            LEFT JOIN pages p ON p.id = c.page_id
            WHERE (c.entity_id_1 = ? OR c.entity_id_2 = ?) AND e.id != ?
            GROUP BY e.id
            ORDER BY strength DESC
            LIMIT 100
        """, (entity['id'], entity['id'], entity['id']))

        db.disconnect()

        result = [{
            'id': r['id'],
            'value': r['entity_value'],
            'type': r['entity_type'],
            'strength': r['strength'],
            'pages': r['pages_count'],
            'files': r['files_count'],
            'page_numbers': r['pages'].split(',') if r['pages'] else []
        } for r in related]

        return jsonify({
            'success': True,
            'entity': {
                'value': entity['entity_value'],
                'type': entity['entity_type']
            },
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-entities', methods=['POST'])
def extract_entities():
    """Rozpoznaj encje we wszystkich dokumentach"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        extractor = EntityExtractor()

        # Pobierz wszystkie strony z tekstem
        pages = db.fetch_all("""
            SELECT id, file_id, page_number, text_content
            FROM pages
            WHERE LENGTH(text_content) > 10
        """)

        total_entities = {
            'persons': 0, 'companies': 0, 'institutions': 0,
            'nips': 0, 'regons': 0, 'krs': 0, 'pesels': 0,
            'phones': 0, 'emails': 0, 'dates': 0,
            'signatures': 0, 'postal_codes': 0, 'amounts': 0
        }

        for page in pages:
            text = page['text_content']
            if not text:
                continue

            entities = extractor.extract_all(text)

            # Zapisz osoby
            for person in entities['persons']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('person', person['full_name'], person['full_name'].upper()))

                entity_row = db.fetch_one("SELECT id FROM entities WHERE entity_type='person' AND entity_value=?", (person['full_name'],))
                if entity_row:
                    db.execute("""
                        INSERT INTO entity_occurrences (entity_id, page_id, file_id)
                        VALUES (?, ?, ?)
                    """, (entity_row['id'], page['id'], page['file_id']))
                    total_entities['persons'] += 1

            # Zapisz firmy
            for company in entities['companies']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('company', company['name'], company['name'].upper()))
                total_entities['companies'] += 1

            # Zapisz instytucje
            for inst in entities['institutions']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('institution', inst['name'], inst['name'].upper()))
                total_entities['institutions'] += 1

            # NIP
            for nip in entities['nips']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('nip', nip['formatted'], nip['nip']))
                total_entities['nips'] += 1

            # REGON
            for regon in entities['regons']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('regon', regon['regon'], regon['regon']))
                total_entities['regons'] += 1

            # KRS
            for krs in entities['krs']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('krs', krs['krs'], krs['krs']))
                total_entities['krs'] += 1

            # PESEL
            for pesel in entities['pesels']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('pesel', pesel['pesel'], pesel['pesel']))
                total_entities['pesels'] += 1

            # Phones
            for phone in entities['phones']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('phone', phone['phone'], phone['phone']))
                total_entities['phones'] += 1

            # Emails
            for email in entities['emails']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('email', email['email'], email['email']))
                total_entities['emails'] += 1

            # Signatures
            for sig in entities['signatures']:
                db.execute("""
                    INSERT OR IGNORE INTO entities (entity_type, entity_value, normalized_value)
                    VALUES (?, ?, ?)
                """, ('signature', sig['value'], sig['value'].upper()))
                total_entities['signatures'] += 1

        db.disconnect()

        return jsonify({
            'success': True,
            'data': total_entities,
            'pages_processed': len(pages)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entities/<entity_type>', methods=['GET'])
def get_entities(entity_type):
    """Pobierz encje danego typu"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        entities = db.fetch_all("""
            SELECT
                e.id,
                e.entity_value,
                COUNT(DISTINCT eo.page_id) as occurrences,
                COUNT(DISTINCT eo.file_id) as files_count
            FROM entities e
            LEFT JOIN entity_occurrences eo ON e.id = eo.entity_id
            WHERE e.entity_type = ?
            GROUP BY e.id
            ORDER BY occurrences DESC, e.entity_value
            LIMIT 500
        """, (entity_type,))

        db.disconnect()

        result = [{
            'id': e['id'],
            'value': e['entity_value'],
            'occurrences': e['occurrences'] or 0,
            'files': e['files_count'] or 0
        } for e in entities]

        return jsonify({'success': True, 'data': result, 'count': len(result)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entity-stats', methods=['GET'])
def get_entity_stats():
    """Statystyki encji"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        stats = db.fetch_all("""
            SELECT entity_type, COUNT(*) as count
            FROM entities
            GROUP BY entity_type
            ORDER BY count DESC
        """)

        db.disconnect()

        result = {row['entity_type']: row['count'] for row in stats}
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-dictionary', methods=['GET'])
def get_user_dictionary():
    """Pobierz słownik użytkownika"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        words = db.fetch_all("SELECT id, original, replacement FROM user_dictionaries ORDER BY original")
        db.disconnect()

        result = [{'id': w['id'], 'original': w['original'], 'replacement': w['replacement']} for w in words]

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-dictionary-word', methods=['POST'])
def add_dictionary_word():
    """Dodaj słowo do słownika"""
    try:
        original = request.json.get('original', '').strip()
        replacement = request.json.get('replacement', '').strip()

        if not original or not replacement:
            return jsonify({'error': 'Wypełnij oba pola'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        db.execute(
            "INSERT OR IGNORE INTO user_dictionaries (original, replacement) VALUES (?, ?)",
            (original, replacement)
        )

        db.disconnect()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-dictionary-word', methods=['POST'])
def delete_dictionary_word():
    """Usuń słowo ze słownika"""
    try:
        word_id = request.json.get('word_id')

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        db.execute("DELETE FROM user_dictionaries WHERE id = ?", (word_id,))

        db.disconnect()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report-kw', methods=['GET'])
def report_kw():
    """Raport Ksiąg Wieczystych"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        kws = db.fetch_all("""
            SELECT
                lr.kw_full,
                lr.kw_district,
                lr.property_address,
                lr.owner_manual,
                COUNT(DISTINCT lro.file_id) as files_count,
                COUNT(DISTINCT lro.page_id) as pages_count
            FROM land_registers lr
            LEFT JOIN land_register_occurrences lro ON lr.id = lro.kw_id
            GROUP BY lr.id
            ORDER BY lr.kw_district, lr.kw_number
        """)

        db.disconnect()

        result = []
        for kw in kws:
            result.append({
                'kw': kw['kw_full'],
                'district': kw['kw_district'],
                'address': kw['property_address'] or '—',
                'owner': kw['owner_manual'] or '—',
                'files': kw['files_count'],
                'pages': kw['pages_count']
            })

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report-coverage', methods=['GET'])
def report_coverage():
    """Raport Coverage - ile stron przeskanowano"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        total_pages = db.fetch_one("SELECT COUNT(*) as count FROM pages")['count']
        indexed_pages = db.fetch_one("SELECT COUNT(*) as count FROM pages WHERE LENGTH(text_content) > 50")['count']
        total_files = db.fetch_one("SELECT COUNT(*) as count FROM source_files")['count']
        total_kw = db.fetch_one("SELECT COUNT(*) as count FROM land_registers")['count']

        db.disconnect()

        coverage = round((indexed_pages / total_pages * 100), 2) if total_pages > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'total_pages': total_pages,
                'indexed_pages': indexed_pages,
                'coverage_percent': coverage,
                'total_files': total_files,
                'total_kw': total_kw
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-excel', methods=['GET'])
def export_excel():
    """Eksportuj do Excel"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        kws = db.get_all_land_registers()
        db.disconnect()

        # Utwórz workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Księgi Wieczyste"

        # Nagłówki
        headers = ['Lp.', 'Księga Wieczysta', 'Okręg', 'Adres', 'Właściciel', 'W plikach', 'Na stronach']
        ws.append(headers)

        # Style
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Dane
        for idx, kw in enumerate(kws, 1):
            ws.append([
                idx,
                kw['kw_full'],
                kw['kw_district'],
                kw['property_address'] or '—',
                kw['owner_manual'] or '—',
                kw['files_count'],
                kw['pages_count']
            ])

        # Szerokość kolumn
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 30
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 12

        # Zapisz
        exports_dir = Path(CONFIG['exports_dir'])
        exports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"Ksiegi_Wieczyste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = exports_dir / filename

        wb.save(str(filepath))

        return send_file(str(filepath), as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-kw', methods=['POST'])
def delete_kw():
    """Usuń KW z bazy"""
    try:
        kw_id = request.json.get('kw_id')

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        db.execute("DELETE FROM land_register_occurrences WHERE kw_id = ?", (kw_id,))
        db.execute("DELETE FROM land_registers WHERE id = ?", (kw_id,))

        db.disconnect()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    """Pobierz listę wszystkich plików PDF"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        files = db.fetch_all("""
            SELECT
                f.id,
                f.filename,
                f.page_count,
                b.name as binder_name,
                COUNT(DISTINCT p.id) as pages_in_db
            FROM source_files f
            LEFT JOIN binders b ON f.binder_id = b.id
            LEFT JOIN pages p ON f.id = p.file_id
            GROUP BY f.id
            ORDER BY f.id DESC
        """)

        result = []
        for file in files:
            result.append({
                'id': file['id'],
                'filename': file['filename'],
                'pages': file['page_count'],
                'binder': file['binder_name'] or 'Unknown',
                'pages_indexed': file['pages_in_db']
            })

        db.disconnect()
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-all', methods=['POST'])
def search_all():
    """Szukaj we wszystkich dokumentach"""
    try:
        query = request.json.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Wpisz szukaną frazę'}), 400

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Szukaj w tekście stron
        results = db.fetch_all("""
            SELECT
                p.id as page_id,
                p.page_number,
                f.filename,
                b.name as binder_name,
                p.text_content,
                f.id as file_id
            FROM pages p
            LEFT JOIN source_files f ON p.file_id = f.id
            LEFT JOIN binders b ON f.binder_id = b.id
            WHERE p.text_content LIKE ?
            ORDER BY f.id, p.page_number
            LIMIT 100
        """, (f"%{query}%",))

        result_list = []
        for row in results:
            # Wyciągnij kontekst (50 znaków przed i po)
            text = row['text_content'] or ''
            idx = text.upper().find(query.upper())
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(text), idx + len(query) + 50)
                context = text[start:end]
            else:
                context = text[:100]

            result_list.append({
                'file_id': row['file_id'],
                'page_id': row['page_id'],
                'filename': row['filename'],
                'page': row['page_number'],
                'binder': row['binder_name'] or 'Unknown',
                'context': context.strip()
            })

        db.disconnect()

        return jsonify({
            'success': True,
            'data': result_list,
            'count': len(result_list)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rescan-ocr', methods=['POST'])
def rescan_ocr():
    """Pełny rescan OCR wszystkich dokumentów"""
    try:
        from modules import PDFReader, KWExtractor

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Pobierz wszystkie pliki
        files = db.fetch_all("SELECT id, filepath FROM source_files")

        if not files:
            db.disconnect()
            return jsonify({'error': 'Brak plików do skanowania'}), 400

        reader = PDFReader()
        extractor = KWExtractor()

        total_pages = 0
        total_kw = 0

        for file in files:
            file_id = file['id']
            filepath = file['filepath']

            # Czytaj PDF z OCR
            pdf_data = reader.read_pdf(filepath)
            if not pdf_data:
                continue

            # Usuń stare strony
            db.execute("DELETE FROM pages WHERE file_id = ?", (file_id,))

            # Dodaj nowe strony z OCR
            kw_found = 0
            for page_data in pdf_data['pages']:
                page_num = page_data['page_number']
                text = page_data['text']

                page_id = db.add_page(file_id, page_num, text)
                total_pages += 1

                # Ekstrahuj KW
                kws = extractor.extract_from_text(text, page_num)
                for kw in kws:
                    kw_full = kw['kw_full']
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
                    kw_found += 1
                    total_kw += 1

        db.disconnect()

        return jsonify({
            'success': True,
            'pages_scanned': total_pages,
            'kw_found': total_kw,
            'files': len(files)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/page-by-file-page/<int:file_id>/<int:page_number>', methods=['GET'])
def get_page_by_file_page(file_id, page_number):
    """Pobierz page_id + tekst po file_id i page_number"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        page = db.fetch_one(
            "SELECT id, page_number, text_content FROM pages WHERE file_id = ? AND page_number = ?",
            (file_id, page_number)
        )
        db.disconnect()

        if not page:
            return jsonify({'success': False, 'error': 'Strona nie znaleziona'}), 404

        return jsonify({
            'success': True,
            'page_id': page['id'],
            'page_number': page['page_number'],
            'text': page['text_content'] or ''
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/page-text/<int:page_id>', methods=['GET'])
def get_page_text(page_id):
    """Pobierz tekst strony"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        page = db.fetch_one("SELECT id, page_number, text_content FROM pages WHERE id = ?", (page_id,))
        db.disconnect()

        if not page:
            return jsonify({'error': 'Strona nie znaleziona'}), 404

        return jsonify({
            'success': True,
            'page_id': page['id'],
            'page_number': page['page_number'],
            'text': page['text_content']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/correct-page-text', methods=['POST'])
def correct_page_text():
    """Zapisz poprawioną wersję tekstu strony"""
    try:
        page_id = request.json.get('page_id')
        corrected_text = request.json.get('text', '')

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Aktualizuj tekst strony
        db.execute(
            "UPDATE pages SET text_content = ? WHERE id = ?",
            (corrected_text, page_id)
        )

        # Dodaj zapis do historii
        db.execute(
            "INSERT INTO ocr_corrections (page_id, original_text, corrected_text) VALUES (?, ?, ?)",
            (page_id, "", corrected_text)
        )

        db.disconnect()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-kw', methods=['POST'])
def add_kw():
    """Dodaj KW ręcznie"""
    try:
        kw_full = request.json.get('kw_full', '').upper().strip()
        address = request.json.get('address', '').strip()
        owner = request.json.get('owner', '').strip()

        if not kw_full:
            return jsonify({'error': 'Podaj numer KW'}), 400

        # Validacja formatu KW
        import re
        kw_pattern = r'([A-Z]{2}\d{1,2}[A-Z]{1,2})[/\s\-]?(\d{8})[/\s\-]?(\d)'
        match = re.match(kw_pattern, kw_full.replace(' ', '').replace('-', '/'))

        if not match:
            return jsonify({'error': 'Nieprawidłowy format KW (np. SZ1S/00012345/6)'}), 400

        kw_district = match.group(1)
        kw_number = match.group(2)
        kw_checksum = match.group(3)
        kw_full = f"{kw_district}/{kw_number}/{kw_checksum}"

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        # Dodaj KW
        db.execute("""
            INSERT OR IGNORE INTO land_registers
            (kw_full, kw_district, kw_number, kw_checksum, property_address, owner_manual)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (kw_full, kw_district, kw_number, kw_checksum, address, owner))

        db.disconnect()

        return jsonify({'success': True, 'kw_full': kw_full})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup', methods=['POST'])
def backup_database():
    """Tworzenie backupu bazy danych"""
    try:
        import shutil
        from datetime import datetime

        backup_dir = Path(CONFIG['exports_dir']) / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"backup_{timestamp}.db"

        shutil.copy2(CONFIG['db_path'], str(backup_path))

        return jsonify({
            'success': True,
            'backup_file': str(backup_path),
            'size_mb': round(backup_path.stat().st_size / 1024 / 1024, 2)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced-export', methods=['POST'])
def advanced_export():
    """Zaawansowany eksport z filtrami"""
    try:
        request_data = request.json or {}
        sheets = request_data.get('sheets', ['entities', 'documents'])
        entity_types = request_data.get('entity_types', None)
        date_from = request_data.get('date_from', None)

        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        # Sheet 1: Entities (if requested)
        if 'entities' in sheets:
            ws = wb.create_sheet("Encje")
            ws.append(['ID', 'Wartość', 'Typ', 'Wystąpienia', 'Dokumenty'])

            query = "SELECT e.id, e.entity_value, e.entity_type, COUNT(DISTINCT eo.page_id) as pages, COUNT(DISTINCT eo.file_id) as files FROM entities e LEFT JOIN entity_occurrences eo ON e.id = eo.entity_id"
            conditions = []
            params = []

            if entity_types:
                placeholders = ','.join(['?' for _ in entity_types])
                conditions.append(f"e.entity_type IN ({placeholders})")
                params.extend(entity_types)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " GROUP BY e.id ORDER BY pages DESC"

            entities = db.fetch_all(query, tuple(params))
            for e in entities:
                ws.append([e['id'], e['entity_value'], e['entity_type'], e['pages'] or 0, e['files'] or 0])

        # Sheet 2: Documents (if requested)
        if 'documents' in sheets:
            ws = wb.create_sheet("Dokumenty")
            ws.append(['Plik', 'Segregator', 'Strony', 'Tagi', 'Data importu'])

            files = db.fetch_all("""
                SELECT f.id, f.filename, b.name as binder, f.page_count,
                       GROUP_CONCAT(dt.tag, ', ') as tags, f.created_at
                FROM source_files f
                LEFT JOIN binders b ON f.binder_id = b.id
                LEFT JOIN document_tags dt ON f.id = dt.file_id
                GROUP BY f.id
                ORDER BY f.created_at DESC
            """)

            for f in files:
                ws.append([f['filename'], f['binder'] or '', f['page_count'], f['tags'] or '', str(f['created_at'])[:10] if f['created_at'] else ''])

        # Sheet 3: Land Registers (if requested)
        if 'kw' in sheets:
            ws = wb.create_sheet("Księgi Wieczyste")
            ws.append(['KW', 'Okręg', 'Adres', 'Właściciel', 'Pliki', 'Strony'])

            kws = db.get_all_land_registers()
            for kw in kws:
                ws.append([kw['kw_full'], kw['kw_district'], kw['property_address'] or '', kw['owner_manual'] or '', kw['files_count'], kw['pages_count']])

        # Styling all sheets
        header_fill = openpyxl.styles.PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = openpyxl.styles.Font(bold=True, color="FFFFFF")

        for ws in wb.worksheets:
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")

            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 50)

        db.disconnect()

        exports_dir = Path(CONFIG['exports_dir'])
        exports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"Zaawansowany_Eksport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = exports_dir / filename

        wb.save(str(filepath))

        return send_file(str(filepath), as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-all-excel', methods=['GET'])
def export_all_excel():
    """Eksport wszystkiego do Excel - wiele zakładek"""
    try:
        db = DatabaseManager(CONFIG['db_path'])
        db.connect()

        wb = openpyxl.Workbook()

        # Sheet 1: Księgi Wieczyste
        ws_kw = wb.active
        ws_kw.title = "Księgi Wieczyste"
        ws_kw.append(['KW', 'Okręg', 'Adres', 'Właściciel', 'Pliki', 'Strony'])
        kws = db.get_all_land_registers()
        for kw in kws:
            ws_kw.append([
                kw['kw_full'], kw['kw_district'],
                kw['property_address'] or '', kw['owner_manual'] or '',
                kw['files_count'], kw['pages_count']
            ])

        # Sheet 2: Pliki
        ws_files = wb.create_sheet("Pliki PDF")
        ws_files.append(['Plik', 'Segregator', 'Strony', 'Tagi'])
        files = db.fetch_all("""
            SELECT f.filename, b.name as binder, f.page_count,
                   GROUP_CONCAT(dt.tag, ', ') as tags
            FROM source_files f
            LEFT JOIN binders b ON f.binder_id = b.id
            LEFT JOIN document_tags dt ON f.id = dt.file_id
            GROUP BY f.id
        """)
        for f in files:
            ws_files.append([f['filename'], f['binder'] or '', f['page_count'], f['tags'] or ''])

        # Sheet 3: Osoby
        ws_persons = wb.create_sheet("Osoby")
        ws_persons.append(['Imię i nazwisko', 'Wystąpienia', 'Pliki'])
        persons = db.fetch_all("""
            SELECT e.entity_value,
                   COUNT(DISTINCT eo.page_id) as occ,
                   COUNT(DISTINCT eo.file_id) as files
            FROM entities e
            LEFT JOIN entity_occurrences eo ON e.id = eo.entity_id
            WHERE e.entity_type='person'
            GROUP BY e.id ORDER BY occ DESC
        """)
        for p in persons:
            ws_persons.append([p['entity_value'], p['occ'] or 0, p['files'] or 0])

        # Sheet 4: Firmy
        ws_companies = wb.create_sheet("Firmy")
        ws_companies.append(['Firma', 'Wystąpienia'])
        companies = db.fetch_all("""
            SELECT entity_value, COUNT(*) as cnt FROM entities
            WHERE entity_type='company' GROUP BY entity_value
        """)
        for c in companies:
            ws_companies.append([c['entity_value'], c['cnt']])

        # Sheet 5: NIPy
        ws_nips = wb.create_sheet("NIPy")
        ws_nips.append(['NIP'])
        nips = db.fetch_all("SELECT entity_value FROM entities WHERE entity_type='nip'")
        for n in nips:
            ws_nips.append([n['entity_value']])

        # Sheet 6: Telefony
        ws_phones = wb.create_sheet("Telefony")
        ws_phones.append(['Numer'])
        phones = db.fetch_all("SELECT entity_value FROM entities WHERE entity_type='phone'")
        for p in phones:
            ws_phones.append([p['entity_value']])

        # Styling
        header_fill = openpyxl.styles.PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        for ws in wb.worksheets:
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font

        db.disconnect()

        # Zapisz
        exports_dir = Path(CONFIG['exports_dir'])
        exports_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        filename = f"Pelny_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = exports_dir / filename
        wb.save(str(filepath))

        return send_file(str(filepath), as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🌐 Virtual Segregatory Web UI")
    print("=" * 50)
    print("✅ Otwórz przeglądarkę: http://localhost:5001")
    print("=" * 50 + "\n")
    app.run(debug=True, host='localhost', port=5001)
