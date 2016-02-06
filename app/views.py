import os

from flask import render_template, flash, redirect, session, url_for, request, g
from app import app, db
from config import EXAMPLE_IMPORT

@app.route('/',methods = ['GET','POST'])
@app.route('/index',methods = ['GET','POST'])
def index():
	return render_template('index.html',testvar = "lol this is a test")
	