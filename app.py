import logging
import os

from flask import Flask

# from flask_jwt import JWT

from flask_restful import Api

from resources.stock import Stock, StockList
from resources.positions import Position, PositionsList
from resources.cash import Cash

app = Flask(__name__)
# turning off the flask SQLAlchemy sync tracker
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# getting url for PostgresDB in Heroku. default is sqlite3 if DATABASE_URL not defined
# check_same_thread parameter for sqlite to support multi-threading
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data.db?check_same_thread=False')

# setting log configuration
log_index = \
    {'DEBUG': logging.DEBUG,
     'INFO': logging.INFO,
     'WARNING': logging.WARNING,
     'ERROR': logging.ERROR,
     'CRITICAL': logging.CRITICAL}

# setting default value to WARNING if not defined or if defined incorrectly
if (debug_level := os.environ.get('DEBUG_LEVEL', 'WARNING')) not in log_index:
    debug_level = 'WARNING'
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S',
                    level=log_index[debug_level])
if debug_level == 'DEBUG':
    app.config['SQLALCHEMY_ECHO'] = True  # send all sqlalchemy statements to log

app.secret_key = 'ronen'
api = Api(app, catch_all_404s=True)  # handle 404 and return friendly message

api.add_resource(Stock, '/stock/<string:symbol>')  # http://hostanme/stock/<symbol name>
api.add_resource(StockList, '/stocks')  # http://hostanme/stocks
api.add_resource(Position, '/position/<string:symbol>')  # http://hostanme/position/<symbol name>
api.add_resource(PositionsList, '/positions')  # http://hostanme/positions
api.add_resource(Cash, '/cash')  # http://hostanme/cash


def main():
    from db import db
    from ma import ma

    db.init_app(app)
    ma.init_app(app)

    # SQLAlchemy will create the tables just before the first request
    @app.before_first_request
    def create_tables():
        db.create_all()

    # starting the app
    app.run(port=5000, debug=True)


if __name__ == '__main__':
    main()
