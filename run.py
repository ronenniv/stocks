from app import app

from db import db

db.init_app(app)

#app.run(port=5000, debug=True)

# SQLAlchemy will create the tables just before the first request
@app.before_first_request
def create_tables():
    db.create_all()