from db import db

from datetime import date

from flask import current_app  # for debugging

from flask_restful import reqparse

import models.constants as const
from models.stock import StockModel


class PositionsModel(db.Model):  # extend db.Model for SQLAlechemy

    JSON_SYMBOL_STR = 'symbol'
    JSON_DATE_STR = 'date'
    JSON_QUANTITY_STR = 'quantity'
    JSON_UNIT_COST_STR = 'unit_cost'

    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(const.SYMBOL_MAX_LEN))
    quantity = db.Column(db.Integer)
    position_date = db.Column(db.Date)
    unit_cost = db.Column(db.Float(precision=const.PRICE_PRECISION))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)  # foreign key to stock table

    def __init__(self, symbol, quantity, position_date, unit_cost, stock_id=None, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.quantity = quantity
        self.position_date = position_date
        self.unit_cost = unit_cost
        self.stock_id = stock_id

    @classmethod
    def parse_request_json(cls):
        """
        parse position details from request
        {"date": <date>,
         "quantity": <quantity>,
         "unit_cost": <unit_cost>}
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            name=PositionsModel.JSON_DATE_STR,
            type=lambda s: date.fromisoformat(s),
            required=True,
            trim=True,
            help='date field is missing')
        parser.add_argument(
            name=PositionsModel.JSON_QUANTITY_STR,
            type=int,
            required=True,
            trim=True,
            help='quantity field is missing')
        parser.add_argument(
            name=PositionsModel.JSON_UNIT_COST_STR,
            type=float,
            required=True,
            trim=True,
            help='unit cost is missing')
        current_app.logger.debug(dict(parser.parse_args()))
        return parser.parse_args(strict=False)  # only the one argument can be in the request

    @classmethod
    def find_by_symbol(cls, symbol):
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        return cls.query.filter_by(symbol=symbol).all()  # SQLAlchemy -> SELECT * FROM stock WHERE symbol=symbol

    def json(self) -> dict:
        """
        create JSON for the stock details
        """
        return {
            'symbol': self.symbol,
            'date': self.position_date.strftime('%Y-%m-%d'),
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'stock_id': self.stock_id

        }

    def save_position_details(self):
        """
        insert position details for a stock
        """
        current_app.logger.debug('func: save_position_details, symbol={}'.format(self.symbol))
        self.stock_id = StockModel.find_by_symbol(self.symbol).id
        current_app.logger.debug(self.json())
        db.session.add(self)
        current_app.logger.debug('func: save_position_details, after session_add')
        db.session.commit()
        current_app.logger.debug('func: save_position_details, after commit')

    def del_position(self):
        """
        delete stock from DB
        """
        db.session.delete(self)
        db.session.commit()

    def get_stock_id(self):
        """
        search for stock id according to the stock symbol
        :return:
        """
        pass
