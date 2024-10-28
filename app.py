from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import uuid
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite for local development
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

# Create uploads folder if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
    
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import User, Meme
from forms import RegistrationForm, LoginForm, UploadMemeForm

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    # Allowed extensions for meme uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()

        if existing_user:
            flash('Username or email already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=16)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Look up the user by email
        user = User.query.filter_by(email=form.email.data).first()

        # Check if the user exists and the password is correct
        if user and check_password_hash(user.password, form.password.data):
            # Log the user in
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to the next page if it exists, or the dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/upload_meme', methods=['GET', 'POST'])
@login_required
def upload_meme():
    form = UploadMemeForm()
    if form.validate_on_submit():
        file = form.meme.data

        # Check if the file is allowed (extension check)
        if file and allowed_file(file.filename):
            # Secure the filename to prevent directory traversal
            filename = secure_filename(file.filename)
            # Ensure no filename collision by appending a unique suffix or use a UUID
            unique_filename = f"{current_user.username}_{uuid.uuid4().hex}_{filename}"
            # Save the file to the uploads folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

            meme = Meme(filename=unique_filename, user_id=current_user.id)
            db.session.add(meme)
            db.session.commit()

            flash('Meme uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type. Please upload a valid image (png, jpg, jpeg, gif).', 'danger')
    return render_template('upload_meme.html', form=form)

def get_meme():
    url = "https://meme-api.com/gimme"
    response = json.loads(requests.request("GET", url).text)
    meme_large = response["preview"][-2]
    subreddit = response["subreddit"]
    return meme_large, subreddit

@app.route('/')
def index():
    meme_pic,subreddit = get_meme()
    return render_template("index.html", meme_pic=meme_pic, subreddit=subreddit)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)