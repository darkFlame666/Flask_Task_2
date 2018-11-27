from flask import Flask, session, render_template, redirect, request, json, url_for, abort
import os
from functools import wraps
import uuid
import redis as redis
import datetime
import jwt
from pathlib import Path

redis = redis.Redis()
app = Flask(__name__)
app.secret_key = b'35dvgy8i(UHoiawu hftvd9'
app.jwt_secret_key = 'SecretKey'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
app.config.update(
    #SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_TYPE='redis'
)
app.upload_path = Path(os.path.join(APP_ROOT, 'uploads'))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'current_user' not in session:
            abort(401)
        if redis.get(session['current_user']) is None:
            abort(401)
        return f(*args, **kwargs)
    return wrapper


with open('data.json') as jdata:
    data = json.load(jdata)
    app.users = data['users']


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('current_user'):
        return redirect(url_for('login'))
    return redirect(url_for('file_add'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        current = None
        for user in data['users']:
            if request.form['username'] == user['username'] and request.form['password'] == user['password']:
                current = user
                session['logged_in'] = True
                break
        if current:
            sid = str(uuid.uuid4())
            session['current_user'] = sid
            session['logged_in'] = True
            redis.set(session['current_user'], user['username'], ex=300)
            return redirect(url_for('home'))
        else:
            error = "Invalid Credentials. Please try again."
            return render_template('loginpg.html', error=error)
    return render_template('loginpg.html')


@app.route('/logout')
def logout():
    #session['current_user'] = None
    session['logged_in'] = None
    redis.delete(session['current_user'])
    session.pop('current_user', None)
    session.clear()
    return redirect(url_for('login'))


@app.route("/list", methods=['GET', 'POST'])
@login_required
def list():
    redis.expire(session['current_user'], time=300)
    user_path = app.upload_path.joinpath(redis.get(session['current_user']).decode('utf-8')).resolve()
    files = []
    for filename in os.listdir(str(user_path)):
        data = []
        data.append(filename)
        data.append("/download/" + filename)
        data.append(("/delete/" + filename))
        files.append(data)

    tokens = {}
    return render_template('list.html', user=redis.get(session['current_user']).decode('utf-8'), files=files, tokens=tokens)


@app.route('/upload', methods=['GET', 'POST'])
def file_add():
    #redis.expire(session['current_user'], time=50)
    user_path = app.upload_path.joinpath(redis.get(session['current_user']).decode()).resolve()
    files = [x.name for x in user_path.glob('**/*') if x.is_file()]
    files_len = len(files)
    token = creating_token("allow", 3000).decode('utf-8')
    return render_template('upload.html', files_len=files_len, token=token)


def creating_token(object, expiration):
    payload = { "user" : redis.get(session['current_user']).decode('utf-8'),
                "file" : object,
                "exp"  : (datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration))}
    return jwt.encode(payload, app.jwt_secret_key, algorithm='HS256')




if __name__ == '__main__':
    app.run(debug=True, port=5001)
