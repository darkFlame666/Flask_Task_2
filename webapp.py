from flask import Flask, session, render_template, redirect, request, json, url_for
import os
import uuid
import redis
r = redis.Redis();

app = Flask(__name__)
app.secret_key = b'35dvgy8i(UHoiawu hftvd9'
app.jwt_secret_key = 'SecretMisteriousKey'

@app.route('/')
def hello_world():
    return 'Hello World!'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app.config.update(
    #SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True
)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        if login_check(request.form['username'], request.form['password']):
            sid = str(uuid.uuid4())
            session['user_sid'] = sid
            session['username'] = request.form['username']

            return redirect(url_for('home'))
        else:
            error = "Invalid Credentials. Please try again."
    return render_template('loginpg.html', error=error)


def login_check(username, password):
    with open('data.json', 'r') as jdata:
        data = json.load(jdata)
    for row in data['users']:
        if row['username'] == username:
            if row['password'] == password:
                return True
    return False


if __name__ == '__main__':
    app.run()
