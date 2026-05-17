"""
Document Tagger - Auto-rozpoznawanie typu dokumentu
Faktura, Umowa, Decyzja, KW, Wniosek, etc.
"""
import re


class DocumentTagger:
    """Auto-tagowanie dokumentów na podstawie zawartości"""

    # Reguły dla typów dokumentów
    DOCUMENT_TYPES = {
        'faktura': {
            'keywords': [
                r'\bfaktura\s+(?:VAT|nr|numer)?', r'\bFV\b', r'\bf-ra\b',
                r'\bnabywca\b', r'\bsprzedawca\b', r'\btermin\s+płatności\b',
                r'\bNIP\s+nabywcy\b', r'\bvat\b', r'\bdo\s+zapłaty\b'
            ],
            'min_matches': 2,
            'weight': 3
        },
        'umowa': {
            'keywords': [
                r'\bumowa\b', r'\bstrony\s+umowy\b', r'\bzawarta\s+w\b',
                r'\bniniejszej\s+umowy\b', r'\bwarunki\s+umowy\b',
                r'§\s*\d+', r'\bart\.\s*\d+\b'
            ],
            'min_matches': 2,
            'weight': 3
        },
        'umowa_najmu': {
            'keywords': [
                r'\bumowa\s+najmu\b', r'\bnajemca\b', r'\bwynajmujący\b',
                r'\bczynsz\b', r'\bnajem\b'
            ],
            'min_matches': 2,
            'weight': 4
        },
        'umowa_sprzedazy': {
            'keywords': [
                r'\bumowa\s+sprzedaży\b', r'\bkupujący\b', r'\bsprzedający\b',
                r'\bcena\s+sprzedaży\b', r'\bprzeniesienie\s+własności\b'
            ],
            'min_matches': 2,
            'weight': 4
        },
        'akt_notarialny': {
            'keywords': [
                r'\bakt\s+notarialny\b', r'\bnotariusz\b', r'\bRep\.?\s*A\b',
                r'\bw\s+kancelarii\s+notarialnej\b'
            ],
            'min_matches': 2,
            'weight': 4
        },
        'ksiega_wieczysta': {
            'keywords': [
                r'\bksięga\s+wieczysta\b', r'\bksiędze\s+wieczystej\b',
                r'[A-Z]{2}\d{1,2}[A-Z]{1,2}/\d{8}/\d',
                r'\bdział\s+[I|II|III|IV]\b', r'\bhipoteka\b'
            ],
            'min_matches': 1,
            'weight': 4
        },
        'decyzja': {
            'keywords': [
                r'\bdecyzja\b', r'\bpostanowienie\b', r'\bdecyduje\b',
                r'\bna\s+podstawie\s+art\.\b', r'\borzeczenie\b'
            ],
            'min_matches': 2,
            'weight': 3
        },
        'wezwanie': {
            'keywords': [
                r'\bwezwanie\b', r'\bwzywa\s+się\b', r'\bwzywam\b',
                r'\bdo\s+zapłaty\b', r'\bostateczne\s+wezwanie\b'
            ],
            'min_matches': 1,
            'weight': 3
        },
        'pozew': {
            'keywords': [
                r'\bpozew\b', r'\bpowód\b', r'\bpozwany\b',
                r'\bdomagam\s+się\b', r'\bsądowy\b'
            ],
            'min_matches': 2,
            'weight': 4
        },
        'pismo_komornicze': {
            'keywords': [
                r'\bkomornik\b', r'\bKm\s+\d+/\d+\b', r'\begzekucja\b',
                r'\bzajęcie\b', r'\bdłużnik\b'
            ],
            'min_matches': 2,
            'weight': 4
        },
        'pismo_sadowe': {
            'keywords': [
                r'\bsąd\s+rejonowy\b', r'\bsąd\s+okręgowy\b',
                r'\bsygn\.?\s*akt\b', r'\bw\s+sprawie\b'
            ],
            'min_matches': 2,
            'weight': 3
        },
        'pelnomocnictwo': {
            'keywords': [
                r'\bpełnomocnictwo\b', r'\bupoważniam\b',
                r'\bdo\s+reprezentowania\b', r'\bpełnomocnik\b'
            ],
            'min_matches': 1,
            'weight': 4
        },
        'wniosek': {
            'keywords': [
                r'\bwniosek\b', r'\bwnioskuję\b', r'\bwniosła\b',
                r'\bo\s+wydanie\b', r'\bprosze\s+o\b'
            ],
            'min_matches': 2,
            'weight': 2
        },
        'zaswiadczenie': {
            'keywords': [
                r'\bzaświadczenie\b', r'\bniniejszym\s+zaświadczam\b',
                r'\bpotwierdzam\b'
            ],
            'min_matches': 1,
            'weight': 3
        },
        'pit_zus': {
            'keywords': [
                r'\bPIT\b', r'\bZUS\b', r'\bUS\b', r'\bdeklaracja\s+podatkowa\b',
                r'\bskładka\b', r'\bpodatek\b'
            ],
            'min_matches': 2,
            'weight': 3
        },
    }

    def tag_document(self, text):
        """Rozpoznaj typy dokumentu na podstawie tekstu"""
        results = []
        text_lower = text.lower()

        for doc_type, rules in self.DOCUMENT_TYPES.items():
            matches = 0
            for keyword in rules['keywords']:
                if re.search(keyword, text_lower, re.IGNORECASE):
                    matches += 1

            if matches >= rules['min_matches']:
                confidence = min(1.0, (matches / len(rules['keywords'])) * rules['weight'] / 4)
                results.append({
                    'type': doc_type,
                    'matches': matches,
                    'confidence': round(confidence, 2)
                })

        # Sortuj po confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results

    def get_primary_tag(self, text):
        """Zwróć najbardziej prawdopodobny tag"""
        tags = self.tag_document(text)
        return tags[0] if tags else None

    def tag_pages_combined(self, pages_texts):
        """Tag dla wielu stron (jeden dokument)"""
        combined_text = ' '.join(pages_texts)
        return self.tag_document(combined_text)
