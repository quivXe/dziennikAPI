from modules.api import Api
import datetime

black_list = ['chemia', 'wos', 'so', 'angielski zaw.', 'informatyka',
              'podstawy informatyki', 'edb', 'kaszubski2']
weekdays = [
        'Poniedziałek',
        'Wtorek',
        'Środa',
        'Czwartek',
        'Piątek'
    ]

class Interpreter:
    
    def __init__(self, username, password):
        
        self.username = username
        self.password = password
        
        self.new_session()
        
        self.grades = {'1': {}, '2': {}}

    def new_session(self):
        self.api = Api(self.username, self.password, update=True)
        
    def get_all_grades(self, semestr):
        
        if len(self.grades[semestr].keys()) == 0:
            raw_grades = self.api.get_grades(semestr)
            self.grades[semestr] = raw_grades
        
        else:
            raw_grades = self.grades[semestr]
        
        all_grades_to_display = []
        
        for lesson_name in raw_grades:
            if lesson_name in black_list:
                continue
            
            average = raw_grades[lesson_name]['average']
            grades = raw_grades[lesson_name]['grades']
            
            all_grades_to_display.append({
                    'lesson_name':lesson_name,
                    'average': average,
                    'grades': grades
                })
        
        return all_grades_to_display
    
    def get_timetable(self, offset):
        
        today = datetime.date.today()
        monday_date = today - datetime.timedelta(days=today.weekday() - (offset*7))
        
        iso_format_monday_date = monday_date.isoformat()
        raw_timetable = self.api.get_timetable(iso_format_monday_date)
        
        days = [{'day': 'Godzina', 'date': ''}]
        for i in range(5):
            current_date = monday_date + datetime.timedelta(days=i)
            days.append(
                {
                    'day':weekdays[i],
                    'date': '{}.{}'.format(
                        '{:02d}'.format(current_date.day),
                        '{:02d}'.format(current_date.month)
                    )
                }
            )
        
        timetable = {'weekdays': days, 'lessons': raw_timetable}
        
        return timetable
    
    def get_tests(self, offset):
        
        today = datetime.date.today()
        monday_date = today - datetime.timedelta(days=today.weekday() - (offset*7))
        
        iso_format_monday_date = monday_date.isoformat()
        raw_tests = self.api.get_tests(iso_format_monday_date)[iso_format_monday_date] # TODO: ogarnac zeby nie bylo pobierania nie potrzebnie tyle info (strona zwraca 4 tyg. zamiast jednego)
        
        week_dates = [monday_date + datetime.timedelta(days=days) for days in range(5)]
        days = []
        for i in range(5):
            days.append(
                {
                    'day':weekdays[i],
                    'date': '{}.{}'.format(
                        '{:02d}'.format(week_dates[i].day),
                        '{:02d}'.format(week_dates[i].month)
                        )
                }
            )
        tests = {'days': [], 'weekdays': days}
        for i, date in enumerate(week_dates):
            date = date.isoformat()
            tests['days'].append([])
            if date in raw_tests.keys():
                for test in raw_tests[date]:
                    tests['days'][i].append({'lesson': test['lesson'],
                                             'description': test['description'],
                                             'test_type': test['test_type']
                                             })
        
        return tests
    
    def get_messages(self, offset):
        today = datetime.date.today()
        tommorow = today + datetime.timedelta(days=1)
        iso_format_tommorow = tommorow.isoformat()
        
        from_date = today + datetime.timedelta(days=offset)
        iso_format_from_date = from_date.isoformat()
        
        raw_messages = self.api.get_messages(iso_format_from_date, iso_format_tommorow)
        
        raw_messages.sort(key=lambda elem: elem['date'], reverse=True)
        return raw_messages
    
    def get_message(self, message_id):
        return self.api.get_message_content(message_id)
    
    def get_addendance(self, offset):

        today = datetime.date.today()
        monday_date = today - datetime.timedelta(days=today.weekday() - (offset*7))
        
        iso_format_monday_date = monday_date.isoformat()
        raw_addendance = self.api.get_addendance(iso_format_monday_date)
        
        addendance = {
                'days': [
                    {
                        'lessons': [None for j in range(10)] # 10 lessons
                    } for i in range(5)], # 5 days
                'weekdays': weekdays
            }
        for raw_lesson in raw_addendance:
            addendance['days'][raw_lesson['weekday_number']]['lessons'][raw_lesson['lesson_number']] = {
                    'category': raw_lesson['category'],
                    'lesson': raw_lesson['lesson']
                }
        
        return addendance
    
    def get_addendance_stats(self):
        
        stats = [
            {'lesson': lesson, 'val': self.api.get_addendance_stats(lesson)} for lesson in self.api.shortcuts if lesson not in black_list
            ]
                
        return stats
            
    
    def get_new_grades(self):
        
        today = datetime.datetime.now()
        
        week_before = today - datetime.timedelta(days=7)
        
        semestr = 2 # TODO: zeby ogarnialo sie samo jaki semestr zaleznie od tego jakie polrocze
        raw_grades = self.api.get_grades(semestr)
        
        grades = []
        for lesson in raw_grades:
            for grade in raw_grades[lesson]['grades']:
                if datetime.datetime.strptime(grade['date'], '%d.%m.%Y') > week_before:
                    grades.append(
                        {
                            'lesson': lesson,
                            'grade': grade['grade'],
                            'weight': grade['weight'],
                            'date': grade['date'],
                            'description': grade['description']
                        })

        grades.sort(key=lambda item: item['date'], reverse=True)
        return grades
