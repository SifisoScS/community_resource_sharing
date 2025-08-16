# Ubuntu/app.py
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
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
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
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
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/post_resource', methods=['GET', 'POST'])
def post_resource():
    if 'user_id' not in session:
        flash('Please log in to post a resource.', 'error')
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
        flash('Resource posted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('resources.html', categories=categories)

@app.route('/request_resource/<int:resource_id>', methods=['POST'])
def request_resource(resource_id):
    if 'user_id' not in session:
        return '<p class="text-red-500">Please log in to request a resource.</p>'
    
    resource = Resource.query.get_or_404(resource_id)
    if not resource.is_available:
        return '<p class="text-red-500">This resource is not available.</p>'
    
    request = Request(
        resource_id=resource_id,
        requester_id=session['user_id'],
        message='Resource request from ' + session['username'],
        status='pending'
    )
    db.session.add(request)
    db.session.commit()
    return '<p class="text-green-500">Request submitted successfully!</p>'

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)