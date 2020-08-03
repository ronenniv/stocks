from db import db

from datetime import date

from flask_restful import reqparse

from models.stock import StockModel


class PositionsModel(db.Model):  # extend db.Model from SQLAlchemy

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

    @staticmethod
    def unit_cost_validation(value):
        value = float(value)
        if value != round(value, 2):
            raise ValueError('Not a valid unit cost number')
        return value

    @classmethod
    def parse_request_json(cls):
        """
        parse position details from request
        {"date": <date>,
         "quantity": <quantity>,
         "unit_cost": <unit_cost>}
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=PositionsModel.JSON_DATE_STR,
                            type=lambda s: date.fromisoformat(s),
                            required=True,
                            trim=True,
                            help='Date is missing or invalid')
        parser.add_argument(name=PositionsModel.JSON_QUANTITY_STR,
                            type=int,
                            required=True,
                            trim=True,
                            help='Quantity is missing or invalid')
        parser.add_argument(name=PositionsModel.JSON_UNIT_COST_STR,
                            type=cls.unit_cost_validation,
                            required=True,
                            trim=True)
        return parser.parse_args(strict=True)  # only the specific argument can be in the request

    @classmethod
    def parse_request_json_position_id(cls):
        """
        parse position id from request
        {"position_id": <position_id>
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=PositionsModel.JSON_POSITION_ID_STR,
                            type=int,
                            required=True,
                            trim=True,
                            help='Position id is missing or invalid')
        return parser.parse_args(strict=True)  # only the one argument can be in the request

    @classmethod
    def find_by_symbol(cls, symbol):
        """
        find stock in DB according to symbol
        if found, return list of positions for the stock, else None
        """
        if stock := StockModel.find_by_symbol(symbol):
            # if stock exist, get all positions according to stock id
            return cls.query.filter_by(stock_id=stock.id).order_by(
                PositionsModel.position_date).all()  # SQLAlchemy -> SELECT * FROM position WHERE stock_id=stock_id
        else:
            return None

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

    def save_details(self) -> bool:
        """
        insert position details for a stock
        """
        if stock := StockModel.find_by_symbol(self.symbol):
            # stock is in DB, then add position and update stock quantity and cost
            self.stock_id = stock.id
            db.session.add(self)
            # calc by adding unit_cost and quantity to existing
            stock.calc_unit_cost_and_quantity(self.unit_cost, self.quantity)
            self.calc_flag = True  # set the flag to show position got calculated
            db.session.commit()
            return True
        else:
            # stock not found
            return False

    def del_position(self, symbol) -> bool:
        """
        delete stock from DB
        :return True for success, False for failure
        """
        # find the stock and calculate the updated unit_cost and quantity
        stock = StockModel.find_by_symbol(symbol)
        if self in stock.positions:  # check if the position belongs to the stock
            db.session.delete(self)
            stock.calc_unit_cost_and_quantity(self.unit_cost, -self.quantity)
            db.session.commit()
            return True
        else:
            # not match between position and the stock symbol
            return False
