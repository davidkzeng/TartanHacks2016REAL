import os

from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from sqlalchemy import desc
from app import app, db, lm
from config import EXAMPLE_IMPORT
from forms import *
from models import User, Listing

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
	nickname = name
	nickname = User.make_unique_nickname(nickname)
	password = pw
	user = User(nickname = nickname, password = password, email = email, rating = 0.0)
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
@app.route('/profile/<nickname>')
@login_required
def profile(nickname = ""):
	if(nickname == ""):
		nickname = g.user.nickname
	nickUser = User.query.filter_by(nickname=nickname).first()
	return render_template('profile.html', user = nickUser, loginUser = g.user)

@app.route('/editprofile', methods = ['GET','POST'])
@login_required
def editProfile():
	form = ProfileForm()
	if (form.validate_on_submit()):
		g.user.description = form.description.data
		db.session.add(g.user)
		db.session.commit()
		return redirect(url_for('profile'))
	return render_template('editprofile.html', form = form, user = g.user)

@app.route('/rate/<rateduser>',methods=['GET','POST'])
@login_required
def rate(rateduser):
	user = User.query.filter_by(nickname=rateduser).first()
	form = RatingForm()
	if(form.validate_on_submit()):
		if user.rating == 0.0:
			user.rating = form.rating.data
			user.numberOfRatings = 1
		else:
			user.rating = float(user.rating * user.numberOfRatings + float(form.rating.data)) / (user.numberOfRatings + 1)
			user.numberOfRatings += 1
		db.session.add(g.user)
		db.session.commit()
		return redirect(url_for('index'))
	return render_template('ratingform.html', form = form, rateduser = rateduser)


@app.route('/listings',methods=['GET','POST'])
@app.route('/listings/<setting>',methods=['GET','POST'])
@login_required
def listings(setting = "aaa"):
	allListingsQuery = Listing.query
	if "b" in setting:
		allListingsQuery = allListingsQuery.filter_by(buysell = True)
	if "s" in setting:
		allListingsQuery = allListingsQuery.filter_by(buysell = False)
	if "l" in setting:
		allListingsQuery = allListingsQuery.filter_by(blockOrDinex = "Block")
	if "d" in setting:
		allListingsQuery = allListingsQuery.filter_by(blockOrDinex = "Dinex")
	if "u" in setting:
		allListingsQuery = allListingsQuery.order_by(Listing.price)
	if "g" in setting:
		allListingsQuery = allListingsQuery.order_by(desc(Listing.price))
	allListings = allListingsQuery.all()
	form = ListingForm()
	if(form.validate_on_submit()):
		newList = Listing(blockOrDinex = form.blockOrDinex.data, price = float(form.price.data), details = form.details.data, location = form.location.data)
		if form.buysell.data == 'Buy':
			newList.buysell = True
		else:
			newList.buysell = False
		newList.user = g.user
		db.session.add(newList)
		db.session.commit()
		return redirect(url_for('listings'))
	return render_template("listings.html",title ='Listings',form = form,lists=allListings,
		user=g.user,set = setting, updateFunc = update)


@app.route('/transaction/<int:postid>', methods=['GET','POST'])
@login_required
def transaction(postid):
	post = Listing.query.filter_by(id = postid).first()
	poster = User.query.filter_by(id=post.user_id).first()
	form = TransactionForm()
	if(form.validate_on_submit()):
		pass	
	return render_template("transaction.html", title = "Transaction", form = form, post = post, poster = poster)

def update(stringSet, change):
	setting = list(stringSet)
	if change == 'b':
		if setting[0] == 'b':
			setting[0] = 'a'
		else:
			setting[0] = 'b'
	if change == 's':
		if setting[0] == 's':
			setting[0] = 'a'
		else:
			setting[0] = 's'
	if change == 'l':
		if setting[1] == 'l':
			setting[1] = 'a'
		else:
			setting[1] = 'l'
	if change == 'd':
		if setting[1] == 'd':
			setting[1] = 'a'
		else:
			setting[1] = 'd'
	if change == 'u':
		if setting[2] == 'u':
			setting[2] = 'a'
		else:
			setting[2] = 'u'
	if change == 'g':
		if setting[2] == 'g':
			setting[2] = 'a'
		else:
			setting[2] = 'g'
	return "".join(setting)

def display(setting, check):
	return check in setting

