from flask import Flask, request, session, redirect, render_template, send_from_directory, send_file
import jwt
import os
from pathlib import Path
app = Flask(__name__)
app.secret_key = b'0293jr i(UHoiawu hft923'
app.jwt_secret_key = 'SecretKey'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
app.config.update(
    #SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True
)
app.upload_path = Path(os.path.join(APP_ROOT, 'uploads'))

@app.route("/upload", methods = ['POST', 'GET'])
def upload():
    token = request.form['token']
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return "error"

    if files_limit(session.get('current_user')):
            message = True
            return render_template('upload.html', message=message)
    target = UPLOAD_FOLDER+"/"+session.get('current_user')+"/"
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        filename = file.filename
        destination = "/".join([target, filename])
        file.save(destination)
    return redirect('http://127.0.0.1:5001/list')

@app.route("/download/<string:token>")
def download(token):
    try:
        user = jwt.decode(token.encode(), app.jwt_secret_key, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return "error"

    user_path = app.upload_path.joinpath(user['user']).resolve()
    q = user_path / user['file']
    if q.exists():
        return send_from_directory(user_path, user['file'])

@app.route('/download/<string:filename>')
def send_file_to_user(filename):
        filepath = UPLOAD_FOLDER+"/"+session.get('current_user')+"/"+filename
        if os.path.isfile(filepath):
            return send_file(filepath)


@app.route('/delete/<string:filename>')
def delete(filename):
        filepath = UPLOAD_FOLDER+"/"+session.get("current_user")+"/"+filename
        if os.path.isfile(filepath):
            os.remove(filepath)
            return redirect('http://127.0.0.1:5001/list')

def get_user_files(username):
    filepath = UPLOAD_FOLDER+"/"+str(session.get('current_user'))
    files=[]
    for filename in os.listdir(filepath):
        data=[]
        data.append(filename)
        data.append("/download/"+filename)
        data.append(("/delete/"+filename))
        files.append(data)
    return files


def files_limit(username):
    if not does_users_dir_exists(session.get('current_user')):
        create_user_dir(session.get('current_user'))
        return False
    filepath = UPLOAD_FOLDER+"/"+str(session.get('current_user'))
    counter=0
    for filename in os.listdir(filepath):
        counter = counter+1
    return counter >=5


def does_users_dir_exists(username):
    return os.path.isdir(UPLOAD_FOLDER+"/"+username)


def create_user_dir(username):
    os.mkdir(UPLOAD_FOLDER+"/"+username)


if __name__ == "__main__":
    app.run(debug = True, port = 5002)