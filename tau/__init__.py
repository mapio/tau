from csv import reader
from pathlib import Path
from smtplib import SMTPException

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import Flask, flash, request, redirect, render_template, send_from_directory, url_for
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

app = Flask(__name__, instance_relative_config = True)
app.config.from_mapping(
    SECRET_KEY = 'dev',
    UPLOAD_FOLDER = str(Path(app.instance_path) / 'uploads')
)
app.config.from_pyfile('config.py', silent = True)

mail = Mail(app)

USTS = URLSafeTimedSerializer(app.config['SECRET_KEY'])
UID2MAIL = dict(reader(
    (Path(app.instance_path) / 'uid2email.tsv').open('r'), delimiter = '\t')
)

Path(app.instance_path).mkdir(exist_ok = True)

@app.route('/uid2mail')
def uid2mail():
    return {'uid2email': UID2MAIL}

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
    return render_template('reqtoken.html', status = status, email = email)


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload/', methods=['GET'])
@app.route('/upload/<string:token>', methods=['GET', 'POST'])
def upload(token = None):
    status = None
    email = None

    if request.method == 'GET':
        if not token:
            status = 'MISSING_TOKEN'
        else:
            try:
                uid = USTS.loads(token, max_age = 24 * 60 * 60 * 5)
            except SignatureExpired:
                status = 'EXPIRED_TOKEN'
            except BadSignature:
                status = 'INVALID_TOKEN'

    else:

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(str(Path(app.config['UPLOAD_FOLDER']) / filename))
            return 'ok'

    return render_template('uploads.html', email = email, status = status)


