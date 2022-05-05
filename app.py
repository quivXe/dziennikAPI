from flask import Flask, render_template, url_for, request, make_response, redirect
from datetime import datetime
from modules.interpreter import Interpreter
from modules.sessions import Sessions
import json
from modules.key_manager import *
from cryptography.fernet import Fernet

app = Flask(__name__)

sessions = Sessions()
default_theme = 'green-black'
fernet = Fernet(Fernet.generate_key())

def check_cookies(*args, **kwargs):
    
    templates_dict = {
            'lessons': False,
            'timetable': False,
            'tests': False,
            'messages': False,
            'message': False,
            'addendance': False,
            'addendance_stats': False,
            'new_grades': False
        }
    if args:
        templates_dict[args[0]] = args[1]
    
    # theme
    theme_cookie = request.cookies.get('theme')
    if theme_cookie is None:
        theme_link = url_for('static', filename='themes/{}.css'.format(default_theme))
        logo_link = url_for('static', filename='images/{}_logo.svg'.format(default_theme.split('-')[0]))
    else:
        theme_link = url_for('static', filename='themes/{}.css'.format(theme_cookie))
        logo_link = url_for('static', filename='images/{}_logo.svg'.format(theme_cookie.split('-')[0]))
    
    # create template
    template =  render_template(
            'index.html',
            theme_link=theme_link,
            logo_link=logo_link,
            lessons=templates_dict['lessons'],
            timetable=templates_dict['timetable'],
            tests=templates_dict['tests'],
            messages=templates_dict['messages'],
            message=templates_dict['message'],
            addendance=templates_dict['addendance'],
            addendance_stats=templates_dict['addendance_stats'],
            new_grades=templates_dict['new_grades']
        )
    
    
    
    # theme
    if theme_cookie is None:
        template = make_response(template)
        template.set_cookie('theme', default_theme)
    
    # date offset
    date_offset_cookie = request.cookies.get('date_offset')
    if date_offset_cookie is None:
        template = make_response(template)
        template.set_cookie('date_offset', '0')
        
    
    # messages date offset
    messages_date_offset_cookie = request.cookies.get('messages_date_offset')
    if messages_date_offset_cookie is None:
        template = make_response(template)
        template.set_cookie('messages_date_offset', '-30')
        
    return template

def verify_session(func):
    def wrapper(*args, **kwargs):
        interpreter = sessions.verify(
                request.cookies.get('session_id'),
                request.cookies.get('username'),
                request.cookies.get('password')
            )
        
        if interpreter:
            kwargs['interpreter'] = interpreter
            val = func(*args, **kwargs)
            
        else:
            val = redirect('/login')
        return val
    
    return wrapper

# when vulcan session will end
@app.errorhandler(json.JSONDecodeError)
def error(e):
    return redirect('/login')
    
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    
    if request.method == 'GET':
        if request.cookies.get('username') is not None and request.cookies.get('password') is not None:
            username = request.cookies.get('username')
            enc_password = request.cookies.get('password')
            dec_password = decrypt(fernet, enc_password)
            
            interpreter = Interpreter(username, dec_password)
            
            if interpreter.api.logged_in:
                s_id = sessions.add_new_session(interpreter, username, enc_password)
                response = redirect('/')
                response.set_cookie('session_id', str(s_id))
                return response
        
        return render_template('login.html')
    
    elif request.method == 'POST':
        username = request.form['username']
        dec_password = request.form['password']
        
        interpreter = Interpreter(username, dec_password)
        
        if interpreter.api.logged_in:
            enc_password = encrypt(fernet, dec_password)
            response = make_response(redirect('/'))
            response.set_cookie('username', username, expires=datetime(2026, 1, 1))
            response.set_cookie('password', enc_password, expires=datetime(2026, 1, 1))
            
            s_id = sessions.add_new_session(interpreter, username, enc_password)
            response.set_cookie('session_id', str(s_id))
            
            return response
        
        return render_template('login.html', wrong_password=True)

@app.route("/", endpoint='main_page')
@verify_session
def main_page(*args, **kwargs):

    interpreter = kwargs['interpreter']
    return check_cookies('new_grades', interpreter.get_new_grades())

@app.route('/oceny/<semestr>', endpoint='grades')
@verify_session
def grades(semestr, *args, **kwargs):

    interpreter = kwargs['interpreter']
    return check_cookies('lessons', interpreter.get_all_grades(semestr))

@app.route('/planlekcji', endpoint='plan_lekcji')
@verify_session
def plan_lekcji(*args, **kwargs):

    interpreter = kwargs['interpreter']
    if request.cookies.get('date_offset') is None:
        offset = 0
    else:
        offset = int(request.cookies.get('date_offset'))
    
    return check_cookies('timetable', interpreter.get_timetable(offset))

@app.route('/sprawdziany', endpoint='tests')
@verify_session
def tests(*args, **kwargs):

    interpreter = kwargs['interpreter']
    if request.cookies.get('date_offset') is None:
        offset = 0
    else:
        offset = int(request.cookies.get('date_offset'))
        
    return check_cookies('tests', interpreter.get_tests(offset))

@app.route('/wiadomosci', endpoint='messages')
@verify_session
def messages(*args, **kwargs):

    interpreter = kwargs['interpreter']
    if request.cookies.get('messages_date_offset') is None:
        offset = -30
    else:
        offset = int(request.cookies.get('messages_date_offset'))
        
    return check_cookies('messages', interpreter.get_messages(offset))
 
@app.route('/wiadomosci/<message_id>', endpoint='message')
@verify_session
def message(message_id, *args, **kwargs):

    interpreter = kwargs['interpreter']
    return check_cookies('message', interpreter.get_message(message_id))

@app.route('/frekwencja', endpoint='addendance')
@verify_session
def addendance(*args, **kwargs):
    
    interpreter = kwargs['interpreter']
    if request.cookies.get('date_offset') is None:
        offset = 0
    else:
        offset = int(request.cookies.get('date_offset'))
        
    return check_cookies('addendance', interpreter.get_addendance(offset))
         
@app.route('/frekwencja/statystyki', endpoint='addendance_stats')
@verify_session
def addendance_session(*args, **kwargs):
    
    interpreter = kwargs['interpreter']
    
    return check_cookies('addendance_stats', interpreter.get_addendance_stats())

@app.route('/set_cookie/<name>/<value>/<page>', endpoint='cookie_page')
@app.route('/set_cookie/<name>/<value>/', endpoint='cookie_page')
def cookie_page(name, value, page=''):
    page = '/' + page.replace('-', '/')
    
    if name == 'date_offset':
        if value != '0':
            value = int(value)
            value += int(request.cookies.get('date_offset'))
            value = str(value)
    
    elif name == 'messages_date_offset':
        value = str(int(value) + int(request.cookies.get('messages_date_offset')))
        

    response = make_response(redirect(page))
    if name == 'theme':
        response.set_cookie(name, value, expires=datetime(2026, 1, 1))
    else:
        response.set_cookie(name, value)
    return response

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)