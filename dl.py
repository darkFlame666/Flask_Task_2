from flask import Flask, request, session, send_from_directory, stream_with_context, abort
import jwt
import os
import redis as redis
from werkzeug.utils import secure_filename, redirect
from pathlib import Path
#from webapp import login_required

app = Flask(__name__, static_url_path='/static/uploads')
app.secret_key = b'0293jr i(UHoiawu hft923'
app.jwt_secret_key = 'SecretKey'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
app.upload_path = Path(os.path.join(APP_ROOT, 'static/uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.update(dict(
    #SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
))
cwd = os.path.dirname(os.path.realpath(__file__))
red = redis.StrictRedis(host='localhost', port=6379, db=0)
redis = redis.Redis()


@app.route("/upload", methods=['POST', 'GET'])
#@login_required
@stream_with_context
def upload():
    token = request.form['token']
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return abort(401)
    user_path = app.upload_path.joinpath(user['user']).resolve()
    files = [x.name for x in user_path.glob('**/*') if x.is_file()]
    files_len = len(files)
    if files_len >= 5:
        return redirect('http://127.0.0.1:5001/upload')
    if 'file' not in request.files:
        return redirect('http://127.0.0.1:5001/upload')
    f = request.files['file']
    filename = secure_filename(f.filename)
    user_path.mkdir(parents=True, exist_ok=True)
    q = user_path / filename
    f.save(str(q))
#   redis.set(session['notif'], True, ex=2)
  #  red.publish('notifications', 'New file has been added to shared  files!')
    return redirect('http://127.0.0.1:5001/list')


@app.route("/download/<string:token>")
def download(token):
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return os.abort(401)
    user_path = app.upload_path.joinpath(user['user']).resolve()
    q = user_path / user['file']
    if q.exists():
        return send_from_directory(user_path, user['file'])
    else:
        os.abort(404)


@app.route('/delete/<string:token>')
def delete(token):
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return os.abort(401)
    user_path = app.upload_path.joinpath(user['user']).resolve()
    q = user_path / user['file']
    if q.exists():
        os.remove(q)
        return redirect('http://127.0.0.1:5001/list')
    else:
        os.abort(404)


if __name__ == "__main__":
    app.run(debug = True, port = 5002)