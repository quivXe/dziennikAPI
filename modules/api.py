import requests
from bs4 import BeautifulSoup
import json


class Api:

    shortcuts = {
        'wszystkie': {'fullname': 'Wszystkie'},
        'religia': {'fullname': 'Religia'},
        'wos': {'fullname': 'Wiedza o społeczeństwie'},
        'informatyka': {'fullname': 'Informatyka'},
        'praktyka zawodowa': {'fullname': 'Praktyka zawodowa'},
        'edb': {'fullname': 'Edukacja dla bezpieczeństwa'},
        'kaszubski2': {'fullname': 'Historia i kultura kaszubska'},
        'angielski zaw.': {'fullname': 'Język angielski w branży informatycznej'},
        'podstawy informatyki': {'fullname': 'podstawy informatyki'},
        'polski': {'fullname': 'Język polski'},
        'ang': {'fullname': 'Język angielski'},
        'hiszpanski': {'fullname': 'Język hiszpański'},
        'kaszubski': {'fullname': 'Język regionalny – kaszubski'},
        'historia': {'fullname': 'Historia'},
        'matma': {'fullname': 'Matematyka'},
        'chemia': {'fullname': 'Chemia'},
        'biologia': {'fullname': 'Biologia'},
        'geografia': {'fullname': 'Geografia'},
        'wf': {'fullname': 'Wychowanie fizyczne'},
        'wychowawcza': {'fullname': 'Zajęcia z wychowawcą'},
        'so': {'fullname': 'Systemy operacyjne'},
        'utk': {'fullname': 'Urządzenia techniki komputerowej'},
        'wiai': {'fullname': 'Witryny i aplikacje internetowe'},
        'sbd': {'fullname': 'Systemy baz danych'},
        'aso': {'fullname': 'Administracja systemami operacyjnymi'},
        'eutk': {'fullname': 'Eksploatacja urządzeń techniki komputerowej'},
        'ksiops': {'fullname': 'kompetencje społeczne i organizacja pracy zespołów'},
        'lsk': {'fullname': 'lokalne sieci komputerowe'},
        'mielsk': {'fullname': 'montaż i eksploatacja lokalnych sieci komputerowych'},
        'tsiai': {'fullname': 'tworzenie stron i aplikacji internetowych'},
        'pbd': {'fullname': 'projektowanie baz danych'},
    }
    fullname_to_shortcut = {}
    for key in shortcuts:
        fullname_to_shortcut[shortcuts[key]['fullname']] = key
    fullname_to_shortcut['Zachowanie'] = 'wychowawcza'

    test_type_ids = {
            '1': 'sprawdzian',
            '2': 'kartkowka',
            '3': 'praca klasowa'
        }

    def __init__(self, username, password, update=False, school_name='puck'):
        self.school_name = school_name
        self.funny_number_TODO = '024049'
        self.login_url_TODO = 'https://cufs.vulcan.net.pl/puck/Account/LogOn?ReturnUrl=%2Fpuck%2FFS%2FLS%3Fwa%3Dwsignin1.0%26wtrealm%3Dhttps%253a%252f%252fuonetplus.vulcan.net.pl%252fpuck%252fLoginEndpoint.aspx%26wctx%3Dhttps%253a%252f%252fuonetplus.vulcan.net.pl%252fpuck%252fLoginEndpoint.aspx'
        
        if update:
            self.session = requests.Session()

            self.log_in(username, password)
            
            if self.logged_in:
                user = self.get_user_info()
    
                self.user_id = str(user['IdUczen'])
                self.grade_book_id = str(user['IdDziennik'])
                self.year = str(user['DziennikRokSzkolny'])
                self.semestrs_id = {
                    '1': user['Okresy'][0]['Id'],
                    '2': user['Okresy'][1]['Id']
                }
    
                self.set_cookies()
                self.set_lessons_id()

    def log_in(self, username, password):
        # - get empty page with DATA FORM for another POST request
        #---
        data = {
        'LoginName': username,
        'Password': password
        }

        login_response = self.session.post(self.login_url_TODO, data=data)
        soup = BeautifulSoup(login_response.text, 'html.parser')
        
        if soup.title.text != 'Working...':
            self.logged_in = False
            return
        else:
            self.logged_in = True

        data = {}
        for HTML_obj_input in soup.find_all('input')[:-1]:
            data[HTML_obj_input.get('name')] = HTML_obj_input.get('value')

        # - create login cookies to access page with grades
        # ---

        access_url = 'https://uonetplus.vulcan.net.pl/' + self.school_name + '/LoginEndpoint.aspx'
        self.session.post(access_url, data=data)

    def get_user_info(self):
        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/UczenDziennik.mvc/Get'

        response = self.session.post(url)
        return json.loads(response.text)["data"][0]

    def set_cookies(self):
        for cookie in [
                    ["idBiezacyUczen", self.user_id],
                    ["idBiezacyDziennik", self.grade_book_id],
                    ["idBiezacyDziennikPrzedszkole", "0"],
                    ["idBiezacyDziennikWychowankowie", "0"],
                    ["biezacyRokSzkolny", self.year]
                ]:
            self.session.cookies.set_cookie(
                    requests.cookies.create_cookie(
                            domain="uonetplus-uczen.vulcan.net.pl",
                            name=cookie[0],
                            value=cookie[1]
                        )
                )

    def get_grades(self, semestr):
        
        semestr = str(semestr)
        if semestr not in ['1', '2']:
            return -1

        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/Oceny.mvc/Get'
        response = self.session.get(url, params={'okres': self.semestrs_id[semestr]})
        response_text = response.text

        raw_lessons_with_grades = json.loads(response_text)['data']['Oceny']
        grades = {}
        for raw_lesson in raw_lessons_with_grades:
            lesson_grades = [{
                'grade': grade_desc['Wpis'],
                'weight': int(grade_desc['Waga']),
                'description': grade_desc['NazwaKolumny'],
                'date': grade_desc['DataOceny']} for grade_desc in raw_lesson['OcenyCzastkowe']]
            # grades[self.fullname_to_shortcut[]] = {'average': raw_lesson['Srednia'], 'grades': lesson_grades}
            lesson = raw_lesson['Przedmiot']
            if lesson in self.fullname_to_shortcut.keys():
                lesson = self.fullname_to_shortcut[lesson]
            grades[lesson] = {'average': raw_lesson['Srednia'], 'grades': lesson_grades}
        
        return grades
    
    def get_timetable(self, monday_iso_format):

        monday_iso_format += "T00:00:00"

        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/PlanZajec.mvc/Get'
        response = self.session.get(url, params={'data': monday_iso_format})
        response_text = response.text

        # its in rows
        raw_time_table_rows = json.loads(response_text)['data']['Rows'][1:12] # lesson starts only 7:50 - 16:15

        time_table = []
        for raw_row in raw_time_table_rows:

            row = []
            for i, raw_lesson in enumerate(raw_row):
                
                if i == 0:
                    time = raw_lesson.split('<')[1].split('>')[1]
                    row.append({'lesson': time, 'class_num': '', 'teacher': '', 'additional_info': ''})

                else:
                    soup = BeautifulSoup(raw_lesson, 'html.parser')
                    spans = soup.find_all('span')

                    if len(spans) > 0:
                        if len(spans) == 4:
                            spans = [spans[0], spans[2], spans[3]] # XD
                        
                        lesson = spans[0].string.split(' [')[0] # skip shit in [???]
                        if lesson in self.fullname_to_shortcut.keys():
                            lesson = self.fullname_to_shortcut[lesson]
                        
                        class_num = spans[1].string
                        if class_num is None:
                            class_num = ''
                        class_num = class_num.strip()
                        if len(class_num) > 0 and class_num[-1] == 'T':
                            class_num = class_num[:-1]
                            
                        teacher = spans[2].string.strip()

                        additional_info = ''
                        if len(soup.text.split('(')) > 1:

                            additional_info_from_page = soup.text.split('(')[1][:-1].lower()

                            if 'okienko' in additional_info_from_page.lower() or 'uczniowie przychodzą później' in additional_info_from_page.lower() or 'uczniowie zwolnieni do domu' in additional_info_from_page.lower():
                                additional_info = 'okienko'

                            elif 'zastępstwo' in additional_info_from_page.lower():
                                additional_info = 'zastepstwo'
                                teacher = additional_info_from_page.split(':')[1]

                            else:
                                additional_info = additional_info_from_page.lower()

                    else:
                        lesson = '-'
                        class_num = ''
                        teacher = ''
                        additional_info = ''

                    row.append({'lesson': lesson, 'class_num': class_num, 'teacher': teacher, 'additional_info': additional_info})

            time_table.append(row)

        return time_table

    def set_lessons_id(self):

        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/FrekwencjaStatystykiPrzedmioty.mvc/Get'
        response = self.session.get(url)
        response_text = response.text

        raw_lessons = json.loads(response_text)['data']
        for raw_lesson in raw_lessons:

            if raw_lesson['Nazwa'] not in self.fullname_to_shortcut.keys():
                self.fullname_to_shortcut[raw_lesson['Nazwa']] = raw_lesson['Nazwa']
                self.shortcuts[raw_lesson['Nazwa']] = {'fullname': raw_lesson['Nazwa']}

            self.shortcuts[self.fullname_to_shortcut[raw_lesson['Nazwa']]]['id'] = raw_lesson['Id']
                
    def get_addendance_stats(self, lesson): 

        if lesson not in self.shortcuts.keys():
            return -1
            

        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/FrekwencjaStatystyki.mvc/Get'
        response = self.session.get(url, params={'idPrzedmiot': self.shortcuts[lesson]['id']})
        response_text = response.text

        return json.loads(response_text)['data']['Podsumowanie']
    
    def get_addendance(self, monday_iso_format):
        
        def get_lesson_number(lesson_number):
            # XDDDDDDDDDDD
            if lesson_number == 23:
                return 9
            return lesson_number - 11
        
        categories = {1: 'present', 2: 'upsent', 4: 'late'}
        
        monday_iso_format += 'T00:00:00'
        
        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/Frekwencja.mvc/Get'
        response = self.session.get(url, params={'data': monday_iso_format, 'idTypWpisuFrekwencji': -1})
        
        raw_addendance = json.loads(response.text)['data']['Frekwencje']
        
        addendance = []
        for day in raw_addendance:
            
            raw_category = day['IdKategoria']
            if raw_category in categories.keys():
                category = categories[raw_category]
            else:
                category = raw_category
                
            raw_lesson = day['PrzedmiotNazwa']
            if raw_lesson in self.fullname_to_shortcut.keys():
                lesson = self.fullname_to_shortcut[raw_lesson]
            else:
                lesson = raw_lesson
                
            addendance.append(
                    {
                        'category': category,
                        'weekday_number': day['NrDnia'] - 1,
                        'lesson_number':  get_lesson_number(day['IdPoraLekcji']),
                        'lesson': lesson
                    }
                )
        
        return addendance
            
    def get_tests(self, monday_iso_format):

        url = 'https://uonetplus-uczen.vulcan.net.pl/' + self.school_name + '/' + self.funny_number_TODO + '/Sprawdziany.mvc/Get'
        response = self.session.get(url, params={'data': monday_iso_format, 'rokSzkolny': self.year})
        response_text = response.text

        raw_weeks = json.loads(response_text)['data'] # returns 4 weeks after including this XD
        raw_week = raw_weeks[0]['SprawdzianyGroupedByDayList'] # !! dodac obsluge wielu dni

        saved_tests = {}
        for raw_week in raw_weeks:
            raw_week = raw_week['SprawdzianyGroupedByDayList']

            monday = raw_week[0]['Data'][:10]

            this_week_tests = {}
            for raw_day in raw_week:

                date = raw_day['Data'][:10]
                raw_tests = raw_day['Sprawdziany']

                for raw_test in raw_tests:

                    lesson = raw_test['Nazwa']
                    if lesson in self.fullname_to_shortcut.keys():
                        lesson = self.fullname_to_shortcut[lesson]

                    description = raw_test['Opis']
                    
                    if date not in this_week_tests.keys():
                        this_week_tests[date] = []

                    test_type = str(raw_test['Rodzaj'])
                    if test_type in self.test_type_ids.keys():
                        test_type = self.test_type_ids[test_type]
                        
                    this_week_tests[date].append({
                        'lesson': lesson,
                        'description': description,
                        'test_type': test_type
                        })
            
            saved_tests[monday] = this_week_tests

        return saved_tests
    
    def get_messages(self, from_date, to_date):
        
        url = 'https://uonetplus-uzytkownik.vulcan.net.pl/' + self.school_name + '/Wiadomosc.mvc/GetInboxMessages'
        response = self.session.get(url, params={'dataOd': from_date + ' 00:00:00', 'dataDo': to_date + ' 00:00:00', 'page':1, 'start':0, 'limit':25})
        response_text = response.text

        raw_messages = json.loads(response_text)['data']
        
        messages = []
        for raw_message in raw_messages:
            message = {
                'id': raw_message['Id'],
                'title': raw_message['Temat'],
                'sender': raw_message['Nadawca']['Name'].split(' -')[0],
                'date': raw_message['Data']
            }
            messages.append(message)
        
        return messages
    
    def get_message_content(self, message_id):

        # XD
        url = 'https://uonetplus-uzytkownik.vulcan.net.pl/' + self.school_name + '/'
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        shit = soup.find_all('script')[0].text
        shit = [line for line in shit.split('}')[0].split('{')[1].split(',') if line.strip().startswith('antiForgeryToken') or line.strip().startswith('appGuid')]
        antiForgeryToken = shit[0].split(': ')[1][1:-1]
        appGuid = shit[1].split(': ')[1][1:-1]

        url = 'https://uonetplus-uzytkownik.vulcan.net.pl/' + self.school_name + '/Wiadomosc.mvc/GetInboxMessageDetails'
        response = self.session.post(url, data={'messageId': message_id}, headers={'x-v-appguid': appGuid, 'x-v-requestverificationtoken': antiForgeryToken})
        response_text = response.text

        # XD
        if '<!DOCTYPE html' in response_text:
            return ['', []]
        
        raw_message = json.loads(response_text)['data']

        message = {
            'content': raw_message['Tresc'],
            'attachments': [{'name': attachment['NazwaPliku'], 'url': attachment['Url']} for attachment in raw_message['Zalaczniki']]
        }
        return message
    
