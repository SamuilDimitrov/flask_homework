import uuid
import os

from flask import Flask, request, render_template, redirect, make_response, url_for, session, flash, make_response
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import asc


from database import db_session, init_db
from models import User, Topic, Post

login_manager = LoginManager()


app = Flask(__name__)
app.secret_key = "Thisissecret"


init_db()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
            db_session.add(user)
            db_session.commit()
            flash("Registration complete!","success")
            return redirect(url_for('login'))
        else:
            flash("Passwords doesn`t match!","danger")
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template("login.html")
    else:

        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            flash("You are logged in!","success")
            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Wrong username or password!","danger")
            return redirect(url_for('login'))

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
            db_session.add(topic)
            db_session.commit()
            flash("Topic added successfully!","success")
            return redirect(url_for('index'))
    return render_template("create_topic.html")

@app.route('/topic/<int:topic_id>')
def show_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first()
    posts = Post.query.filter_by(topic_id=topic_id).order_by(asc(Post.id))
    entries = []
    for post in posts:
        entry = lambda: None; entry.post = post; entry.user = User.query.filter_by(id=post.user_id).first()
        entries.append(entry)
    return render_template("topic.html",topic = topic,posts = posts,entries = entries)

@app.route('/create_post/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def create_post(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first()
    if request.method == 'POST':
        content = request.form["content"]
        if len(content) > 0:
            print(current_user.id)
            post = Post(content = content,topic_id = topic_id,user_id = current_user.id)
            db_session.add(post)
            db_session.commit()
            flash("Post added successfully!","success")
            return redirect("/topic/"+str(topic_id))
        else:
            flash("Add content")
    return render_template("create_post.html",topic = topic)

@app.route('/logout')
@login_required
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post_to_delete = Post.query.filter_by(id = id).first()
    if current_user.id != post_to_delete.user_id:
        return redirect("/topic/"+str(post_to_delete.topic_id))
    db_session.delete(post_to_delete)
    db_session.commit()
    return redirect("/topic/"+str(post_to_delete.topic_id))

@app.route('/change/<int:id>',methods=['GET', 'POST'])
@login_required
def change(id):
    post_to_change = Post.query.filter_by(id = id).first()
    if current_user.id != post_to_change.user_id:
        return render_template('change.html', post = post_to_change)
    if request.method == 'POST':
        post_to_change.content = request.form['Change_content']
        db_session.commit()
        return redirect("/topic/"+str(post_to_change.topic_id))
    return render_template('change.html', post = post_to_change)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template("profile.html")

@app.route('/',methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        return redirect(url_for('create_topic'))
    topics = Topic.query.order_by(asc(Topic.id)).all()
    return render_template("index.html",topics = topics)
