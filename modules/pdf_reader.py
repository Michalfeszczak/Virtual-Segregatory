import hashlib
import pdfplumber
import pytesseract
from PIL import Image
import io
from pathlib import Path

class PDFReader:
    def __init__(self):
        self.encoding = 'utf-8'
        self.use_ocr = True

    def read_pdf(self, pdf_path):
        """Czytaj PDF i ekstrahuj tekst (z OCR jeśli trzeba)"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                print(f"❌ Plik nie istnieje: {pdf_path}")
                return None

            with pdfplumber.open(pdf_path) as pdf:
                pages_data = []
                for page_num, page in enumerate(pdf.pages, 1):
                    # Spróbuj czytać tekst normalnie
                    text = page.extract_text() or ""
                    text = self.normalize_text(text)

                    # Jeśli brak tekstu - użyj OCR
                    if not text or len(text.strip()) < 50:
                        text = self.extract_text_ocr(page, page_num)

                    pages_data.append({
                        'page_number': page_num,
                        'text': text,
                        'original_text': text
                    })

                return {
                    'filename': pdf_path.name,
                    'filepath': str(pdf_path),
                    'page_count': len(pdf.pages),
                    'file_hash': self.calculate_file_hash(pdf_path),
                    'pages': pages_data
                }

        except Exception as e:
            print(f"❌ Błąd odczytywania PDF: {e}")
            return None

    def extract_text_ocr(self, page, page_num):
        """Ekstrahuj tekst z OCR (Tesseract)"""
        try:
            # Konwertuj stronę na obraz
            image = page.to_image()

            # Pobierz obraz PIL
            pil_image = image.original

            # Uruchom OCR
            text = pytesseract.image_to_string(pil_image, lang='pol+eng')
            text = self.normalize_text(text)

            if text.strip():
                print(f"  ✓ Strona {page_num}: OCR sukces ({len(text)} znaków)")

            return text
        except Exception as e:
            print(f"  ⚠ Strona {page_num}: OCR błąd - {str(e)[:50]}")
            return ""

    def normalize_text(self, text):
        """Normalizuj tekst"""
        if not text:
            return ""
        # Zamień wielokrotne spacje na jedno
        text = ' '.join(text.split())
        # Usuń zbędne znaki
        text = text.replace('\x00', '')
        return text

    def calculate_file_hash(self, filepath):
        """Oblicz hash pliku"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
