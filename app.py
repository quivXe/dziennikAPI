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

def check_cookies(render_template_args):
    
    
    # theme
    theme_cookie = request.cookies.get('theme')
    if theme_cookie is None:
        theme_link = url_for('static', filename='{}.css'.format(default_theme))
    else:
        theme_link = url_for('static', filename='{}.css'.format(theme_cookie))
    
    # create template
    template =  render_template(
        'index.html',
        theme_link=theme_link,
        lessons=render_template_args['lessons'],
        timetable=render_template_args['timetable'],
        tests=render_template_args['tests'],
        messages=render_template_args['messages'],
        message=render_template_args['message']
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

# when vulcan session will end
@app.errorhandler(json.JSONDecodeError)
def error(e):
    return redirect('/login')
    
@app.route('/login', methods=['GET', 'POST'])
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

@app.route("/")
def main_page():
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:
        return check_cookies({
            'lessons': False,
            'timetable': False,
            'tests': False,
            'messages': False,
            'message': False
            })
    else:
        return redirect('/login')
    
@app.route('/oceny/<semestr>')
def grades(semestr):
    
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:
        return check_cookies({
            'lessons': interpreter.get_all_grades(semestr),
            'timetable': False,
            'tests': False,
            'messages': False,
            'message': False
            })
    else:
        return redirect('/login')

@app.route('/planlekcji')
def plan_lekcji():
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:    
        if request.cookies.get('date_offset') is None:
            offset = 0
        else:
            offset = int(request.cookies.get('date_offset'))
        
        return check_cookies({
            'lessons': False,
            'timetable': interpreter.get_timetable(offset),
            'tests': False,
            'messages': False,
            'message': False
            })
    else:
        return redirect('/login')
    

@app.route('/sprawdziany')
def tests():
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:
        if request.cookies.get('date_offset') is None:
            offset = 0
        else:
            offset = int(request.cookies.get('date_offset'))
            
        return check_cookies(
            {
                'lessons': False,
                'timetable': False,
                'tests': interpreter.get_tests(offset),
                'messages': False,
                'message': False
                })
    else:
        return redirect('/login')

@app.route('/wiadomosci')
def messages():
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:
        if request.cookies.get('messages_date_offset') is None:
            offset = -30
        else:
            offset = int(request.cookies.get('messages_date_offset'))
            
        return check_cookies(
            {
                'lessons': False,
                'timetable': False,
                'tests': False,
                'messages': interpreter.get_messages(offset),
                'message': False
            })
    else:
        return redirect('/login')
 
@app.route('/wiadomosci/<message_id>')
def message(message_id):
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:
        return check_cookies(
            {
                'lessons': False,
                'timetable': False,
                'tests': False,
                'messages': False,
                'message': interpreter.get_message(message_id)
                })
    else:
        return redirect('/login')
    
@app.route('/newsession')
def new_session():
    global interpreter
    
    interpreter = sessions.verify(
            request.cookies.get('session_id'),
            request.cookies.get('username'),
            request.cookies.get('password')
        )
    if interpreter:
        return redirect('/')
    else:
        return redirect('/login')
         
@app.route('/set_cookie/<name>/<value>/<page>')
@app.route('/set_cookie/<name>/<value>/')
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
    response.set_cookie(name, value)
    return response

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)
