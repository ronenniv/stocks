from db import db

from flask import current_app  # for debugging

from flask_restful import reqparse, abort

from sqlalchemy.exc import IntegrityError

import models.constants as const


class StockModel(db.Model):  # extend db.Model for SQLAlechemy

    JSON_SYMBOL_STR = 'symbol'
    JSON_DESC_STR = 'desc'

    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(const.SYMBOL_MAX_LEN), unique=True)
    desc = db.Column(db.String(const.DESC_MAX_LEN))
    quantity = db.Column(db.Integer())
    unit_cost = db.Column(db.Float(precision=const.PRICE_PRECISION))
    price = db.Column(db.Float(precision=const.PRICE_PRECISION))

    #positions = db.relationship('PositionsModel', lazy='dynamic')  # this definition comes together with the define in
    # PositionsModel. Lazy will ask to not create entries for positions

    def __init__(self, symbol, desc, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.desc = desc
        self.quantity = 0
        self.unit_cost = 0
        self.price = 0

    @staticmethod
    def validate_symbol(symbol) -> bool:
        """
        return True if symbol is valid
        """
        return (len(symbol) <= const.SYMBOL_MAX_LEN) and symbol.isalpha() and symbol.isupper()

    @staticmethod
    def validate_desc(desc) -> bool:
        """
        return true if desc is valid
        """
        return len(desc) <= const.DESC_MAX_LEN and desc.isprintable()

    @classmethod
    def parse_request_json_with_symbol(cls):
        """
        parse symbol and description from request
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            name=StockModel.JSON_SYMBOL_STR,
            type=str,
            required=True,
            trim=True,
            help='Stock symbol is missing')
        parser.add_argument(
            name=StockModel.JSON_DESC_STR,
            type=str,
            required=True,
            trim=True,
            help='Stock description is missing')
        result = parser.parse_args(strict=False)  # only the two argument can be in the request
        current_app.logger.debug('in parse')
        current_app.logger.debug(dict(parser.parse_args()))

        # validation on parse data
        if not cls.validate_symbol(result[StockModel.JSON_SYMBOL_STR]):
            abort(400, message='Symbol incorrect')
        if not cls.validate_desc(result[StockModel.JSON_DESC_STR]):
            abort(400, message='Description incorrect')

        return result

    @classmethod
    def parse_request_json(cls):
        """
        parse desc from request
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            name=StockModel.JSON_DESC_STR,
            type=str,
            required=True,
            trim=True,
            help='Stock description is missing')
        current_app.logger.debug('in parse')
        current_app.logger.debug(dict(parser.parse_args()))
        result = parser.parse_args(strict=False)  # only the one argument can be in the request
        # validation on parse data
        if not cls.validate_symbol(result[StockModel.JSON_SYMBOL_STR]):
            abort(400, message='Symbol incorrect')

        return result

    @classmethod
    def find_by_symbol(cls, symbol):
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        return cls.query.filter_by(symbol=symbol).first()  # SQLAlchemy -> SELECT * FROM stock WHERE symbol=symbol

    def json(self) -> dict:
        """
        create JSON for the stock details
        """
        return {
            'symbol': self.symbol,
            'desc': self.desc,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'price': self.price
        }

    def detailed_json(self) -> dict:
        """
        create JSON for the stock details and stock's positions
        """
        return {
            'symbol': self.symbol,
            'desc': self.desc,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'price': self.price,
            'positions':
                [position.json() for position in self.positions.all()]
        }

    def save_stock_details(self) -> bool:
        """
        update or insert symbol and desc for stock
        :rtype: True for success, False for failure
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except IntegrityError:  # unique constraint violation
            db.session.rollback()
            return False

    def del_stock(self):
        """
        delete stock from DB
        """
        db.session.delete(self)
        db.session.commit()
