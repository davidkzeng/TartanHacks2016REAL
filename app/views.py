import os

from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from config import EXAMPLE_IMPORT
from forms import LoginForm, RegisterForm, ProfileForm
from models import User

@app.route('/',methods = ['GET','POST'])
@app.route('/index',methods = ['GET','POST'])
@login_required
def index():
	return render_template('index.html',testvar = "lol this is a test")
	
@app.route('/login',methods = ['GET','POST'])
def login():
	if g.user is not None and g.user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if(form.validate_on_submit()):
		session['remember_me'] = form.remember_me.data
		return try_login(form.nickname.data,form.password.data)
	return render_template('login.html',title = 'Sign in', form = form)

def try_login(name,pw):
	user = User.query.filter_by(nickname = name).first()
	if user is None:
		flash('Username does not Exist')
		return redirect(url_for('login'))
	else:
		if not pw == user.password:
			flash('Password Incorrect')
			return redirect(url_for('login'))
	remember_me = False
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None)
	login_user(user, remember = remember_me)
	return redirect(request.args.get('next') or url_for('index'))

@app.route('/register',methods = ['GET','POST'])
def register():
	form = RegisterForm()
	if(form.validate_on_submit()):
		return try_register(form.nickname.data,form.password.data,form.email.data)
	return render_template('register.html',title = 'Register', form = form)

def try_register(name,pw,email):
	user = User.query.filter_by(email = email).first()
	if not user is None:
		flash('Email in Use')
		return redirect(url_for('register'))
	nickname = namex
	nickname = User.make_unique_nickname(nickname)
	password = pw
	user = User(nickname = nickname, password = password, email = email)
	db.session.add(user)
	db.session.commit()
	flash("We made a new account for you!")
	return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#necessary for logins to work
@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

#Flask will call this before a request
@app.before_request 
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
    	db.session.add(g.user)
    	db.session.commit()

@app.route('/profile')
@login_required
def profile():
	return render_template('profile.html', user = g.user)

@app.route('/editprofile',methods = ['GET','POST'])
@login_required
def editProfile():
	form = ProfileForm()
	if(form.validate_on_submit()):
		g.user.description = form.description.data
		db.session.add(g.user)
    	db.session.commit()
	return render_template('editprofile.html', form = form, user = g.user)