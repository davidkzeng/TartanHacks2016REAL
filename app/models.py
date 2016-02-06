from app import db
from flask import url_for
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(64), index = True)
    email = db.Column(db.String(120), index=True)
    description = db.Column(db.String(140), default = "I'm too lame to write a description of myself!")
    profileName = db.Column(db.String(64))
    rating = db.Column(db.Float)
    numberOfRatings = db.Column(db.Integer)
    listing = db.Column(db.String(140))
    listings = db.relationship('Listing', backref='user', lazy='dynamic')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):     
        return unicode(self.id) 

    @staticmethod
    def make_unique_nickname(nickname):
        version = 1
        new_nickname = nickname
        user = User.query.filter_by(nickname = new_nickname).first()
        while user is not None:
            version += 1
            new_nickname = nickname + str(version)
            user = User.query.filter_by(nickname = new_nickname).first()
        return new_nickname

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime)
    buysell = db.Column(db.Boolean)
    blockOrDinex = db.Column(db.String)
    price = db.Column(db.Float)
    location = db.Column(db.String(50))
    details = db.Column(db.String(140))
    active = db.Column(db.Boolean)

    def __repr__(self):
        return '<Post %r>' % (self.body)
