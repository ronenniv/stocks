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
    JSON_POSITION_ID_STR = 'position_id'

    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    position_date = db.Column(db.Date)
    unit_cost = db.Column(db.Float)
    # unit_cost = db.Column(db.Float(precision=const.PRICE_PRECISION))
    calc_flag = db.Column(db.Boolean)  # indicator for calc
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)  # foreign key to stock table

    def __init__(self, symbol, quantity, position_date, unit_cost, calc_flag=False, stock_id=None, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.quantity = quantity
        self.position_date = position_date
        self.unit_cost = unit_cost
        self.calc_flag = calc_flag
        self.stock_id = stock_id

    def __repr__(self):
        return str(self.json())

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
            help='date field is missing or invalid')
        parser.add_argument(
            name=PositionsModel.JSON_QUANTITY_STR,
            type=int,
            required=True,
            trim=True,
            help='quantity field is missing or invalid')
        parser.add_argument(
            name=PositionsModel.JSON_UNIT_COST_STR,
            type=float,
            required=True,
            trim=True,
            help='unit cost is missing or invalid')
        current_app.logger.debug(dict(parser.parse_args()))
        return parser.parse_args(strict=True)  # only the one argument can be in the request

    @classmethod
    def parse_request_json_position_id(cls):
        """
        parse position id from request
        {"position_id": <position_id>
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            name=PositionsModel.JSON_POSITION_ID_STR,
            type=int,
            required=True,
            trim=True,
            help='position id field is missing or invalid')
        current_app.logger.debug('func: parse_request_json_position_id, parse={}'.format(dict(parser.parse_args())))
        return parser.parse_args(strict=True)  # only the one argument can be in the request

    @classmethod
    def find_by_symbol(cls, symbol):
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        stock = StockModel.find_by_symbol(symbol)
        if stock:
            stock_id = stock.id
        else:
            return None
        return cls.query.filter_by(stock_id=stock_id).order_by(
            PositionsModel.position_date).all()  # SQLAlchemy -> SELECT * FROM position WHERE stock_id=stock_id

    @classmethod
    def find_by_position_id(cls, position_id):
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        return cls.query.get(position_id)  # SQLAlchemy -> SELECT * FROM position WHERE id=position_id

    def json(self) -> dict:
        """
        create JSON for the stock details
        """
        return {
            'position_id': self.id,
            'date': self.position_date.strftime('%Y-%m-%d'),
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'calc_flag': self.calc_flag,
            'stock_id': self.stock_id
        }

    def save_details(self):
        """
        insert position details for a stock
        """
        stock = StockModel.find_by_symbol(self.symbol)
        self.stock_id = stock.id
        current_app.logger.debug('func: save_details, self={}'.format(self.json()))
        db.session.add(self)
        # find the stock and update its unit_cost and quantity
        current_app.logger.debug('func: save_details, stock={}'.format(stock))
        # calc by adding unit_cost and quantity to existing
        stock.calc_unit_cost_and_quantity(self.unit_cost, self.quantity)
        self.calc_flag = True  # set the flag to show position got calculated
        db.session.commit()

    def del_position(self, symbol) -> bool:
        """
        delete stock from DB
        :return True for success, False for failure
        """
        # find the stock and calculate the updated unit_cost and quantity
        stock = StockModel.find_by_symbol(symbol)
        if stock.id == self.stock_id:
            db.session.delete(self)
            current_app.logger.debug('func: del_position, stock={}'.format(stock.detailed_json()))
            stock.calc_unit_cost_and_quantity(self.unit_cost, -self.quantity)
            db.session.commit()
            return True
        else:
            # not match between position stock id and the stock symbol
            return False


    def get_stock_id(self):
        """
        search for stock id according to the stock symbol
        :return:
        """
        pass
