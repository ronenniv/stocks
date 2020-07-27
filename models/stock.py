import requests
import requests.exceptions
from flask import current_app  # for debugging
from flask_restful import reqparse, abort
from sqlalchemy.exc import IntegrityError
import logging

import models.constants as const
from db import db


class StockModel(db.Model):  # extend db.Model for SQLAlechemy

    JSON_SYMBOL_STR = 'symbol'
    JSON_DESC_STR = 'desc'
    JSON_UNIT_COST_STR = 'unit_cost'

    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(const.SYMBOL_MAX_LEN), unique=True)
    desc = db.Column(db.String(const.DESC_MAX_LEN))
    quantity = db.Column(db.Integer())
    unit_cost = db.Column(db.Float(precision=const.PRICE_PRECISION))

    # this definition comes together with the definition in
    # PositionsModel. Lazy will ask to not create entries for positions
    positions = db.relationship('PositionsModel', lazy='dynamic', backref='stock', cascade='all')

    def __init__(self, symbol, desc, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.desc = desc
        self.quantity = 0
        self.unit_cost = 0
        self.price = 0

    def __repr__(self):
        return str(self.json())

    @staticmethod
    def parse_validations(symbol=None, desc=None) -> dict:
        """
        return True if both fields are valid
        can transfer only one value to validate
        """
        validation_flag = {}
        if symbol:
            if len(symbol) <= const.SYMBOL_MAX_LEN and symbol.isalpha() and symbol.isupper():
                validation_flag['symbol'] = True
            else:
                validation_flag['symbol'] = False
        if desc:
            if len(desc) <= const.DESC_MAX_LEN and desc.isprintable():
                validation_flag['desc'] = True
            else:
                validation_flag['desc'] = False
        return validation_flag

    @classmethod
    def parse_request_json_with_symbol(cls):
        """
        parse symbol and description from request
        :return parsed args as dict
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=StockModel.JSON_SYMBOL_STR,
                            type=str.upper,
                            required=True,
                            trim=True,
                            help='Symbol is missing')
        parser.add_argument(name=StockModel.JSON_DESC_STR,
                            type=str,
                            required=True,
                            trim=True,
                            help='Description is missing')
        result = parser.parse_args(strict=False)

        # validation on parse data
        validation_result = cls.parse_validations(**result)
        if not validation_result['symbol']:
            abort(400, message='Symbol is incorrect')
        elif not validation_result['desc']:
            abort(400, message='Description is incorrect')

        return result

    @classmethod
    def parse_request_json(cls):
        """
        parse desc from request
        :return parsed arg as dict
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=StockModel.JSON_DESC_STR,
                            type=str,
                            required=True,
                            trim=True,
                            help='Description is incorrect')
        result = parser.parse_args(strict=False)
        # validation on parse data
        if not cls.parse_validations(desc=result[StockModel.JSON_DESC_STR])['desc']:
            abort(400, message='Description incorrect')

        return result

    @classmethod
    def find_by_symbol(cls, symbol):
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        # SELECT * FROM stock WHERE symbol=symbol
        return cls.query.filter_by(symbol=symbol).first()

    def json(self) -> dict:
        """
        create JSON for the stock details. not include current price
        """
        return {
            'id': self.id,
            'symbol': self.symbol,
            'desc': self.desc,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
        }

    def detailed_json(self, app=None) -> dict:
        """
        create JSON for the stock details, stock price and stock's positions
        """
        positions_list = {'positions':
                              [position.json() for position in self.positions.all()]}

        self.get_current_price(app)  # get the current stock price
        return {
            'id': self.id,
            'symbol': self.symbol,
            'desc': self.desc,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'price': self.price,
            **positions_list
        }

    def save_details(self) -> bool:
        """
        update or insert symbol and desc for stock
        :return: True for success, False for failure
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except IntegrityError:
            # unique constraint violation - stock already exist
            current_app.logger.debug(f'func: stock.save_details, exception: IntegrityError, self: {self}')
            db.session.rollback()
            return False

    def update_symbol_and_desc(self, symbol, desc):
        """update existing stock symbol and desc
        :return True if success, False if error"""
        try:
            self.symbol = symbol
            self.desc = desc
            db.session.commit()
            return True
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f'func: update_symbol_and_desc, exception {e}, self: {self}')
            return False

    def calc_unit_cost_and_quantity(self, unit_cost, quantity):
        """calculate the unit cost and the quantity according to the position
        positive quantity for adding, negative quantity for removing"""
        try:
            self.unit_cost = round(
                ((self.unit_cost * self.quantity) + (unit_cost * quantity)) / (self.quantity + quantity),
                const.PRICE_PRECISION)
            self.quantity = self.quantity + quantity
        except ZeroDivisionError:
            # all positions are sold -> quantity is zero
            self.unit_cost = 0
            self.quantity = 0
        db.session.commit()

    def get_current_price(self, app=None):
        """get current stock price from finnhub"""
        quote_api_url = const.FINNHUB_URL + "/quote"
        try:
            response = requests.get(quote_api_url,
                                    params={'symbol': self.symbol, 'token': const.TOKEN},
                                    timeout=0.5
                                    )
            logging.getLogger(__name__).debug('logged from thread')
            if app:
                app.logger.debug(f'url={response.url}')
            else:
                current_app.logger.debug(f'url={response.url}')
            response.raise_for_status()
        except requests.exceptions.ConnectTimeout as e:
            if app:
                app.logger.debug(f'func: get_current_price ConnectTimeout')
            else:
                current_app.logger.error(f'func: get_current_price ConnectTimeout')
            self.price = 'ERR'
        except Exception as e:
            if app:
                app.logger.debug(f'func: get_current_price Exception {e}')
            else:
                current_app.logger.error(f'func: get_current_price Exception {e}')
            self.price = 'ERR'
        else:
            json_response = response.json()
            if 'error' in json_response:
                # symbol not found
                current_app.logger.error(f'func: get_current_price, symbol {self.symbol} not found')
                self.price = 'ERR'
            else:
                self.price = json_response['c']

    def del_stock(self) -> bool:
        """delete stock from DB
        :return: True for success, False for failure"""
        try:
            db.session.delete(self)  # del will cascade to positions deletion
            db.session.commit()
            return True
        except IntegrityError as e:  # unique constraint violation
            current_app.logger.debug(f'func: del_stock, Exception {e}')
            db.session.rollback()
            return False
