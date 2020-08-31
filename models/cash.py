import logging
from typing import Dict

from sqlalchemy.exc import IntegrityError

from db import db

BalanceJSON = Dict[str, float]

NOT_VALID_BALANCE = 'Not a valid balance number'
BALANCE = 'balance'


class CashModel(db.Model):  # extend db.Model for SQLAlchemy

    __tablename__ = 'cash'

    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float(precision=2), nullable=False)

    '''
    def __init__(self, balance: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.id = 1  # only the first row
        self.balance = balance'''

    def __repr__(self):
        return f'id={self.id}, balance={self.balance}'

    @classmethod
    def balance_validation(cls, value: float) -> float:
        value = float(value)
        if value != round(value, 2):
            raise ValueError(NOT_VALID_BALANCE)
        return value

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

    @classmethod
    def del_balance(cls) -> bool:
        """:return True for delete, False for not found"""
        cash = cls.get_details()
        if cash:
            db.session.delete(cls.get_details())
            db.session.commit()
            return True
        return False

