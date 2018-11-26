from flask import Flask, session, render_template, redirect, request, json, url_for
import os
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
    SESSION_COOKIE_HTTPONLY=True
)
app.upload_path = Path(os.path.join(APP_ROOT, 'uploads'))
with open('data.json') as jdata:
    data = json.load(jdata)
    app.users = data['users']


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('current_user'):
        return redirect(url_for('login'))
    return render_template('upload.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        current = None
        for user in data['users']:
            if request.form['username'] == user['username'] and request.form['password'] == user['password']:
                current = user
                break
        if current:
            sid = str(uuid.uuid4())
            session['current_user'] = sid
            redis.set(session['current_user'], user['username'], ex=50)
            return redirect(url_for('home'))
        else:
            error = "Invalid Credentials. Please try again."
            return render_template('loginpg.html', error=error)
    return render_template('loginpg.html')


@app.route('/logout')
def logout():
    redis.delete(session['current_user'])
    session.pop('current_user', None)
    return redirect(url_for('login'))

@app.route("/list")
def list():
    files = get_user_files(session['current_user'])
    return render_template('list.html', files=files)


@app.route('/upload', methods=['GET', 'POST'])
def file_add():
    redis.expire(session['current_user'], time=50)
    user_path = app.upload_path.joinpath(redis.get(session['current_user']).decode()).resolve()
    files = [x.name for x in user_path.glob('**/*') if x.is_file()]
    files_len = len(files)
    token = creating_token("allow", 240).decode('utf-8')
    return render_template('upload.html', files_len=files_len, token=token)


def creating_token(object, expiration):
    payload = { "user" : redis.get(session['current_user']).decode('utf-8'),
                "file" : object,
                "exp"  : (datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration))}
    return jwt.encode(payload, app.jwt_secret_key, algorithm='HS256')


def get_user_files(username):
    filepath = UPLOAD_FOLDER+"/" +str(session.get('current_user'))
    files = []
    for filename in os.listdir(filepath):
        data=[]
        data.append(filename)
        data.append("http://127.0.0.1:5002/download/"+filename)
        data.append(("http://127.0.0.1:5002/delete/"+filename))
        files.append(data)
    return files

if __name__ == '__main__':
    app.run(debug=True, port=5001)
