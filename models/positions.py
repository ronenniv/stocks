from db import db

from datetime import date

from flask import current_app  # for debugging

from flask_restful import reqparse

import models.constants as const


class PositionsModel(db.Model):  # extend db.Model for SQLAlechemy

    JSON_SYMBOL_STR = 'symbol'
    JSON_DATE_STR = 'date'
    JSON_QUANTITY_STR = 'quantity'
    JSON_UNIT_COST_STR = 'unit_cost'

    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(const.SYMBOL_MAX_LEN))
    quantity = db.Column(db.Integer)
    date = db.Column(db.Date)
    unit_cost = db.Column(db.Float(precision=const.PRICE_PRECISION))

    stock_id = db.Column(db.Integer, db.ForeignKey(stock.id))
    stock = db.relationship('StockModel', lazy='dynamic')  # this definition comes together with the defintion in
    # StockModel. Lazy will ask to not create entries for positions

    def __init__(self, symbol, quantity, date, unit_cost, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.quantity = quantity
        self.date = date
        self.unit_cost = unit_cost

    '''
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
        current_app.logger.debug('in parse')
        current_app.logger.debug(dict(parser.parse_args()))
        return parser.parse_args(strict=False)  # only the two argument can be in the request
        '''

    @classmethod
    def parse_request_json(cls):
        """
        parse position details from request
        {"symbol": <symbol>,
         "date": <date>,
         "quantity": <quantity>,
         "unit_cost": <unit_cost>}
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            name=StockModel.JSON_SYMBOL_STR,
            type=str,
            required=True,
            trim=True,
            help='Stock symbol is missing')
        parser.add_argument(
            name=StockModel.JSON_DATE_STR,
            type=date.fromisoformat('YYYY-MM-DD'),
            required=True,
            trim=True,
            help='Stock date is missing')
        parser.add_argument(
            name=StockModel.JSON_QUANTITY_STR,
            type=int,
            required=True,
            trim=True,
            help='Stock quantity is missing')
        parser.add_argument(
            name=StockModel.JSON_UNIT_COST_STR,
            type=float,
            required=True,
            trim=True,
            help='Stock unit cost is missing')
        current_app.logger.debug(dict(parser.parse_args()))
        return parser.parse_args(strict=False)  # only the one argument can be in the request

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

    def save_stock_details(self):
        """
        update or insert symbol and desc for stock
        """
        stock = StockModel.find_by_symbol(self.symbol)
        if stock:
            stock.symbol = self.symbol
            stock.desc = self.desc
        else:
            stock = StockModel(self.symbol, self.desc)  # copy only symbol and desc
        current_app.logger.debug('stock found with {} {}'.format(stock.symbol, stock.desc))
        db.session.add(stock)
        db.session.commit()

    def del_stock(self):
        """
        delete stock from DB
        """
        db.session.delete(self)
        db.session.commit()
