import requests
import requests.exceptions
from flask_restful import reqparse
from sqlalchemy.exc import IntegrityError
import logging

import models.constants as const
from db import db


class StockModel(db.Model):  # extend db.Model for SQLAlchemy

    ID_STR = 'id'
    SYMBOL_STR = 'symbol'
    DESC_STR = 'desc'
    QUANTITY_STR = 'quantity'
    UNIT_COST_STR = 'unit_cost'
    STOP_QUOTE_STR = 'stop_quote'

    PRICE_STR = 'price'

    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(const.SYMBOL_MAX_LEN), unique=True)
    desc = db.Column(db.String(const.DESC_MAX_LEN))
    quantity = db.Column(db.Integer())
    unit_cost = db.Column(db.Float(precision=const.PRICE_PRECISION))
    stop_quote = db.Column(db.Float(precision=const.PRICE_PRECISION))

    # this definition comes together with the definition in
    # PositionsModel. Lazy will ask to not create entries for positions
    positions = db.relationship('PositionsModel', lazy='dynamic', backref='stock', cascade='all')

    def __init__(self, symbol, desc, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.desc = desc
        self.quantity = 0
        self.unit_cost = 0
        self._price = 0
        self.stop_quote = 0

    def get_price(self):
        """get current stock price from finnhub"""
        quote_api_url = const.FINNHUB_URL + "/quote"
        try:
            response = requests.get(quote_api_url,
                                    params={'symbol': self.symbol, 'token': const.TOKEN},
                                    timeout=0.5
                                    )
            response.raise_for_status()
        except requests.exceptions.ConnectTimeout:
            logging.warning(f'func: get_current_price ConnectTimeout')
            self._price = 'ERR'
        except Exception as e:
            logging.error(f'func: get_current_price Exception {e}')
            self._price = 'ERR'
        else:
            json_response = response.json()
            if 'error' in json_response:
                # symbol not found
                logging.error(f'func: get_current_price, symbol {self.symbol} not found')
                self._price = 'ERR'
            else:
                self._price = json_response['c']
        finally:
            return self._price

    price = property(fget=get_price, fset=None, fdel=None, doc="Get current price")

    def __repr__(self):
        return str(self.json())

    @staticmethod
    def symbol_validation(value):
        """ do validation on symbol received from request"""
        value = str(value)
        if len(value) > const.SYMBOL_MAX_LEN and not value.isalpha():
            raise ValueError('Not a valid symbol')
        return value.upper()

    @staticmethod
    def desc_validation(value):
        """ do validation on desc received from request"""
        value = str(value)
        if len(value) > const.DESC_MAX_LEN and not value.isprintable():
            raise ValueError('Not a valid description')
        return value

    @classmethod
    def parse_request_json_with_symbol(cls):
        """
        parse symbol and description from request
        :return parsed args as dict
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=StockModel.SYMBOL_STR,
                            type=cls.symbol_validation,
                            required=True,
                            trim=True)
        parser.add_argument(name=StockModel.DESC_STR,
                            type=cls.desc_validation,
                            required=True,
                            trim=True)
        return parser.parse_args(strict=False)

    @classmethod
    def parse_request_json(cls):
        """
        parse desc from request
        :return parsed arg as dict
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=StockModel.DESC_STR,
                            type=cls.desc_validation,
                            required=True,
                            trim=True,
                            help='Description is incorrect')
        return parser.parse_args(strict=False)

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
        create JSON for the stock details. not including current price
        """
        json_dict = {
            self.ID_STR: self.id,
            self.SYMBOL_STR: self.symbol,
            self.DESC_STR: self.desc,
            self.QUANTITY_STR: self.quantity,
            self.UNIT_COST_STR: self.unit_cost
        }
        if self.stop_quote:
            json_dict[self.STOP_QUOTE_STR] = self.stop_quote
        return json_dict

    def detailed_json(self) -> dict:
        """
        create JSON for the stock details, current stock price and stock's positions
        """
        json_dict = self.json()
        # add the current price to json
        json_dict[self.PRICE_STR] = self.price
        # add the positions list to the json
        positions_list = {'positions': [position.json() for position in self.positions.all()]}
        json_dict.update(positions_list)

        return json_dict

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
            logging.info(f'func: stock.save_details, exception: IntegrityError, self: {self}')
            db.session.rollback()
            return False

    def update_symbol_and_desc(self, symbol, desc) -> bool:
        """update existing stock symbol and desc
        :return True if success, False if error"""
        try:
            self.symbol = symbol
            self.desc = desc
            db.session.commit()
            return True
        except IntegrityError as e:
            db.session.rollback()
            logging.error(f'func: update_symbol_and_desc, exception {e}, self: {self}')
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

    def del_stock(self) -> bool:
        """delete stock from DB
        :return: True for success, False for failure"""
        try:
            db.session.delete(self)  # del will cascade to positions deletion
            db.session.commit()
            return True
        except IntegrityError as e:  # unique constraint violation
            db.session.rollback()
            logging.warning(f'func: del_stock, Exception {e}')
            return False
