import os

from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.mail import Message
from sqlalchemy import desc
from app import app, db, lm, mail
from config import EXAMPLE_IMPORT, ADMINS
from forms import *
from models import User, Listing
from decimal import *
from urllib2 import urlopen
import json
from datetime import datetime, timedelta
import pygal
from pygal.style import TurquoiseStyle	

@app.route('/',methods = ['GET','POST'])
@app.route('/index',methods = ['GET','POST'])
def index():
	print g.user
	return render_template('index.html')
	
@app.route('/login',methods = ['GET','POST'])
def login():
	if g.user is not None and g.user.is_authenticated:
		return redirect(url_for('profile'))
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
	nickname = name.strip()
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
	form = ProfileForm(description = g.user.description)
	if (form.validate_on_submit()):
		g.user.description = form.description.data
		g.user.buyAlert = form.buyAlert.data
		g.user.sellAlert = form.sellAlert.data
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
		return redirect('/profile/' + user.nickname)
	return render_template('ratingform.html', form = form, rateduser = rateduser)


@app.route('/listings',methods=['GET','POST'])
@app.route('/listings/<setting>',methods=['GET','POST'])
@login_required
def listings(setting = "aaa"):
	allListingsQuery = Listing.query.filter_by(active = True)
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
		newList = Listing(blockOrDinex = form.blockOrDinex.data, timestamp = datetime.now(), price = float(form.price.data), details = form.details.data, location = form.location.data, active = True)
		if form.buysell.data == 'Buy':
			newList.buysell = True
		else:
			newList.buysell = False
		newList.user = g.user
		db.session.add(newList)
		db.session.commit()
		if newList.buysell == True:
			alertuserstup = db.session.query(User.email).filter_by(buyAlert=True).all()
		else:
			alertuserstup = db.session.query(User.email).filter_by(sellAlert=True).all()
		alertusers = [x[0] for x in alertuserstup]
		alertusers = filter (lambda x: ('@' in x) and ('.' in x), alertusers)
		if (len(alertusers) != 0):
			msg = Message('New Post Alert on Dining Exchange',sender='davidflasktest@gmail.com',recipients=alertusers)
			msg.body = "Hello,\n\n A listing for which you are receiving alerts has been posted to CMU Dining Exchange."
			msg.body += "\n\nThe listing is visible at " + "http://127.0.0.1:5000" + url_for('listings')
			mail.send(msg)
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
		post.active = False
		post.datetime = datetime.now()
		db.session.add(post)
		db.session.commit()
		recipients = [poster.email, g.user.email]
		recipients = filter (lambda x: ('@' in x) and ('.' in x), recipients)
		if len(recipients) != 0:
			msg = Message('Dining Exchange Match',sender='davidflasktest@gmail.com',recipients=recipients)
			msg.body = "Hello users,\n\n" + "You have recently been matched on CMU Dining Exchange. The user "
			msg.body += str(g.user.nickname) + " will" # has accepted your offer. The terms of the agreement are: \n\n" 
			if post.buysell:
				msg.body += " buy "
			else:
				msg.body += " sell "
			msg.body += "one " + post.blockOrDinex
			msg.body += " per $" + str(post.price)  
			msg.body += " from " + poster.nickname + ". The meeting location is " + post.location + "."
			msg.body += "\n\nAfter the exchange, please rate each other on http://127.0.0.1:5000"
			msg.body += url_for('rate', rateduser = poster.nickname) + " and http://127.0.0.1:5000"
			msg.body += url_for('rate', rateduser = g.user.nickname)
			msg.body += "\n\nThank you for using CMU Dining Exchange!"		
			mail.send(msg)
		return redirect(url_for('success'))
	return render_template("transaction.html", title = "Transaction", form = form, post = post, poster = poster)

@app.route('/success')
def success():
	return render_template("success.html")

def getPastTransactions():
	pastListings = Listing.query.filter_by(active = False).all()
	return pastListings

@app.route('/priceHistory')
def priceHistory():
	blockHistory = getPastTransactions()
	blockHistoryTimes = [x.timestamp for x in blockHistory]
	blockPrices = [x.price if x.blockOrDinex == "Block" else None for x in blockHistory]
	dinexPrices = [x.price if x.blockOrDinex == "Dinex" else None for x in blockHistory]
	date_chart = pygal.Line(x_label_rotation=20,style = TurquoiseStyle,x_title = "Time Sold",
		y_title = "Price per Block",height = 400)
	date_chart.x_labels = map(lambda d: d.strftime('%Y-%m-%d %H:%M'), blockHistoryTimes)
	date_chart.add("Blocks",blockPrices)
	secondaryExists = False
	for x in dinexPrices:
		if x != None:
			secondaryExists = True
	if secondaryExists:
		date_chart.add("Dinex",dinexPrices, secondary = True)
	date_chart.render()
	return render_template('pricehistory.html',price_chart = date_chart)

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

def createSomeData():
	return true