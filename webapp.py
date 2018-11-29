from flask import Flask, session, render_template, redirect, request, json, url_for, abort, Response, stream_with_context, send_from_directory, make_response, jsonify
import os
from functools import wraps
import uuid
import redis as redis
import datetime
import jwt
import json
from pathlib import Path

red = redis.StrictRedis(host='localhost', port=6379, db=0)
redis = redis.Redis()

app = Flask(__name__, static_url_path='/static')
app.secret_key = b'0293jr i(UHoiawu hft923'
app.jwt_secret_key = 'SecretKey'
jwtPassword = 'secret'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
app.upload_path = Path(os.path.join(APP_ROOT, './static/uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.update(dict(
    #SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_TYPE='redis'
))
cwd = os.path.dirname(os.path.realpath(__file__))

with open('data.json') as jdata:
    data = json.load(jdata)
    app.users = data['users']


def login_required(jdata):
    @wraps(jdata)
    def wrapper(*args, **kwargs):
        if 'current_user' not in session:
            abort(401)
        if redis.get(session['current_user']) is None:
            abort(401)
        return jdata(*args, **kwargs)

    return wrapper


def creating_token(object, expiration):
    payload = {"user": redis.get(session['current_user']).decode('utf-8'),
                "file": object,
                "exp": (datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration))}
    return jwt.encode(payload, app.jwt_secret_key, algorithm='HS256')


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('current_user'):
        return redirect(url_for('login'))
    return redirect(url_for('file_add'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        current = None
        for user in data['users']:
            if request.form['username'] == user['username'] and request.form['password'] == user['password']:
                current = user
                session['logged_in'] = True
                session['notif'] = False
                break
        if current:
            sid = str(uuid.uuid4())
            session['current_user'] = sid
            session['logged_in'] = True
            session['notif'] = False
            redis.set(session['current_user'], user['username'], ex=300)
            return redirect(url_for('home'))
        else:
            error = "Invalid Credentials. Please try again."
            return render_template('loginpg.html', error=error)
    return render_template('loginpg.html')


@app.route('/logout')
def logout():
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
    user = redis.get(session['current_user']).decode('utf-8')
    files = []
    for filename in os.listdir(str(user_path)):
        data = []
        data.append(filename)
        data.append("/download/" + filename)
        data.append("/delete/" + filename)
        data.append("/static/uploads/"+user+"/"+filename)
        files.append(data)

    tokens = {}
    return render_template('list.html', user=redis.get(session['current_user']).decode('utf-8'), files=files, tokens=tokens)


@app.route("/shared", methods=['GET', 'POST'])
def shared():
    user_path = UPLOAD_FOLDER
    print(user_path)
    files = []
    for dir in os.listdir(str(user_path)):
        data = []
        data.append(dir)
        for filename in os.listdir(str(user_path)+"/"+dir):
            dat = []
            dat.append(filename)
            dat.append("/static/uploads/"+dir+"/"+filename)
            data.append(dat)
        files.append(data)
    tokens = {}
    return render_template('shared.html', files=files, tokens=tokens)


def does_users_dir_exists(username):
    return os.path.isdir(UPLOAD_FOLDER+"/"+username)


def create_user_dir(username):
    os.mkdir(UPLOAD_FOLDER+"/"+username)


@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype="text/event-stream")


@stream_with_context
def event_stream():
    if (redis.get(session['notif'])):
        session['notif'] = False
        pubsub = red.pubsub()
        pubsub.subscribe('notifications')
        for msg in pubsub.listen():
            yield 'data: %s\n\n' % 'New file has been added to shared files!'


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def file_add():
    user_path = app.upload_path.joinpath(redis.get(session['current_user']).decode()).resolve()
    if not does_users_dir_exists(redis.get(session['current_user']).decode()):
        create_user_dir(redis.get(session['current_user']).decode())
    files = [x.name for x in user_path.glob('**/*') if x.is_file()]
    files_len = len(files)
    token = creating_token("allow", 300).decode('utf-8')
    return render_template('upload.html', files_len=files_len, token=token)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
