from typing import List, Dict, Union

import requests
import requests.exceptions
from sqlalchemy.exc import IntegrityError
import logging

from db import db


StockJSON = Dict[str, Union[int, str, float]]
StockDetailedJSON = Dict[str, Union[int, str, float, List[StockJSON]]]

NOT_VALID_SYMBOL = 'Not a valid symbol'
NOT_VALID_DESC = 'Not a valid description'
ID = 'id'
SYMBOL = 'symbol'
DESC = 'desc'
QUANTITY = 'quantity'
UNIT_COST = 'unit_cost'
STOP_QUOTE = 'stop_quote'
PRICE = 'price'
ERR = 'ERR'
# maximum length for string fields
SYMBOL_MAX_LEN = 5  # maximum len of symbol string
DESC_MAX_LEN = 30  # maximum len of description string

# for stock price requests
TOKEN = "bs2hfe7rh5rc90r58vqg"
FINNHUB_URL = "https://finnhub.io/api/v1"


class StockModel(db.Model):  # extend db.Model for SQLAlchemy

    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(SYMBOL_MAX_LEN), nullable=False, unique=True)
    desc = db.Column(db.String(DESC_MAX_LEN), nullable=False)
    quantity = db.Column(db.Integer())
    unit_cost = db.Column(db.Float(precision=2))
    stop_quote = db.Column(db.Float(precision=2))

    # this definition comes together with the definition in
    # PositionsModel. Lazy will ask to not create entries for positions
    positions = db.relationship('PositionsModel', lazy='dynamic', backref='stock', cascade='all')

    def get_price(self) -> float:
        """get current stock price from finnhub"""
        quote_api_url = FINNHUB_URL + "/quote"
        try:
            response = requests.get(quote_api_url,
                                    params={'symbol': self.symbol, 'token': TOKEN},
                                    timeout=0.5
                                    )
            response.raise_for_status()
        except requests.exceptions.ConnectTimeout:
            logging.warning(f'func: get_current_price ConnectTimeout')
            self._price = ERR
        except Exception as e:
            logging.error(f'func: get_current_price Exception {e}')
            self._price = ERR
        else:
            json_response = response.json()
            if 'error' in json_response:
                # symbol not found
                logging.error(f'func: get_current_price, symbol {self.symbol} not found')
                self._price = ERR
            else:
                self._price = json_response['c']
        finally:
            return self._price

    price = property(fget=get_price, fset=None, fdel=None, doc="Get current price")

    def __repr__(self) -> str:
        return f'id={self.id}, symbol={self.symbol}, desc={self.desc}, quantity={self.quantity}, unit_cost={self.unit_cost}, stop_quote={self.stop_quote} '

    @classmethod
    def find_by_symbol(cls, symbol: str) -> "StockModel":
        """
        find record in DB according to symbol
        if found, return object with stock details, otherwise None
        """
        # SELECT * FROM stock WHERE symbol=symbol
        return cls.query.filter_by(symbol=symbol).first()

    @classmethod
    def find_by_stock_id(cls, stock_id: int) -> "StockModel":
        """
        find record in DB according to stock_id
        if found, return object with stock details, otherwise None
        """
        # SELECT * FROM stock WHERE symbol=symbol
        return cls.query.filter_by(stock_id=stock_id).first()

    def _json(self) -> StockJSON:
        """
        create JSON for the stock details. not including current price
        """
        json_dict = {
            ID: self.id,
            SYMBOL: self.symbol,
            DESC: self.desc,
            QUANTITY: self.quantity,
            UNIT_COST: self.unit_cost
        }
        if self.stop_quote:
            json_dict[STOP_QUOTE] = self.stop_quote
        return json_dict

    def _detailed_json(self) -> StockDetailedJSON:
        """
        create JSON for the stock details, current stock price and stock's positions
        """
        json_dict = self.json()
        # add the current price to json
        json_dict[PRICE] = self.price
        # add the positions list to the json
        positions_list = {'positions': [position.json() for position in self.positions.all()]}
        json_dict.update(positions_list)
        return json_dict

    def _detailed_stock(self) -> StockDetailedJSON:
        """
        create JSON for the stock details, current stock price and stock's positions
        """
        stock_json = stock_schema.dump(self)
        # add the current price to json
        stock_json[PRICE] = self.price
        # add the positions list to the json
        positions_list = self.positions.all()
        stock_json.update(positions_list)

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

    def update_symbol_and_desc(self, symbol: str, desc: str) -> bool:
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

    def calc_unit_cost_and_quantity(self, unit_cost: float, quantity: int, commit_flag: bool):
        """calculate the unit cost and the quantity according to the position
        positive quantity for adding, negative quantity for removing"""
        try:
            self.unit_cost = round(
                ((self.unit_cost * self.quantity) + (unit_cost * quantity)) / (self.quantity + quantity), 2)
            self.quantity = self.quantity + quantity
        except ZeroDivisionError:
            # all positions are sold -> quantity is zero
            self.unit_cost = 0
            self.quantity = 0
        if commit_flag:
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
