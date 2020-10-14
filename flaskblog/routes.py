# -*- coding: utf-8 -*-
import secrets, os, io
import numpy as np
from base64 import b64encode
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.models import User, Post
from flaskblog.forms import CatsAndDogsPredictionForm, RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.vgg16 import preprocess_input
import tensorflow as tf



@app.route("/")
@app.route("/home")
def home() :
    page = request.args.get('page', default=1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=5, page=page)
    return render_template("home.html", posts = posts)

@app.route("/about")
def about():
    return render_template("about.html", title = "About")

@app.route("/register", methods=["GET","POST"]) 
def register() :
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created, you are now able to log in !', 'success')
        return(redirect(url_for("login")))
        
    return render_template("register.html", title = "Register", form = form)

@app.route("/login", methods=["GET","POST"]) 
def login() :
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Loggin unsuccessful, please check your credentials", "danger")
    return render_template("login.html", title = "Log in", form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + file_ext
    picture_path = os.path.join(app.root_path, 'static/images/', picture_fn)
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    prev_picture = os.path.join(app.root_path, 'static/profile_pics', current_user.image_file)
    if os.path.exists(prev_picture) and os.path.basename(prev_picture) != 'default.jpeg':
        os.remove(prev_picture)
    return picture_fn

@app.route("/account", methods=["GET","POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been successfuly updated", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename="images/" + current_user.image_file) #20:13
    return render_template("account.html", title="Account", image_file=image_file, form=form)

@app.route("/post/new", methods=["GET","POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created", "success")
        return redirect(url_for('home'))
    return render_template("create_post.html", title="New Post", form=form, legend="New post")

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=["GET","POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user :
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated", "success")
        return redirect(url_for("post", post_id=post.id))
    if request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template("create_post.html", title="Update Post", form=form, legend="Update post")   

@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user :
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted", "success")
    return redirect(url_for("home"))

@app.route("/user/<string:username>")
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', default=1, type=int)
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(per_page=5, page=page)
    return render_template("user_posts.html", posts = posts, user=user)


def send_reset_email(user):
    pass
@app.route("/reset_password", methods=["GET","POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("If an account with this email address exists, a password reset message will be sent shortly.", "danger")
        return redirect(url_for("login"))
    return render_template("reset_request.html", title="Reset Password", form=form)
    
@app.route("/reset_password/<token>", methods=["GET","POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return render_template("reset_request.html")
    form = ResetPasswordForm()
    return render_template("reset_token.html", title="Reset Password", form=form)

@app.route("/cats_dogs_prediction", methods= ["GET","POST"])
def predict_image():
    form = CatsAndDogsPredictionForm()
    #loaded_model = load_model("flaskblog/model.h5")
    if form.validate_on_submit():
        if form.picture.data:
            picture = form.picture.data
            img = Image.open(picture)
            file_object = io.BytesIO()
            output_size = (224,224)
            img.thumbnail(output_size)
            img.save(file_object, 'PNG')
            base64img = "data:image/png;base64,"+b64encode(file_object.getvalue()).decode('ascii')
            image_asarray = np.asarray(img)
            image_asarray = np.expand_dims(image_asarray, axis=0)
            prediction = loaded_model.predict(image_asarray)
            if prediction[0][0] > prediction[0][1]:
                label = "cat"
            else:
                label = "dog"
            return render_template("cat_dog_prediction.html", form=form, title="Cats and Dogs Prediction", img=base64img, label=label)
        
    return render_template("cat_dog_prediction.html", form=form, title="Cats and Dogs Prediction")

@app.route("/cats_dogs_prediction/display", methods=["GET"])
def display_img():
    print('ok')
    