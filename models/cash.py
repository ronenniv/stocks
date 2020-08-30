import logging
from typing import Dict

from flask_restful import reqparse
from sqlalchemy.exc import IntegrityError

from db import db

BalanceJSON = Dict[str, float]


class CashModel(db.Model):  # extend db.Model for SQLAlchemy

    BALANCE_STR = 'balance'

    __tablename__ = 'cash'

    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float(precision=2), nullable=False)

    def __init__(self, balance=0, **kwargs):
        super().__init__(**kwargs)
        self.id = 1  # only the first row
        self.balance = balance

    def __repr__(self):
        return str(self.json())

    @staticmethod
    def balance_validation(value: float) -> float:
        value = float(value)
        if value != round(value, 2):
            raise ValueError('Not a valid balance number')
        return value

    @classmethod
    def parse_balance_from_json(cls) -> float:
        """
        parse desc from request
        :return balance from JSON
        """
        parser = reqparse.RequestParser()
        parser.add_argument(name=CashModel.JSON_BALANCE_STR,
                            type=cls.balance_validation,
                            required=True,
                            trim=True)
        return parser.parse_args(strict=True)[cls.JSON_BALANCE_STR]  # return the balance from json

    def json(self) -> BalanceJSON:
        """
        create JSON for the stock details
        """
        return {
            self.BALANCE_STR: self.balance
        }

    def save_details(self) -> bool:
        """
        insert cash balance
        :return: True for success, False for failure
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except IntegrityError as e:  # unique constraint violation
            logging.info(f'func: save_details, exception {e}, self: {self}')
            db.session.rollback()
            return False

    def update_details(self) -> bool:
        """
        update or insert cash balance
        :return: True for success, False for failure
        """
        # try to add balance. if exist then try to update
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except IntegrityError:
            try:
                db.session.rollback()
                self.query.filter_by(id=self.id).update(dict(balance=self.balance))
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                logging.error(f'func: update_details, exception {e}, self: {self}')
                return False

    @classmethod
    def get_details(cls) -> "CashModel":
        return cls.query.get(1)
