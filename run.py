from app import app

from db import db

# SQLAlchemy will create the tables just before the first request
@app.before_first_request
def create_tables():
    db.create_all()
