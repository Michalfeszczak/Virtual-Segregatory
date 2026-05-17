"""
Entity Extractor - Rozpoznawanie encji w dokumentach
Osoby, firmy, NIP, REGON, KRS, PESEL, telefony, adresy, daty, sygnatury
"""
import re
from collections import defaultdict


class EntityExtractor:
    """Ekstraktor encji z polskich dokumentów"""

    # PEŁNY słownik polskich imion męskich (350+)
    POLISH_NAMES_MALE = {
        'Aaron', 'Abel', 'Abraham', 'Achim', 'Adam', 'Adrian', 'Albin', 'Albrecht',
        'Aleks', 'Aleksander', 'Aleksy', 'Alfons', 'Alfred', 'Alojzy', 'Amadeusz',
        'Ambroży', 'Anatol', 'Andrzej', 'Antoni', 'Apolinary', 'Arek',
        'Arian', 'Arkadiusz', 'Armand', 'Arnold', 'Artur', 'August', 'Aureliusz',
        'Bartek', 'Bartłomiej', 'Bartosz', 'Bazyli', 'Beniamin', 'Benedykt',
        'Benjamin', 'Bernard', 'Błażej', 'Bogdan', 'Bogumił', 'Bogusław',
        'Bohdan', 'Bolesław', 'Bonifacy', 'Borys', 'Brajan', 'Bronisław',
        'Bruno',
        'Cezary', 'Cyprian', 'Cyryl', 'Czesław',
        'Damian', 'Daniel', 'Dariusz', 'Dawid', 'Demian', 'Denis',
        'Dezyderiusz', 'Dionizy', 'Dobromir', 'Dobrosław', 'Dominik', 'Donald',
        'Donat',
        'Edgar', 'Edmund', 'Edward', 'Edwin', 'Eliasz', 'Eligiusz', 'Emanuel',
        'Emil', 'Erik', 'Eryk', 'Ernest', 'Eugeniusz', 'Eustachy', 'Ezechiel',
        'Fabian', 'Fabio', 'Faustyn', 'Felicjan', 'Feliks', 'Ferdynand',
        'Filip', 'Florian', 'Franciszek', 'Fryderyk',
        'Gabriel', 'Gerard', 'German', 'Gracjan', 'Grzegorz', 'Gustaw', 'Gwido',
        'Henryk', 'Herbert', 'Hieronim', 'Hilary', 'Hipolit', 'Hubert', 'Hugo',
        'Ignacy', 'Igor', 'Iwan', 'Iwo', 'Izaak', 'Izydor', 'Ireneusz',
        'Jacek', 'Jakub', 'Jan', 'January', 'Janusz', 'Jarema', 'Jaromir',
        'Jarosław', 'Jerzy', 'Joachim', 'Joel', 'Jonasz', 'Jonatan', 'Józef',
        'Julian', 'Juliusz', 'Justyn', 'Justynian',
        'Kacper', 'Kajetan', 'Kalikst', 'Kamil', 'Karol', 'Kasper', 'Kazimierz',
        'Kewin', 'Kim', 'Klaudiusz', 'Klemens', 'Konstanty', 'Konrad', 'Kordian',
        'Kornel', 'Kosma', 'Krystian', 'Krzysztof', 'Ksawery', 'Kuba',
        'Lech', 'Leon', 'Leonard', 'Leonid', 'Leopold', 'Leszek', 'Liam',
        'Lubomir', 'Lucjan', 'Ludwik',
        'Maciej', 'Maks', 'Maksym', 'Maksymilian', 'Marceli', 'Marcin', 'Marek',
        'Marian', 'Mariusz', 'Mark', 'Martin', 'Mateusz', 'Maurycy',
        'Michał', 'Mieczysław', 'Mieszko', 'Mikołaj', 'Miłosz',
        'Miłosław', 'Miron', 'Modest', 'Mojżesz',
        'Narcyz', 'Natan', 'Natanael', 'Nikodem', 'Niko', 'Norbert',
        'Oktawian', 'Olaf', 'Oleg', 'Oliwer', 'Olgierd', 'Onufry', 'Oskar',
        'Otto',
        'Pankracy', 'Paweł', 'Patryk', 'Pius', 'Piotr', 'Placyd', 'Prokop',
        'Przemek', 'Przemysław',
        'Rafael', 'Rafał', 'Radomir', 'Radosław', 'Rajmund', 'Remigiusz',
        'Renat', 'Robert', 'Roch', 'Roman', 'Romeo', 'Romuald', 'Ronald',
        'Rudolf', 'Rufin', 'Rupert', 'Ryszard',
        'Sebastian', 'Serafin', 'Sergiusz', 'Seweryn', 'Sławomir', 'Sławek',
        'Stanisław', 'Stefan', 'Sylwester', 'Sylwiusz', 'Symeon',
        'Szczepan', 'Szymon',
        'Tadeusz', 'Tobiasz', 'Teobald', 'Teodor', 'Teofil', 'Tymon',
        'Tymoteusz', 'Tytus', 'Tomasz',
        'Ulrich', 'Urban',
        'Walenty', 'Walerian', 'Walery', 'Wacław', 'Waldemar', 'Wawrzyniec',
        'Wenancjusz', 'Wiesław', 'Wiktor', 'Wilhelm', 'Wincenty',
        'Witold', 'Władysław', 'Włodzimierz', 'Wojciech',
        'Xawier',
        'Zachariasz', 'Zbigniew', 'Zbysław', 'Zdzisław', 'Zenobiusz', 'Zenon',
        'Ziemowit', 'Zygmunt',
        'Żelisław',
        'Łazarz', 'Łukasz',
        'Ścibor', 'Świętopełk', 'Świętosław',
    }

    # PEŁNY słownik polskich imion żeńskich (350+)
    POLISH_NAMES_FEMALE = {
        'Adelajda', 'Adriana', 'Agata', 'Agnieszka', 'Aida', 'Aldona', 'Aleksandra',
        'Alicja', 'Alina', 'Alma', 'Amalia', 'Amelia', 'Amira', 'Anabela', 'Anastazja',
        'Andżelika', 'Aneta', 'Angelika', 'Aniela', 'Anita', 'Anna', 'Antonina',
        'Antonia', 'Apolonia', 'Ariana', 'Aurelia', 'Aurora',
        'Balbina', 'Barbara', 'Beata', 'Berenika', 'Bernadeta', 'Bernardyna',
        'Berta', 'Bianka', 'Blanka', 'Bogna', 'Bogumiła', 'Bogusława', 'Bożena',
        'Brygida',
        'Cecylia', 'Celina', 'Cezaryna', 'Charlotta', 'Cyrylla',
        'Daniela', 'Danuta', 'Daria', 'Diana', 'Dobrochna', 'Dobromira',
        'Dobrosława', 'Dominika', 'Donata', 'Dorota',
        'Edyta', 'Ela', 'Elektra', 'Eliza', 'Elwira', 'Elżbieta', 'Emanuela',
        'Emilia', 'Emma', 'Erna', 'Estera', 'Eufemia', 'Eugenia', 'Eulalia',
        'Eunika', 'Eustachia', 'Ewa', 'Ewelina',
        'Fabiana', 'Felicja', 'Felicyta', 'Filipina', 'Filomena', 'Flora',
        'Florentyna', 'Franciszka',
        'Gabriela', 'Gabriella', 'Genowefa', 'Gertruda', 'Gizela', 'Grażyna',
        'Greta', 'Gryzelda',
        'Halina', 'Hanna', 'Hanka', 'Helena', 'Henryka', 'Hermina', 'Hilaria',
        'Honorata', 'Hortensja',
        'Ida', 'Idalia', 'Iga', 'Ilona', 'Inez', 'Inga', 'Irena',
        'Irma', 'Ismena', 'Iwa', 'Iwona', 'Izabela', 'Izolda',
        'Jadwiga', 'Jagienka', 'Jagoda', 'Jana', 'Janina', 'Jasmin',
        'Joanna', 'Joasia', 'Jola', 'Jolanta', 'Judyta', 'Julia', 'Julianna',
        'Julita', 'Justyna',
        'Kalina', 'Kamila', 'Karina', 'Karla', 'Karolina', 'Katarzyna',
        'Kazimiera', 'Kinga', 'Klara', 'Klaudia', 'Klementyna',
        'Kleopatra', 'Konstancja', 'Kornelia', 'Krystyna', 'Krystianna',
        'Ksawera', 'Ksenia',
        'Laila', 'Lara', 'Larysa', 'Laura', 'Lea', 'Lena', 'Leokadia',
        'Leonia', 'Leontyna', 'Lidia', 'Liliana', 'Linda', 'Liwia', 'Lola',
        'Lorena', 'Lubomira', 'Lucja', 'Lucyna', 'Ludmila',
        'Ludmiła', 'Ludwika', 'Luiza', 'Luna',
        'Magda', 'Magdalena', 'Maja', 'Malina', 'Małgorzata', 'Manuela',
        'Mara', 'Maria', 'Marianna', 'Mariola', 'Maryla', 'Marlena', 'Marta',
        'Martyna', 'Maryna', 'Marzena', 'Matylda', 'Melania', 'Melisa', 'Mia',
        'Michalina', 'Mila', 'Milena', 'Mira', 'Mirella', 'Miriam',
        'Mirosława', 'Misia', 'Monika',
        'Nadia', 'Nadzieja', 'Natalia', 'Nela', 'Nika',
        'Nikola', 'Nina', 'Noemi', 'Nora', 'Norma',
        'Octawia', 'Odetta', 'Oliwia', 'Olga', 'Olimpia', 'Otylia',
        'Patrycja', 'Paulina', 'Pelagia', 'Petronela', 'Polina',
        'Pola',
        'Rachela', 'Radosława', 'Rafaela', 'Rebeka', 'Regina', 'Renata',
        'Roksana', 'Roma', 'Romana', 'Rozalia', 'Rozanna', 'Róża',
        'Sabina', 'Salomea', 'Sandra', 'Sara', 'Selena', 'Seweryna', 'Sławomira',
        'Sonia', 'Stanisława', 'Stefania', 'Stella', 'Sylwana', 'Sylwia',
        'Tamara', 'Teodora', 'Teofila', 'Teresa', 'Tola',
        'Urszula',
        'Wanda', 'Waleria', 'Wendy', 'Weronika', 'Wiesława',
        'Wioleta', 'Wioletta', 'Wirginia', 'Wisława',
        'Yolanda',
        'Zenobia', 'Zofia', 'Zoja', 'Zuzanna',
        'Żaneta', 'Żywia',
        'Świętosława',
    }

    # POPULARNE polskie nazwiska (600+)
    POLISH_SURNAMES = {
        'Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński',
        'Lewandowski', 'Zieliński', 'Szymański', 'Woźniak', 'Dąbrowski',
        'Kozłowski', 'Jankowski', 'Mazur', 'Wojciechowski', 'Kwiatkowski',
        'Krawczyk', 'Kaczmarek', 'Piotrowski', 'Grabowski', 'Pawłowski',
        'Michalski', 'Nowakowski', 'Nowicki', 'Adamczyk', 'Dudek', 'Zając',
        'Wieczorek', 'Jabłoński', 'Król', 'Majewski', 'Olszewski', 'Jaworski',
        'Wróbel', 'Malinowski', 'Pawlak', 'Witkowski', 'Walczak', 'Stępień',
        'Górski', 'Rutkowski', 'Michalak', 'Sikora', 'Ostrowski', 'Baran',
        'Duda', 'Szewczyk', 'Tomaszewski', 'Pietrzak', 'Marciniak', 'Wróblewski',
        'Zalewski', 'Jakubowski', 'Jasiński', 'Zawadzki', 'Sadowski', 'Bąk',
        'Chmielewski', 'Włodarczyk', 'Borkowski', 'Czarnecki', 'Sawicki',
        'Sokołowski', 'Urbański', 'Kubiak', 'Maciejewski', 'Szczepański',
        'Kucharski', 'Wilk', 'Kalinowski', 'Lis', 'Mazurek', 'Wysocki',
        'Adamski', 'Kaźmierczak', 'Wasilewski', 'Sobczak', 'Czerwiński',
        'Andrzejewski', 'Cieślak', 'Głowacki', 'Zakrzewski', 'Kołodziej',
        'Sikorski', 'Krajewski', 'Gajewski', 'Szymczak', 'Szulc', 'Baranowski',
        'Laskowski', 'Brzeziński', 'Makowski', 'Ziółkowski', 'Przybylski',
        'Domański', 'Borowski', 'Czajkowski', 'Sosnowski', 'Lewicki',
        'Chojnacki', 'Kucharczyk', 'Krupa', 'Kowal', 'Janik',
        'Adamiak', 'Antczak', 'Banaś', 'Banaszek', 'Bartkowiak', 'Bednarczyk',
        'Bednarek', 'Bednarski', 'Bielawski', 'Bielecki', 'Bielski', 'Białek',
        'Bochenek', 'Bogucki', 'Bogusz', 'Bogusławski', 'Bojarski', 'Borek',
        'Boruta', 'Brzozowski', 'Buczek', 'Buczyński', 'Budzyński',
        'Bukowski', 'Burda', 'Cebula', 'Chmiel', 'Choiński', 'Chudzik',
        'Cieśla', 'Cybulski', 'Cymański', 'Czaja', 'Czajka', 'Czapla',
        'Czarny', 'Czekaj', 'Czyż', 'Dębski', 'Dobrowolski',
        'Domagała', 'Drąg', 'Drozd', 'Dybek', 'Dymek',
        'Dziedzic', 'Falkowski', 'Fila', 'Filipek', 'Filipiak', 'Filipowicz',
        'Florczak', 'Florek', 'Frankowski', 'Furtak', 'Furman',
        'Gajda', 'Gajos', 'Garbacik', 'Garbacz', 'Gawron', 'Gawroński',
        'Gąsiorek', 'Glinka', 'Głąbka', 'Godlewski', 'Gorczyca',
        'Gosk', 'Grabarczyk', 'Granczak', 'Graczyk', 'Grochowski', 'Grzelak',
        'Grzelczyk', 'Grzybek', 'Grzybowski', 'Gut', 'Guzik',
        'Helminiak', 'Hennig', 'Hertel', 'Hofman', 'Hołubowicz',
        'Iwański', 'Jackowski', 'Jagielski', 'Jagodziński', 'Jakubczyk',
        'Jakubiec', 'Janas', 'Janiak', 'Janicki', 'Jankowiak',
        'Janocha', 'Janowicz', 'Jarmoluk', 'Jarosz', 'Jaroszewicz',
        'Jasiek', 'Jaśkiewicz', 'Jelinek', 'Jendrzejczyk', 'Jeziorski',
        'Jeż', 'Jędrzejczak', 'Jędrzejczyk', 'Jędrzejewski', 'Józefowicz',
        'Juchnik', 'Juraszek', 'Jurczak', 'Jurkiewicz',
        'Kacprzak', 'Kaczanowski', 'Kaczor', 'Kajdan',
        'Kamel', 'Kania', 'Kaniewski', 'Kapica', 'Karaś', 'Karczewski',
        'Karcz', 'Karwowski', 'Kasprzak', 'Kawecki', 'Kawiak', 'Kawka',
        'Kępa', 'Kępiński', 'Kępka', 'Kędzia', 'Kędziora', 'Kędzierski',
        'Kica', 'Kiełbasa', 'Kierczak', 'Kilar', 'Kindek',
        'Klapacz', 'Klatka', 'Klepacz', 'Klimas', 'Klimaszewski',
        'Klimczak', 'Klimek', 'Kłak', 'Kłosiński', 'Kłos',
        'Kmiecik', 'Kmieć', 'Knapczyk', 'Knapik', 'Kobus',
        'Koc', 'Kochan', 'Kogut', 'Kolasa', 'Komorowski',
        'Konieczny', 'Konopka', 'Korab', 'Kornecki', 'Korol',
        'Kosek', 'Kosiba', 'Kosiński', 'Kosiorek',
        'Koszela', 'Kościelniak', 'Kościuk', 'Kowalik', 'Kowalska',
        'Kowalewski', 'Kowalewicz', 'Kozak', 'Kozieł', 'Kozioł', 'Koźmiński',
        'Krasnodębski', 'Krawiec', 'Krempa', 'Krukowski', 'Kruk', 'Krupiński',
        'Krupski', 'Kruszewski', 'Kubacki', 'Kubala', 'Kubiczek', 'Kucharek',
        'Kuczyński', 'Kufel', 'Kulesza', 'Kulig', 'Kulik', 'Kulpa',
        'Kumor', 'Kunicki', 'Kupiec', 'Kurek', 'Kurkowski',
        'Kustra', 'Kuźma', 'Kuźniak', 'Kwaśniak', 'Kwiatek',
        'Kwiecień',
        'Lasocki', 'Latkowski', 'Lechicki', 'Ledwoń', 'Lenartowicz',
        'Lesiak', 'Leszczyński', 'Leśniak', 'Leśnik', 'Leśniewski', 'Leśniewicz',
        'Lewandowicz', 'Liber', 'Liszka', 'Łach', 'Łapiński', 'Łaszewski',
        'Łazarz', 'Łątkowski', 'Łoboda', 'Łoś',
        'Łuczak', 'Łuczyński', 'Łukasiewicz', 'Łukasik', 'Łukaszczyk',
        'Łukaszewski', 'Łukomski', 'Łysiak',
        'Mach', 'Maciaszek', 'Maciąg', 'Maciejak',
        'Maciejka', 'Madejski', 'Magiera', 'Majcher', 'Majchrzak',
        'Majchrowicz', 'Majkowski', 'Maliński', 'Małachowski', 'Małecki',
        'Mańkowski', 'Markiewicz', 'Marek', 'Marczak', 'Markowski',
        'Maślak', 'Maślanka', 'Matecki', 'Matejka', 'Matuszak', 'Matuszewski',
        'Mazurkiewicz', 'Mądry', 'Mendel', 'Michalec',
        'Mielczarek', 'Mielczarski', 'Mielczyński',
        'Mikulski', 'Mikulec', 'Mikus', 'Milewski', 'Mizera', 'Mleczko',
        'Mokrzycki', 'Molenda', 'Morawski', 'Motyka', 'Mrowiec', 'Mróz',
        'Mrugała', 'Mucha', 'Murawski', 'Myszka',
        'Nadolski', 'Napiórkowski', 'Niemczyk', 'Niemiec',
        'Nizioł', 'Nowaczyk', 'Nowy', 'Ochman',
        'Ogórek', 'Okoń', 'Okrasa', 'Olejak', 'Olejarczyk', 'Olejnik',
        'Olejniczak', 'Olesik', 'Orłowski', 'Orzeł', 'Osiński', 'Osowski',
        'Ożóg', 'Ożga',
        'Pakulski', 'Palka', 'Panek', 'Papież', 'Papuga',
        'Parol', 'Pasieka', 'Pasternak', 'Patyk',
        'Pawelec', 'Pawlik', 'Pawliński', 'Pawluk',
        'Pelc', 'Pełka', 'Pęcek', 'Pęczak',
        'Pęksa', 'Pietras', 'Pietrasik', 'Pietraszewski', 'Pietrzykowski',
        'Pilarczyk', 'Pilarski', 'Pilch', 'Piłat', 'Pinkowski',
        'Pionek', 'Piotrkowski', 'Piskorski', 'Pisarczyk', 'Pisarek',
        'Plichta', 'Pluciński', 'Pluta', 'Płatek', 'Płonka',
        'Podgórski', 'Pogorzelski', 'Polański', 'Poniedziałek',
        'Popek', 'Popiel', 'Poprawa', 'Porębski', 'Potocki',
        'Pożoga', 'Prokop', 'Próchnik',
        'Przybyłowski', 'Przybyła', 'Przybysz',
        'Raczyk', 'Radecki', 'Radkiewicz', 'Rakowski', 'Rapacz',
        'Rataj', 'Robak',
        'Rogalski', 'Rogala', 'Rogowski', 'Romanowski', 'Romański',
        'Roszczyk', 'Rożek', 'Różański', 'Rudawski', 'Ruda',
        'Rudnicki', 'Rusek', 'Rusin', 'Rusiński',
        'Ryba', 'Rybak', 'Rycerz', 'Rychter',
        'Ryniec', 'Ryś', 'Rzepecki', 'Rzeźnik',
        'Sajdak', 'Sakwa', 'Salamon', 'Sałata',
        'Sandecki', 'Sas', 'Sasin', 'Schiller',
        'Sędziwy', 'Sergiusz', 'Seńkowski',
        'Sidor', 'Sienkiewicz', 'Sieracki', 'Sieradzki',
        'Sila', 'Siwy', 'Skiba', 'Skibiński', 'Skoczek',
        'Skowron', 'Skowroński', 'Skrzypczak', 'Skrzypiec', 'Skrzypek',
        'Sławiński', 'Słomka', 'Smolnik', 'Smyk',
        'Sobczyk', 'Sobera', 'Sobierajski', 'Sobieski', 'Sobocki', 'Sobol',
        'Sobota', 'Sokal', 'Sołtys', 'Sołtysiak',
        'Sosulski', 'Sowa', 'Stachowicz', 'Stachowiak', 'Stachura',
        'Staniszewski', 'Stankiewicz', 'Stańczak', 'Stańczyk', 'Staszek',
        'Staszewski', 'Stefański', 'Stocki', 'Stokłosa', 'Stolarz', 'Stolarczyk',
        'Stopa', 'Strzelczyk', 'Strzelecki', 'Strzelec', 'Suchocki',
        'Sułek', 'Surma', 'Suwała',
        'Szafraniec', 'Szafarski', 'Szczepaniak',
        'Szczerba', 'Szczygieł', 'Szczygielski', 'Szewczak',
        'Szlachta', 'Szmidt', 'Szostak', 'Szostakowski',
        'Szuba', 'Szuber', 'Szumacher',
        'Szyc', 'Szymanowski', 'Szyszka', 'Szyszko',
        'Ślęczka', 'Ślęzak', 'Śliwa', 'Śliwiński', 'Śpiewak', 'Świątek',
        'Świątkowski', 'Świder', 'Świerczek', 'Świetlik',
        'Tabaka', 'Talaga', 'Talar', 'Targosz', 'Tarka', 'Tarnowski', 'Tatara',
        'Tomala', 'Tomanek', 'Tomaszczyk',
        'Tomaszek', 'Tomczak', 'Tomczyk', 'Topolski',
        'Trzciński', 'Trzeciak', 'Tulik',
        'Twardochleb', 'Tworek', 'Tyczyński', 'Tyszkiewicz',
        'Urbaniak', 'Urbanowicz', 'Urban', 'Walczuk', 'Walkowiak', 'Walkowski',
        'Wałach', 'Warda', 'Wąsik', 'Werner', 'Wesołowski',
        'Wieczerza', 'Wielgus', 'Wielgo', 'Wiernicki', 'Wiernik',
        'Więcek', 'Więcław', 'Wilczyński',
        'Wiśnia', 'Wiśniarski', 'Wiśniowski',
        'Witczak', 'Witek', 'Witkiewicz',
        'Włoch', 'Wnęk', 'Wojnar', 'Wojewoda', 'Wojtas', 'Wojtczak',
        'Wojtkowiak', 'Wolicki', 'Wolski', 'Woźnica',
        'Wozniak', 'Wójtowicz', 'Wróblik', 'Wycisk',
        'Wysocka',
        'Zabłocki', 'Zaborski', 'Zacharko', 'Zachariasz',
        'Zagórski', 'Zając', 'Zaorski', 'Zapała',
        'Zarych', 'Zaręba', 'Zarzycki',
        'Zawalski', 'Zawiślak', 'Zawisza', 'Zborowski', 'Zdanowski',
        'Zdrojewski', 'Zelek', 'Zięba',
        'Ziętek', 'Zmuda', 'Zubrzycki', 'Zych',
        'Zygmunt', 'Żak', 'Żebrowski', 'Żelazo', 'Żelichowski',
        'Żmuda', 'Żuk', 'Żur', 'Żurek', 'Żurowski', 'Żyła',
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

    def _is_surname_form(self, name):
        """Sprawdź czy słowo wygląda jak nazwisko (formy odmienne)"""
        # Bazowe nazwiska w słowniku
        if name in self.POLISH_SURNAMES:
            return True

        # Formy odmienione (Kowalskiego, Kowalskiemu, Kowalską itp.)
        # Sprawdź czy końcówka pasuje do typowych form polskich nazwisk
        base_candidates = []
        if name.endswith('skiego') or name.endswith('ckiego'):
            base_candidates.append(name[:-3] + 'i')  # Kowalskiego -> Kowalski
        elif name.endswith('skiemu') or name.endswith('ckiemu'):
            base_candidates.append(name[:-3] + 'i')
        elif name.endswith('skim') or name.endswith('ckim'):
            base_candidates.append(name[:-1] + 'i')
        elif name.endswith('ską') or name.endswith('cką'):
            base_candidates.append(name[:-1] + 'a')
        elif name.endswith('skiej') or name.endswith('ckiej'):
            base_candidates.append(name[:-3] + 'a')
        elif name.endswith('skie') or name.endswith('ckie'):
            base_candidates.append(name[:-1] + 'i')

        for base in base_candidates:
            if base in self.POLISH_SURNAMES:
                return True

        # Typowe końcówki nazwisk polskich
        surname_suffixes = ('ski', 'cki', 'ska', 'cka', 'icz', 'wicz', 'iak', 'yk',
                            'ak', 'ek', 'czyk', 'or', 'on', 'arz', 'erz')
        if any(name.endswith(s) for s in surname_suffixes) and len(name) >= 4:
            return True

        return False

    def _normalize_first_name(self, name):
        """Zwróć bazową formę imienia (np. Janowi -> Jan)"""
        all_names = self.POLISH_NAMES_MALE | self.POLISH_NAMES_FEMALE

        if name in all_names:
            return name

        # Próby form odmienionych
        candidates = []
        # Jana -> Jan
        if len(name) > 3 and name[-1] == 'a':
            candidates.append(name[:-1])
        # Janowi -> Jan
        if name.endswith('owi'):
            candidates.append(name[:-3])
        # Janem -> Jan
        if name.endswith('em'):
            candidates.append(name[:-2])
        # Anny -> Anna
        if name.endswith('y'):
            candidates.append(name[:-1] + 'a')
        # Annie -> Anna
        if name.endswith('ie'):
            candidates.append(name[:-2] + 'a')

        for c in candidates:
            if c in all_names:
                return c
        return None

    def extract_persons(self, text):
        """Wyłapuj osoby z imienia + nazwiska z walidacją + confidence"""
        persons = []
        all_names = self.POLISH_NAMES_MALE | self.POLISH_NAMES_FEMALE

        # Wzorzec: Imię + Nazwisko (z dużej litery)
        pattern = re.compile(
            r'\b([A-ZŁŻŚĆŃÓĄĘ][a-zżółćńąęś]+)\s+([A-ZŁŻŚĆŃÓĄĘ][a-zżółćńąęś]+(?:-[A-ZŁŻŚĆŃÓĄĘ][a-zżółćńąęś]+)?)\b'
        )

        for match in pattern.finditer(text):
            first_name = match.group(1)
            last_name = match.group(2)

            # Sprawdz czy to imie (lub forma odmienna)
            normalized_first = first_name if first_name in all_names else self._normalize_first_name(first_name)
            if not normalized_first:
                continue

            # Confidence score
            confidence = 0.5
            if first_name in all_names:
                confidence += 0.25
            if self._is_surname_form(last_name):
                confidence += 0.25
            if last_name in self.POLISH_SURNAMES:
                confidence = min(confidence + 0.1, 1.0)

            gender = 'M' if normalized_first in self.POLISH_NAMES_MALE else 'F'

            persons.append({
                'first_name': first_name,
                'normalized_first_name': normalized_first,
                'last_name': last_name,
                'gender': gender,
                'full_name': f"{first_name} {last_name}",
                'confidence': round(confidence, 2),
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
