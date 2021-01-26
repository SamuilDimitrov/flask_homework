import uuid
import os

from flask import Flask,request, render_template, redirect, make_response, url_for, session, flash, make_response
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "Thisissecret"
db = SQLAlchemy(app)

login_manager.init_app(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    login_id = db.Column(db.String(36), nullable=True)
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.login_id

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(1000), unique=True, nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    content = db.Column(db.String(10000), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_pasword = request.form["verify_password"]
        user = User.query.filter_by(username=username).first()
        if(user is not None):
            flash("This username already exists!","danger")
            return render_template("register.html")
        if confirm_pasword == password:
            user = User(username=username, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Registration complete!","success")
            return redirect(url_for('login'))
        else:
            flash("Passwords doesn`t match!","danger")
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    response = None
    if request.method == 'GET':
        response = make_response(render_template("login.html"))
    else:

        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            response = make_response(redirect(url_for('profile')))
            flash("You are logged in!","success")
            user.login_id = str(uuid.uuid4())
            db.session.commit()
            login_user(user)
        else:
            response = make_response(redirect(url_for('login')))
            flash("Wrong username or password!","danger")
    return response

@app.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        print(description);
        topics = Topic.query.filter_by(name=name).first()

        if topics:
            flash("This topic already exists!","danger")
            return render_template("create_topic.html")
        else:
            topic = Topic(name=name, description = description)
            db.session.add(topic)
            db.session.commit()
            flash("Topic added successfully!","success")
            return redirect(url_for('index'))
    return render_template("create_topic.html")

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        content = request.form["content"]
        if len(content) > 0:
            if current_user.is_authenticated:
                post = Post(content = content)
                db.session.add(post)
                db.session.commit()
            else:
                flash("You are not logged in")
        else:
            flash("Add content")
    return render_template("create_post.html")

@app.route('/logout')
@login_required
def logout():
    current_user.login_id = None
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template("profile.html")

@app.route('/',methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        return redirect(url_for('create_topic'))
    topics = Topic.query.order_by(Topic.id).all()
    return render_template("index.html",topics = topics)