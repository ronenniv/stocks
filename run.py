# this file is required for Heroku deployment
from app import app

from db import db
from ma import ma

db.init_app(app)
ma.init_app(app)


# SQLAlchemy will create the tables just before the first request
@app.before_first_request
def create_tables():
    db.create_all()

