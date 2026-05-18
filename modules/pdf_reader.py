"""
PDF Reader z OCR support - SZYBKA WERSJA
- Najpierw próbuje ekstrakcji tekstu wektorowego (PyMuPDF)
- Jeśli strona to obraz/scan, używa Tesseract OCR
- MULTI-THREADING dla OCR (4-8x szybsze na multi-core)
- Wsparcie dla polskich znaków
"""
import hashlib
import fitz  # PyMuPDF
from pathlib import Path
import pytesseract
from PIL import Image
import io
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing


class PDFReader:
    # Klasowe parametry konfiguracji (zmienne)
    OCR_LANG = 'pol+eng'
    OCR_CONFIG = '--oem 3 --psm 3'  # PSM 3 = auto page seg z OSD (szybkie + dokładne)
    OCR_ZOOM = 1.5  # 1.5x dla balansu szybkości/jakości (2.0 = wolne, lepsze; 1.0 = szybkie, gorsze)

    def __init__(self):
        self.encoding = 'utf-8'

        # Multi-threading: użyj 75% rdzeni CPU dla OCR
        cpu_count = multiprocessing.cpu_count()
        self.max_workers = max(2, int(cpu_count * 0.75))
        print(f"🧵 PDFReader: max_workers = {self.max_workers} (CPU cores: {cpu_count})")

        # Konfiguracja Tesseract
        tesseract_paths = [
            '/opt/homebrew/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/usr/bin/tesseract',
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break

        # TESSDATA_PREFIX
        tessdata_paths = [
            '/opt/homebrew/share/tessdata',
            '/usr/local/share/tessdata',
            '/usr/share/tesseract-ocr/4.00/tessdata',
        ]
        for path in tessdata_paths:
            if os.path.exists(path):
                os.environ['TESSDATA_PREFIX'] = path
                break

    def read_pdf(self, pdf_path, progress_callback=None, lazy_ocr=False):
        """
        Czytaj PDF i ekstrahuj tekst.

        Args:
            pdf_path: Ścieżka do pliku PDF
            progress_callback: Opcjonalna funkcja callback(current, total, text_preview)
            lazy_ocr: Jeśli True, OCR jest pomijany - tylko tekst wektorowy
                      (do OCR później on-demand). Bardzo szybkie!
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                print(f"❌ Plik nie istnieje: {pdf_path}")
                return None

            print(f"\n📄 Czytam PDF: {pdf_path.name}")
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            print(f"📖 Stron: {page_count}")
            print(f"🚀 Tryb: {'LAZY (bez OCR)' if lazy_ocr else 'PEŁNY (z OCR multi-thread)'}")

            start_time = time.time()

            # KROK 1: Najpierw szybko sprawdź wszystkie strony - tekst wektorowy
            vector_results = {}  # page_num -> text
            scan_pages = []  # page_num do OCR

            for page_num in range(page_count):
                page = doc[page_num]
                text = self.extract_searchable_text(page)

                if text and len(text.strip()) >= 10:
                    vector_results[page_num] = text
                else:
                    scan_pages.append(page_num)

            vector_count = len(vector_results)
            ocr_count = 0
            ocr_failed = 0

            print(f"📝 Tekst wektorowy: {vector_count}/{page_count} stron")
            print(f"🔍 Skany do OCR: {len(scan_pages)}/{page_count} stron")

            # KROK 2: OCR (jeśli potrzeba i nie lazy)
            ocr_results = {}  # page_num -> text

            if scan_pages and not lazy_ocr:
                # OCR w wielu wątkach - dramatyczne przyspieszenie!
                ocr_results, ocr_count, ocr_failed = self._batch_ocr(
                    doc, scan_pages, progress_callback, page_count
                )

            # KROK 3: Złóż wszystko razem
            pages_data = []
            for page_num in range(page_count):
                if page_num in vector_results:
                    text = vector_results[page_num]
                    method = "vector"
                elif page_num in ocr_results:
                    text = ocr_results[page_num]
                    method = "ocr"
                else:
                    text = ""  # Lazy OCR - tekst zostanie dodany później
                    method = "pending_ocr" if lazy_ocr else "ocr_failed"

                pages_data.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'original_text': text,
                    'method': method
                })

                if progress_callback and not (scan_pages and not lazy_ocr):
                    # Tylko jeśli OCR nie był wykonany (callback już został wywołany w batch_ocr)
                    try:
                        progress_callback(page_num + 1, page_count, text[:100])
                    except Exception:
                        pass

            doc.close()

            elapsed = time.time() - start_time
            print(f"\n✅ Odczyt zakończony w {elapsed:.1f}s:")
            print(f"   📝 Tekst wektorowy: {vector_count} stron")
            print(f"   🔍 OCR (multi-thread): {ocr_count} stron")
            if ocr_failed:
                print(f"   ⚠️  OCR nieudany: {ocr_failed} stron")
            if lazy_ocr and scan_pages:
                print(f"   ⏳ Czeka na OCR: {len(scan_pages)} stron (lazy)")

            return {
                'filename': pdf_path.name,
                'filepath': str(pdf_path),
                'page_count': page_count,
                'file_hash': self.calculate_file_hash(pdf_path),
                'pages': pages_data,
                'stats': {
                    'vector_pages': vector_count,
                    'ocr_pages': ocr_count,
                    'ocr_failed': ocr_failed,
                    'pending_ocr': len(scan_pages) if lazy_ocr else 0,
                    'processing_time': round(elapsed, 1)
                }
            }

        except Exception as e:
            import traceback
            print(f"❌ Błąd odczytywania PDF: {e}")
            print(traceback.format_exc())
            return None

    def _batch_ocr(self, doc, scan_pages, progress_callback, total_pages):
        """
        OCR wielu stron równolegle w wątkach.
        Zwraca: (results_dict, ocr_count, failed_count)
        """
        results = {}
        ocr_count = 0
        failed_count = 0
        completed = 0
        total_scans = len(scan_pages)

        # PRE-RENDER: Renderuj wszystkie obrazy stron PRZED OCR
        # (PyMuPDF nie jest thread-safe dla render, ale OCR tak)
        print(f"🎨 Renderuję {total_scans} stron do obrazów...")
        render_start = time.time()
        page_images = {}

        for page_num in scan_pages:
            try:
                page = doc[page_num]
                mat = fitz.Matrix(self.OCR_ZOOM, self.OCR_ZOOM)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("ppm")
                page_images[page_num] = img_bytes
            except Exception as e:
                print(f"⚠️ Błąd renderowania strony {page_num + 1}: {e}")
                failed_count += 1

        render_elapsed = time.time() - render_start
        print(f"✅ Render: {render_elapsed:.1f}s ({render_elapsed/max(1,len(page_images)):.2f}s/strona)")

        # PARALLEL OCR
        print(f"🔍 OCR w {self.max_workers} wątkach...")
        ocr_start = time.time()

        def ocr_worker(page_num, img_bytes):
            """Worker function dla OCR jednej strony"""
            try:
                img = Image.open(io.BytesIO(img_bytes))
                text = pytesseract.image_to_string(
                    img,
                    lang=self.OCR_LANG,
                    config=self.OCR_CONFIG
                )
                return page_num, self.normalize_text(text)
            except Exception as e:
                return page_num, None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(ocr_worker, page_num, img_bytes): page_num
                for page_num, img_bytes in page_images.items()
            }

            for future in as_completed(futures):
                page_num = futures[future]
                completed += 1
                try:
                    pnum, text = future.result()
                    if text and len(text.strip()) > 5:
                        results[pnum] = text
                        ocr_count += 1
                    else:
                        failed_count += 1

                    # Progress logging co 5 stron
                    if completed % 5 == 0 or completed == total_scans:
                        elapsed = time.time() - ocr_start
                        rate = completed / elapsed if elapsed > 0 else 0
                        eta = (total_scans - completed) / rate if rate > 0 else 0
                        print(f"   📊 OCR: {completed}/{total_scans} stron ({rate:.1f} str/s, ETA: {eta:.0f}s)")

                    if progress_callback:
                        try:
                            progress_callback(completed, total_scans, text[:100] if text else "")
                        except Exception:
                            pass
                except Exception as e:
                    failed_count += 1
                    print(f"❌ OCR worker error (strona {page_num + 1}): {e}")

        ocr_elapsed = time.time() - ocr_start
        print(f"✅ OCR zakończone: {ocr_elapsed:.1f}s ({ocr_elapsed/max(1, total_scans):.2f}s/strona)")

        return results, ocr_count, failed_count

    def normalize_text(self, text):
        """Normalizuj tekst (zachowaj polskie znaki!)"""
        if not text:
            return ""
        text = ' '.join(text.split())
        return text

    def extract_searchable_text(self, page):
        """
        Spróbuj wyciągnąć istniejącą warstwę tekstową PDF zanim odpalimy OCR.
        Niektóre PDF-y mają gotowy OCR, ale `get_text("text")` zwraca go ubogo.
        """
        text = self.normalize_text(page.get_text("text"))
        if len(text) >= 10:
            return text

        try:
            words = page.get_text("words") or []
            if words:
                fallback_text = self.normalize_text(" ".join(word[4] for word in words if len(word) > 4 and word[4]))
                if len(fallback_text) >= 10:
                    return fallback_text
        except Exception:
            pass

        return text

    def ocr_page(self, page, zoom=None):
        """OCR pojedynczej strony - używane dla on-demand OCR"""
        try:
            zoom = zoom or self.OCR_ZOOM
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))

            text = pytesseract.image_to_string(
                img,
                lang=self.OCR_LANG,
                config=self.OCR_CONFIG
            )
            return text if text.strip() else ""
        except pytesseract.TesseractError as e:
            print(f"❌ Błąd Tesseract OCR: {e}")
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), alpha=False)
                img = Image.open(io.BytesIO(pix.tobytes("ppm")))
                text = pytesseract.image_to_string(img, lang='eng')
                return text if text.strip() else ""
            except Exception:
                return ""
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd OCR: {e}")
            return ""

    def extract_single_page(self, pdf_path, page_number):
        """Ekstrahuj tekst z jednej konkretnej strony (on-demand OCR)"""
        try:
            doc = fitz.open(str(pdf_path))
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return None

            page = doc[page_number - 1]
            text = self.extract_searchable_text(page)

            if not text or len(text.strip()) < 10:
                text = self.ocr_page(page)
                text = self.normalize_text(text)

            doc.close()
            return text
        except Exception as e:
            print(f"❌ Błąd ekstrakcji strony: {e}")
            return None

    def extract_single_page_pdf(self, pdf_path, page_number, output_path=None):
        """Wyciągnij pojedynczą stronę jako oddzielny PDF (do podglądu)"""
        try:
            from PyPDF2 import PdfReader, PdfWriter

            reader = PdfReader(str(pdf_path))
            if page_number < 1 or page_number > len(reader.pages):
                return None

            writer = PdfWriter()
            writer.add_page(reader.pages[page_number - 1])

            if output_path:
                with open(output_path, 'wb') as f:
                    writer.write(f)
                return output_path
            else:
                buf = io.BytesIO()
                writer.write(buf)
                buf.seek(0)
                return buf
        except Exception as e:
            print(f"❌ Błąd ekstrakcji strony PDF: {e}")
            return None

    def calculate_file_hash(self, filepath):
        """Oblicz hash pliku (SHA-256)"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
