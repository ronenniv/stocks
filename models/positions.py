from typing import List, Dict, Union

from db import db

from datetime import date

import logging

from models.stock import StockModel

# from schemas.positions import PositionSchema

PositionJSON = Dict[str, Union[int, date, float]]

NOT_VALID_COST = 'Not a valid unit cost number'
PARAM_IS_MISSING = '{} is missing or invalid'
SYMBOL = 'symbol'
QUANTITY = 'quantity'
POSITION_DATE = 'position_date'
UNIT_COST = 'unit_cost'
CALC_FLAG = 'calc_flag'
POSITION_ID = 'position_id'
STOCK_ID = 'stock_id'


class PositionsModel(db.Model):  # extend db.Model from SQLAlchemy

    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    position_date = db.Column(db.Date, nullable=False)
    unit_cost = db.Column(db.Float(precision=2), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)  # foreign key to stock table

    def __repr__(self):
        return f'id={self.id}, quantity={self.quantity}, position_date={self.position_date}, unit_cost={self.unit_cost}, stock_id={self.stock_id}'

    @classmethod
    def find_by_symbol(cls, symbol: str) -> List["PositionsModel"]:
        """
        find all positions for stock according to symbol
        :return if found, return list of positions for the stock, else None
        """
        if stock := StockModel.find_by_symbol(symbol):
            # if stock exist, get all positions according to stock id
            return cls.query.filter_by(stock_id=stock.id).order_by(
                PositionsModel.position_date).all()  # SQLAlchemy -> SELECT * FROM position WHERE stock_id=stock_id
        else:
            return None

    @classmethod
    def find_by_position_id(cls, position_id: int) -> "PositionsModel":
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        return cls.query.get(position_id)  # SQLAlchemy -> SELECT * FROM position WHERE id=position_id

    def save_details(self, symbol: str) -> bool:
        """
        insert position details for a stock
        """
        if stock := StockModel.find_by_symbol(symbol):
            # stock is in DB, then add position and update stock quantity and cost
            try:
                self.stock_id = stock.id
                db.session.add(self)
                # calc by adding unit_cost and quantity to existing
                stock.calc_unit_cost_and_quantity(self.unit_cost, self.quantity, commit_flag=False)
                db.session.commit()
                return True
            except:
                db.session.rollback()
                logging.error(f'failed to save details self={self}, symbol={symbol}')
                return False
        else:
            # stock not found
            return False

    def del_position(self, symbol: str) -> bool:
        """
        delete stock from DB
        :return True for success, False for failure
        """
        # find the stock and calculate the updated unit_cost and quantity

        try:
            db.session.delete(self)
            self.stock.calc_unit_cost_and_quantity(self.unit_cost, -self.quantity, commit_flag=False)
            db.session.commit()
            return True
        except:
            db.session.rollback()
            logging.error(f'error in del position {self}')
            return False

