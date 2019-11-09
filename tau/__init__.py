from csv import reader
from pathlib import Path
from smtplib import SMTPException

import click
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import Flask, abort, request, redirect, render_template, send_from_directory, url_for
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

app = Flask(__name__, instance_relative_config = True)
app.config.from_mapping(
    SECRET_KEY = 'dev',
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024,
    UPLOAD_FOLDER = str(Path(app.instance_path) / 'uploads'),
    TOKEN_DURATION = 24 * 60 * 60 * 5
)
app.config.from_pyfile('config.py', silent = True)

mail = Mail(app)

USTS = URLSafeTimedSerializer(app.config['SECRET_KEY'])

UID2MAIL = dict(reader(
    (Path(app.instance_path) / 'uid2email.tsv').open('r'), delimiter = '\t')
)

Path(app.instance_path).mkdir(exist_ok = True)
UPLOAD_FOLDER_PATH = Path(app.config['UPLOAD_FOLDER']).absolute()
UPLOAD_FOLDER_PATH.mkdir(exist_ok = True, parents = True)

@app.cli.command("get-url")
@click.argument("uid")
def get_url(uid):
    print(USTS.dumps(uid))

@app.route('/stats')
def stats():
    files = list(map(lambda p: str(p.relative_to(UPLOAD_FOLDER_PATH)), UPLOAD_FOLDER_PATH.rglob('*.java')))
    return {
        'info': {'uploads': len(files), 'uids': len(UID2MAIL)},
        'uid2email': UID2MAIL,
        'uploads': files,
    }

@app.route("/", methods=['GET', 'POST'])
def index():
    status = None
    email = None
    if request.method == 'GET':
        status = 'GET'
    else:
        if not 'uid' in request.form:
            status = 'MISSING_UID'
        else:
            uid = request.form['uid']
            try:
                email = UID2MAIL[uid]
            except KeyError:
                status = 'UNREGISTERED_UID'
            else:
                token = USTS.dumps(uid)
                try:
                    msg = Message('Your token is: {}'.format(token), recipients = ['massimno.santini@gmail.com'])
                    #mail.send(msg)
                    status = 'OK'
                except SMTPException:
                    status = 'SEND_ERROR'
    return render_template('index.html', status = status, email = email)

@app.route('/upload/', methods=['GET'])
@app.route('/upload/<string:token>', methods=['GET', 'POST'])
def upload(token = None):
    status = None
    email = None
    if not token:
        status = 'MISSING_TOKEN'
    else:
        try:
            uid = USTS.loads(token, max_age = app.config['TOKEN_DURATION'])
        except SignatureExpired:
            status = 'EXPIRED_TOKEN'
        except BadSignature:
            status = 'INVALID_TOKEN'
        else:
            try:
                email = UID2MAIL[uid]
            except KeyError:
                status = 'UNREGISTERED_UID'
            else:
                status = 'OK'
    if request.method == 'POST' and status == 'OK':
        if 'file' not in request.files: abort(400)
        file = request.files['file']
        if file.filename == '': abort(400)
        if file and Path(file.filename).suffix.lower() == '.java':
            filename = secure_filename(file.filename)
            dst = UPLOAD_FOLDER_PATH / uid
            try:
                dst.mkdir(exist_ok = True)
                file.save(str(dst / filename))
            except OSError:
                abort(500)
            return filename
    return render_template('upload.html', status = status, email = email)


