"""
Entity Extractor - Rozpoznawanie encji w dokumentach
Osoby, firmy, NIP, REGON, KRS, PESEL, telefony, adresy, daty, sygnatury
"""
import re
from collections import defaultdict


class EntityExtractor:
    """Ekstraktor encji z polskich dokumentów"""

    # Polskie imiona męskie (najczęstsze)
    POLISH_NAMES_MALE = {
        'Adam', 'Adrian', 'Aleksander', 'Andrzej', 'Antoni', 'Arkadiusz', 'Artur',
        'Bartłomiej', 'Bartosz', 'Bogdan', 'Bogusław', 'Bolesław',
        'Cezary', 'Czesław',
        'Damian', 'Dariusz', 'Dawid', 'Dominik',
        'Edward', 'Emil', 'Eugeniusz',
        'Filip', 'Franciszek',
        'Grzegorz',
        'Henryk', 'Hubert',
        'Igor', 'Ireneusz', 'Ignacy',
        'Jacek', 'Jakub', 'Jan', 'Janusz', 'Jarosław', 'Jerzy', 'Józef',
        'Kacper', 'Karol', 'Kazimierz', 'Konrad', 'Krystian', 'Krzysztof',
        'Leszek', 'Lech', 'Ludwik',
        'Maciej', 'Marcin', 'Marek', 'Mariusz', 'Mateusz', 'Michał', 'Mieczysław', 'Mikołaj',
        'Norbert',
        'Patryk', 'Paweł', 'Piotr', 'Przemysław',
        'Radosław', 'Rafał', 'Robert', 'Roman', 'Ryszard',
        'Sebastian', 'Sławomir', 'Stanisław', 'Stefan', 'Sylwester', 'Szymon',
        'Tadeusz', 'Tomasz',
        'Wacław', 'Waldemar', 'Wiesław', 'Wiktor', 'Witold', 'Władysław',
        'Włodzimierz', 'Wojciech',
        'Zbigniew', 'Zdzisław', 'Zygmunt',
        'Łukasz',
    }

    # Polskie imiona żeńskie
    POLISH_NAMES_FEMALE = {
        'Agata', 'Agnieszka', 'Aleksandra', 'Alicja', 'Anna', 'Aniela',
        'Barbara', 'Beata', 'Bogumiła', 'Bożena',
        'Cecylia',
        'Danuta', 'Dorota',
        'Edyta', 'Elżbieta', 'Emilia', 'Ewa', 'Ewelina',
        'Grażyna',
        'Halina', 'Hanna', 'Helena',
        'Iga', 'Ilona', 'Irena', 'Iwona', 'Izabela',
        'Jadwiga', 'Janina', 'Joanna', 'Jolanta', 'Justyna',
        'Karolina', 'Katarzyna', 'Kazimiera', 'Klaudia', 'Krystyna',
        'Lidia', 'Lucyna',
        'Magdalena', 'Maja', 'Małgorzata', 'Maria', 'Marianna', 'Marta', 'Martyna', 'Marzena',
        'Mirosława', 'Monika',
        'Natalia',
        'Olga',
        'Patrycja', 'Paulina',
        'Renata', 'Róża',
        'Sandra', 'Stanisława', 'Stefania', 'Sylwia',
        'Teresa',
        'Urszula',
        'Wanda', 'Weronika', 'Wiesława',
        'Zofia', 'Zuzanna',
    }

    # Formy prawne firm
    COMPANY_FORMS = [
        r'Sp\.\s*z\s*o\.?o\.?',
        r'sp\.?\s*z\s*o\.?o\.?',
        r'S\.?A\.?',
        r'Sp\.?\s*j\.?',
        r'Sp\.?\s*k\.?',
        r'sp\.?\s*komandyt',
        r'spółka',
        r'Spółka',
        r'Sp\.?\s*akcyjna',
    ]

    # Instytucje
    INSTITUTIONS = [
        'Sąd Rejonowy', 'Sąd Okręgowy', 'Sąd Apelacyjny', 'Sąd Najwyższy',
        'Urząd Gminy', 'Urząd Miasta', 'Urząd Skarbowy', 'Urząd Wojewódzki',
        'Urząd Marszałkowski', 'Urząd Stanu Cywilnego',
        'Kancelaria Notarialna', 'Notariusz',
        'Komornik', 'Komornik Sądowy',
        'Bank', 'Spółdzielnia',
        'Wspólnota Mieszkaniowa', 'Wspólnota',
        'Stowarzyszenie', 'Fundacja',
        'NFZ', 'ZUS', 'GUS', 'KRUS',
        'Starostwo Powiatowe',
    ]

    def __init__(self):
        # Kompiluj regex'y dla wydajności
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        """Kompiluj wszystkie wzorce regex"""
        return {
            'nip': re.compile(r'(?:NIP[\s:.-]*)?(\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}|\d{10})'),
            'regon': re.compile(r'(?:REGON[\s:.-]*)?(\d{9}|\d{14})'),
            'krs': re.compile(r'(?:KRS[\s:.-]*)?(\d{10})'),
            'pesel': re.compile(r'(?:PESEL[\s:.-]*)?(\d{11})'),
            'phone': re.compile(r'(?:tel\.?|telefon|kom\.?|mob\.?)[\s:.-]*((?:\+?48[\s-]?)?(?:\d{3}[\s-]?\d{3}[\s-]?\d{3}|\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}))', re.IGNORECASE),
            'phone_simple': re.compile(r'\b(?:\+?48[\s-]?)?(\d{3}[\s-]?\d{3}[\s-]?\d{3})\b'),
            'email': re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'),
            'kw': re.compile(r'\b([A-Z]{2,4}[\d/]{1,2}[A-Z]{0,2})[\s/-]?(\d{8})[\s/-]?(\d)\b'),
            'date': re.compile(r'\b(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})\b'),
            'date_word': re.compile(r'\b(\d{1,2})\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+(\d{4})\b', re.IGNORECASE),
            'sygnatura_akt': re.compile(r'(?:Sygn\.?\s*akt[\s:.-]*)([IVXLC]+\s*[A-Z]{1,3}\s*\d+/\d+)', re.IGNORECASE),
            'sygnatura_komornicza': re.compile(r'(?:Km\.?\s*)(\d+/\d+)', re.IGNORECASE),
            'rep_a': re.compile(r'(?:Rep\.?\s*A[\s:.-]*)(\d+/\d+)', re.IGNORECASE),
            'postal_code': re.compile(r'\b(\d{2}-\d{3})\b'),
            'amount_pln': re.compile(r'\b(\d{1,3}(?:\s\d{3})*(?:,\d{2})?)\s*(?:zł|PLN|złotych)\b'),
        }

    @staticmethod
    def validate_nip(nip):
        """Walidacja NIP"""
        nip = re.sub(r'[\s-]', '', nip)
        if len(nip) != 10 or not nip.isdigit():
            return False
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(nip[i]) * weights[i] for i in range(9)) % 11
        return checksum == int(nip[9])

    @staticmethod
    def validate_pesel(pesel):
        """Walidacja PESEL"""
        pesel = re.sub(r'\s', '', pesel)
        if len(pesel) != 11 or not pesel.isdigit():
            return False
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = (10 - sum(int(pesel[i]) * weights[i] for i in range(10)) % 10) % 10
        return checksum == int(pesel[10])

    @staticmethod
    def validate_regon(regon):
        """Walidacja REGON (9 lub 14 cyfr)"""
        regon = re.sub(r'[\s-]', '', regon)
        if len(regon) == 9:
            weights = [8, 9, 2, 3, 4, 5, 6, 7]
            checksum = sum(int(regon[i]) * weights[i] for i in range(8)) % 11
            return checksum % 10 == int(regon[8])
        elif len(regon) == 14:
            weights = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
            checksum = sum(int(regon[i]) * weights[i] for i in range(13)) % 11
            return checksum % 10 == int(regon[13])
        return False

    def extract_persons(self, text):
        """Wyłapuj osoby z imienia + nazwiska"""
        persons = []
        all_names = self.POLISH_NAMES_MALE | self.POLISH_NAMES_FEMALE

        # Wzorzec: Imię + Nazwisko (z dużej litery)
        pattern = re.compile(
            r'\b([A-ZŁŻŚĆŃÓĄĘ][a-zżółćńąęś]+)\s+([A-ZŁŻŚĆŃÓĄĘ][a-zżółćńąęś]+(?:-[A-ZŁŻŚĆŃÓĄĘ][a-zżółćńąęś]+)?)\b'
        )

        for match in pattern.finditer(text):
            first_name = match.group(1)
            last_name = match.group(2)

            if first_name in all_names:
                gender = 'M' if first_name in self.POLISH_NAMES_MALE else 'F'
                persons.append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'gender': gender,
                    'full_name': f"{first_name} {last_name}",
                    'position': match.start()
                })

        return self._deduplicate(persons, 'full_name')

    def extract_companies(self, text):
        """Wyłapuj nazwy firm"""
        companies = []

        # Pattern: Nazwa + forma prawna
        for form in self.COMPANY_FORMS:
            pattern = re.compile(
                r'([A-ZŁŻŚĆŃÓĄĘ][\w\s&\.\-]{2,80}?)\s+' + form,
                re.IGNORECASE
            )
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 80:
                    companies.append({
                        'name': name,
                        'form': form,
                        'full_name': match.group(0),
                        'position': match.start()
                    })

        return self._deduplicate(companies, 'name')

    def extract_institutions(self, text):
        """Wyłapuj instytucje publiczne"""
        institutions = []

        for inst in self.INSTITUTIONS:
            pattern = re.compile(r'\b' + re.escape(inst) + r'(?:\s+w\s+[A-ZŁŻŚĆŃÓĄĘ][\w]+)?', re.IGNORECASE)
            for match in pattern.finditer(text):
                institutions.append({
                    'name': match.group(0),
                    'type': inst,
                    'position': match.start()
                })

        return self._deduplicate(institutions, 'name')

    def extract_nips(self, text):
        """Wyłapuj numery NIP"""
        nips = []
        for match in self.patterns['nip'].finditer(text):
            nip = re.sub(r'[\s-]', '', match.group(1))
            if len(nip) == 10:
                nips.append({
                    'nip': nip,
                    'formatted': f"{nip[:3]}-{nip[3:6]}-{nip[6:8]}-{nip[8:]}",
                    'valid': self.validate_nip(nip),
                    'position': match.start()
                })
        return self._deduplicate(nips, 'nip')

    def extract_regons(self, text):
        """Wyłapuj numery REGON"""
        regons = []
        for match in self.patterns['regon'].finditer(text):
            regon = re.sub(r'[\s-]', '', match.group(1))
            if len(regon) in [9, 14]:
                regons.append({
                    'regon': regon,
                    'valid': self.validate_regon(regon),
                    'position': match.start()
                })
        return self._deduplicate(regons, 'regon')

    def extract_krs(self, text):
        """Wyłapuj numery KRS"""
        krs_list = []
        for match in self.patterns['krs'].finditer(text):
            krs = match.group(1)
            if len(krs) == 10:
                krs_list.append({
                    'krs': krs,
                    'position': match.start()
                })
        return self._deduplicate(krs_list, 'krs')

    def extract_pesels(self, text):
        """Wyłapuj numery PESEL"""
        pesels = []
        for match in self.patterns['pesel'].finditer(text):
            pesel = match.group(1)
            if len(pesel) == 11:
                pesels.append({
                    'pesel': pesel,
                    'valid': self.validate_pesel(pesel),
                    'position': match.start()
                })
        return self._deduplicate(pesels, 'pesel')

    def extract_phones(self, text):
        """Wyłapuj numery telefonów"""
        phones = []

        # Pattern z prefiksem "tel."
        for match in self.patterns['phone'].finditer(text):
            phone = re.sub(r'[\s-]', '', match.group(1))
            phones.append({
                'phone': phone,
                'context': 'explicit',
                'position': match.start()
            })

        # Pattern bez prefiksu - tylko 9 cyfrowe (telefon komórkowy/stacjonarny)
        for match in self.patterns['phone_simple'].finditer(text):
            phone = re.sub(r'[\s-]', '', match.group(1))
            if len(phone) == 9 and phone[0] in '456789':
                if not any(p['phone'] == phone for p in phones):
                    phones.append({
                        'phone': phone,
                        'context': 'inferred',
                        'position': match.start()
                    })

        return self._deduplicate(phones, 'phone')

    def extract_emails(self, text):
        """Wyłapuj adresy email"""
        emails = []
        for match in self.patterns['email'].finditer(text):
            emails.append({
                'email': match.group(1).lower(),
                'position': match.start()
            })
        return self._deduplicate(emails, 'email')

    def extract_dates(self, text):
        """Wyłapuj daty"""
        dates = []
        months = {
            'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4,
            'maja': 5, 'czerwca': 6, 'lipca': 7, 'sierpnia': 8,
            'września': 9, 'października': 10, 'listopada': 11, 'grudnia': 12
        }

        # Daty numeryczne
        for match in self.patterns['date'].finditer(text):
            try:
                day, month, year = match.group(1), match.group(2), match.group(3)
                if len(year) == 2:
                    year = '20' + year if int(year) < 50 else '19' + year
                d, m, y = int(day), int(month), int(year)
                if 1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2100:
                    dates.append({
                        'date': f"{y:04d}-{m:02d}-{d:02d}",
                        'original': match.group(0),
                        'position': match.start()
                    })
            except:
                pass

        # Daty słowne
        for match in self.patterns['date_word'].finditer(text):
            try:
                day = int(match.group(1))
                month = months.get(match.group(2).lower(), 0)
                year = int(match.group(3))
                if month and 1 <= day <= 31:
                    dates.append({
                        'date': f"{year:04d}-{month:02d}-{day:02d}",
                        'original': match.group(0),
                        'position': match.start()
                    })
            except:
                pass

        return self._deduplicate(dates, 'date')

    def extract_signatures(self, text):
        """Wyłapuj sygnatury sądowe i komornicze"""
        signatures = []

        # Sygnatury akt sądowych
        for match in self.patterns['sygnatura_akt'].finditer(text):
            signatures.append({
                'type': 'akt',
                'value': match.group(1),
                'position': match.start()
            })

        # Sygnatury komornicze
        for match in self.patterns['sygnatura_komornicza'].finditer(text):
            signatures.append({
                'type': 'komornicza',
                'value': f"Km {match.group(1)}",
                'position': match.start()
            })

        # Rep A (akty notarialne)
        for match in self.patterns['rep_a'].finditer(text):
            signatures.append({
                'type': 'rep_a',
                'value': f"Rep. A {match.group(1)}",
                'position': match.start()
            })

        return self._deduplicate(signatures, 'value')

    def extract_postal_codes(self, text):
        """Wyłapuj kody pocztowe"""
        codes = []
        for match in self.patterns['postal_code'].finditer(text):
            codes.append({
                'code': match.group(1),
                'position': match.start()
            })
        return self._deduplicate(codes, 'code')

    def extract_amounts(self, text):
        """Wyłapuj kwoty w PLN"""
        amounts = []
        for match in self.patterns['amount_pln'].finditer(text):
            try:
                amount_str = match.group(1).replace(' ', '').replace(',', '.')
                value = float(amount_str)
                amounts.append({
                    'value': value,
                    'formatted': match.group(0),
                    'position': match.start()
                })
            except:
                pass
        return amounts

    def extract_all(self, text):
        """Wyłapuj wszystkie encje"""
        return {
            'persons': self.extract_persons(text),
            'companies': self.extract_companies(text),
            'institutions': self.extract_institutions(text),
            'nips': self.extract_nips(text),
            'regons': self.extract_regons(text),
            'krs': self.extract_krs(text),
            'pesels': self.extract_pesels(text),
            'phones': self.extract_phones(text),
            'emails': self.extract_emails(text),
            'dates': self.extract_dates(text),
            'signatures': self.extract_signatures(text),
            'postal_codes': self.extract_postal_codes(text),
            'amounts': self.extract_amounts(text),
        }

    def get_summary(self, entities):
        """Podsumowanie wszystkich encji"""
        return {
            'persons': len(entities['persons']),
            'companies': len(entities['companies']),
            'institutions': len(entities['institutions']),
            'nips': len(entities['nips']),
            'regons': len(entities['regons']),
            'krs': len(entities['krs']),
            'pesels': len(entities['pesels']),
            'phones': len(entities['phones']),
            'emails': len(entities['emails']),
            'dates': len(entities['dates']),
            'signatures': len(entities['signatures']),
            'postal_codes': len(entities['postal_codes']),
            'amounts': len(entities['amounts']),
            'total': sum(len(v) for v in entities.values())
        }

    @staticmethod
    def _deduplicate(items, key):
        """Usuń duplikaty z listy słowników"""
        seen = set()
        result = []
        for item in items:
            if item[key] not in seen:
                seen.add(item[key])
                result.append(item)
        return result
