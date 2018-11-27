from flask import Flask, request, session, redirect, render_template, send_from_directory, send_file, url_for, abort
import jwt
import os
from werkzeug.utils import secure_filename
from pathlib import Path
from webapp import login_required
app = Flask(__name__)
app.secret_key = b'0293jr i(UHoiawu hft923'
app.jwt_secret_key = 'SecretKey'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
app.config.update(
    #SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
app.upload_path = Path(os.path.join(APP_ROOT, 'uploads'))
JWT_ALGORITHM = 'HS384'

@app.route("/upload", methods=['POST', 'GET'])
#@login_required
def upload():
    token = request.form['token']
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return abort(401)
    user_path = app.upload_path.joinpath(user['user']).resolve()
    files = [x.name for x in user_path.glob('**/*') if x.is_file()]
    files_len = len(files)
    if files_len >=5:
        return redirect('http://127.0.0.1:5001/upload')
    if 'file' not in request.files:
        return redirect('http://127.0.0.1:5001/upload')
    f = request.files['file']
    filename = secure_filename(f.filename)
    user_path.mkdir(parents=True, exist_ok=True)
    q = user_path / filename
    f.save(str(q))
    print("YOUR FILE HAS BEEN ADDED")
    return redirect('http://127.0.0.1:5001/list')


@app.route("/download/<string:token>")
#@login_required
def download(token):
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return "error"
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


def does_users_dir_exists(username):
    return os.path.isdir(UPLOAD_FOLDER+"/"+username)


def create_user_dir(username):
    os.mkdir(UPLOAD_FOLDER+"/"+username)


if __name__ == "__main__":
    app.run(debug = True, port = 5002)