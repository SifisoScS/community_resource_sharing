# Ubuntu/app.py
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import Babel, gettext
from models import User, Resource, Category, Request, db
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Configure Flask
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Flask-Babel Configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'sw', 'zu']

def get_locale():
    if request.method == 'POST' and 'language' in request.form:
        session['language'] = request.form['language']
    return session.get('language', request.accept_languages.best_match(['en', 'sw', 'zu']) or 'en')

babel = Babel(app, locale_selector=get_locale)

@app.route('/set_language', methods=['POST'])
def set_language():
    if 'language' in request.form:
        session['language'] = request.form['language']
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    resources = Resource.query.filter_by(is_active=True).all()
    return render_template('index.html', resources=resources)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_verified'] = user.is_verified  # Sync verification status
            flash(gettext('Login successful!'), 'success')
            return redirect(url_for('index'))
        else:
            flash(gettext('Invalid username or password.'), 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash(gettext('Username already exists.'), 'error')
        elif User.query.filter_by(email=email).first():
            flash(gettext('Email already registered.'), 'error')
        else:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=generate_password_hash(password),
                is_verified=False,  # Default to unverified
                rating=0.0,
                rating_count=0
            )
            db.session.add(user)
            db.session.commit()
            flash(gettext('Registration successful! Please log in.'), 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/verify_identity', methods=['GET', 'POST'])
def verify_identity():
    if 'user_id' not in session:
        flash(gettext('Please log in to verify your identity.'), 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        verification_code = request.form.get('verification_code')
        user = User.query.get(session['user_id'])
        if verification_code == 'VALID_CODE':  # Replace with actual validation logic
            user.is_verified = True
            session['is_verified'] = True
            db.session.commit()
            flash(gettext('Identity verified successfully!'), 'success')
            return redirect(url_for('profile'))
        else:
            flash(gettext('Invalid verification code.'), 'error')
    return render_template('verify_identity.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash(gettext('Please log in to view your profile.'), 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    resources = Resource.query.filter_by(owner_id=user.id, is_active=True).all()
    return render_template('profile.html', user=user, resources=resources)

@app.route('/rate_user/<int:user_id>', methods=['POST'])
def rate_user(user_id):
    if 'user_id' not in session:
        return '<p class="text-red-500">' + gettext('Please log in to rate a user.') + '</p>'
    rating = int(request.form.get('rating', 1))
    if 1 <= rating <= 5:
        if user := User.query.get(user_id):
            user.rating = (user.rating * user.rating_count + rating) / (user.rating_count + 1)
            user.rating_count += 1
            db.session.commit()
            return '<p class="text-green-500">' + gettext('Rating submitted!') + '</p>'
    return '<p class="text-red-500">' + gettext('Invalid rating.') + '</p>'

@app.route('/post_resource', methods=['GET', 'POST'])
def post_resource():
    if 'user_id' not in session:
        flash(gettext('Please log in to post a resource.'), 'error')
        return redirect(url_for('login'))
    
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = request.form['category_id']
        location = request.form['location']
        
        resource = Resource(
            title=title,
            description=description,
            category_id=category_id,
            location=location,
            owner_id=session['user_id']
        )
        db.session.add(resource)
        db.session.commit()
        flash(gettext('Resource posted successfully!'), 'success')
        return redirect(url_for('index'))
    return render_template('post_resource.html', categories=categories)

@app.route('/request_resource/<int:resource_id>', methods=['POST'])
def request_resource(resource_id):
    if 'user_id' not in session:
        return '<p class="text-red-500">' + gettext('Please log in to request a resource.') + '</p>'
    
    resource = Resource.query.get_or_404(resource_id)
    if not resource.is_available:
        return '<p class="text-red-500">' + gettext('This resource is not available.') + '</p>'
    
    request = Request(
        resource_id=resource_id,
        requester_id=session['user_id'],
        message='Resource request from ' + session['username'],
        status='pending'
    )
    db.session.add(request)
    db.session.commit()
    return '<p class="text-green-500">' + gettext('Request submitted successfully!') + '</p>'

@app.route('/match_resources')
def match_resources():
    if 'user_id' not in session:
        flash(gettext('Please log in to match resources.'), 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user_location = user.location if user else None
    resources = Resource.query.filter_by(is_active=True).all()
    
    if user_location:
        matched_resources = [r for r in resources if r.location == user_location]
    else:
        matched_resources = resources
    
    return render_template('match_resources.html', resources=matched_resources)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/mission_vision')
def mission_vision():
    return render_template('mission_vision.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/browse')
def browse():
    resources = Resource.query.filter_by(is_active=True).all()
    return render_template('browse.html', resources=resources)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_verified', None)
    session.pop('language', None)
    flash(gettext('Logged out successfully.'), 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)