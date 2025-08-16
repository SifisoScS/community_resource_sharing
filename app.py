from flask import Flask, render_template, redirect, url_for, request, session
from models import User, Resource, db  # Assuming you have a models.py for database models

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resources.db'
db.init_app(app)

@app.route('/')
def index():
    resources = Resource.query.all()
    return render_template('index.html', resources=resources)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic
        pass
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle registration logic
        pass
    return render_template('register.html')

@app.route('/post_resource', methods=['GET', 'POST'])
def post_resource():
    if request.method == 'POST':
        # Handle resource posting logic
        pass
    return render_template('resources.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)