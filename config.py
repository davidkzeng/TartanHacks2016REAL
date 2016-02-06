import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

WTF_CSRF_ENABLED = True
SECRET_KEY = "secret2"

UPLOAD_FOLDER = os.path.join(basedir, 'app/static')
EXAMPLE_IMPORT = "hi"

MAIL_SERVER= 'smtp.gmail.com'
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME = 'davidflasktest@gmail.com'
MAIL_PASSWORD = 'flasktest'
ADMINS = ['davidflasktest@gmail.com']