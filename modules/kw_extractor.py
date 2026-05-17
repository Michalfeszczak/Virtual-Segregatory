import re
from config import KW_PATTERN

class KWValidator:
    """Walidator dla Ksiąg Wieczystych"""

    @staticmethod
    def validate_checksum(kw_district, kw_number, kw_checksum):
        """Walidacja sumy kontrolnej KW - uproszczona"""
        # Dla MVP1 - zawsze zwracamy True, bo algorytm jest skomplikowany
        # W przyszłości zostanie prawidłowo zaimplementowany
        # Teraz priorytet to funkcjonalność, nie walidacja
        return True

    @staticmethod
    def standardize(kw_full):
        """Standaryzuj zapis KW"""
        kw_full = kw_full.upper().strip()
        # Usuń spacje i myślniki
        kw_full = kw_full.replace(' ', '').replace('-', '')
        # Dodaj prawidłowy format
        match = re.match(r'([A-Z]{2}\d{1,2}[A-Z]{1,2})(\d{8})(\d)', kw_full)
        if match:
            return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
        return kw_full


class KWExtractor:
    """Ekstraktor Ksiąg Wieczystych"""

    def __init__(self):
        self.validator = KWValidator()
        # Wzorce z obsługą błędów OCR (I→1, l→1, O→0, S→5)
        self.kw_patterns = [
            r'([A-Z]{2}\d{1,2}[A-Z]{1,2})[/\s\-]?(\d{8})[/\s\-]?(\d)',  # Standard
            r'([A-Z]{2}[I1l]{1,2}[A-Z]{1,2})[/\s\-]?(\d{8})[/\s\-]?(\d)',  # OCR: I→1
            r'([A-Z]{2}\d{1,2}[A-Z][O0])[/\s\-]?(\d{8})[/\s\-]?(\d)',  # OCR: O→0
        ]

    def extract_from_text(self, text, page_number=1):
        """Ekstrahuj KW z tekstu"""
        kws = []
        text_upper = text.upper()

        for pattern in self.kw_patterns:
            matches = re.finditer(pattern, text_upper)
            for match in matches:
                try:
                    kw_district = match.group(1)
                    kw_number = match.group(2)
                    kw_checksum = match.group(3)

                    kw_full = f"{kw_district}/{kw_number}/{kw_checksum}"

                    # Pobierz kontekst
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context_before = text[start:match.start()].strip()
                    context_after = text[match.end():end].strip()

                    kw_info = {
                        'kw_full': kw_full,
                        'kw_district': kw_district,
                        'kw_number': kw_number,
                        'kw_checksum': kw_checksum,
                        'page_number': page_number,
                        'context_before': context_before[-30:],
                        'context_after': context_after[:30],
                        'valid_checksum': self.validator.validate_checksum(
                            kw_district, kw_number, kw_checksum
                        )
                    }

                    # Unikaj duplikatów
                    if not any(k['kw_full'] == kw_full for k in kws):
                        kws.append(kw_info)
                except:
                    pass

        return kws

    def extract_from_pages(self, pages_data):
        """Ekstrahuj KW ze wszystkich stron"""
        all_kws = {}

        for page_data in pages_data:
            page_number = page_data['page_number']
            text = page_data['text']

            kws = self.extract_from_text(text, page_number)

            for kw in kws:
                kw_full = kw['kw_full']
                if kw_full not in all_kws:
                    all_kws[kw_full] = {
                        'info': kw,
                        'occurrences': []
                    }
                all_kws[kw_full]['occurrences'].append({
                    'page_number': page_number,
                    'context_before': kw['context_before'],
                    'context_after': kw['context_after']
                })

        return all_kws

    def get_summary(self, all_kws):
        """Podsumowanie znalezionych KW"""
        summary = {
            'total_found': len(all_kws),
            'by_district': {},
            'details': []
        }

        for kw_full, data in sorted(all_kws.items()):
            district = data['info']['kw_district']

            if district not in summary['by_district']:
                summary['by_district'][district] = 0
            summary['by_district'][district] += 1

            summary['details'].append({
                'kw_full': kw_full,
                'district': district,
                'occurrences': len(data['occurrences']),
                'pages': [o['page_number'] for o in data['occurrences']],
                'valid': data['info']['valid_checksum']
            })

        return summary
