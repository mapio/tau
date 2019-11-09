from pathlib import Path

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import Flask, flash, request, redirect, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__, instance_relative_config = True)
app.config.from_mapping(
    SECRET_KEY = 'dev',
    UPLOAD_FOLDER = str(Path(app.instance_path) / 'uploads')
)
app.config.from_pyfile('config.py', silent = True)

USTS = URLSafeTimedSerializer(app.config['SECRET_KEY'])

Path(app.instance_path).mkdir(exist_ok = True)

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('reqtoken.html')
    else:
        return USTS.dumps(request.form['uid'])

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload/', methods=['GET'])
@app.route('/upload/<string:token>', methods=['GET', 'POST'])
def upload_file(token = None):

    if request.method == 'GET':
        error = None
        uid = None
        if not token:
            error = 'MISSING'
        else:
            try:
                uid = USTS.loads(token, max_age = 24 * 60 * 60 * 5)
            except SignatureExpired:
                error = 'EXPIRED'
            except BadSignature:
                error = 'INVALID'
        return render_template('uploads.html', uid = uid, error = error)

    elif request.method == 'POST':
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

