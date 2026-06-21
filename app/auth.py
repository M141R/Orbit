from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_user,logout_user,login_required
from werkzeug.security import check_password_hash,generate_password_hash
import secrets
from datetime import datetime,timedelta, timezone
from .models import User
from . import db

auth = Blueprint('auth',__name__)

@auth.route("/login")
def login():
    return render_template('auth/login.html')

@auth.route("/login",methods = ['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user = db.session.scalar(db.select(User).where(User.email==email))

    if not user or not check_password_hash(user.password_hash,password):
        flash('Please check you login details and try again')
        return redirect(url_for('auth.login'))
    
    login_user(user,remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('auth/signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = db.session.scalar(db.select(User).where(User.email==email))

    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.login'))
    
    new_user = User(email=email, username=name, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route('/forgot-password')
def forgot_password():
    return render_template('auth/forgot_password.html')

@auth.route('/forgot-password', methods=['POST'])
def forgot_password_post():
    email = request.form.get('email')
    user = db.session.scalar(db.select(User).where(User.email==email))

    if user:
        user.reset_token = secrets.token_urlsafe(32)
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()

        flash('Password reset link sent to your email')

    return redirect(url_for('auth.login'))

@auth.route('/reset-password/<token>')
def reset_password(token):
    user = db.session.scalar(db.select(User).where(User.reset_token == token))

    if not user or user.reset_token_expires.replace(tzinfo=timezone.utc) <datetime.now(timezone.utc):
        flash('Invalid or expired reset token')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html',token=token)

