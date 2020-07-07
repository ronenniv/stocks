from db import db

from flask import current_app  # for debugging

from flask_restful import reqparse, abort

from sqlalchemy.exc import IntegrityError

import models.constants as const


class CashModel(db.Model):  # extend db.Model for SQLAlechemy

    JSON_BALANCE_STR = 'balance'

    __tablename__ = 'cash'

    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float(precision=const.PRICE_PRECISION), nullable=False)

    def __init__(self, id=1, balance=0, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.balance = balance

    def __repr__(self):
        return str(self.json())

    @classmethod
    def parse_request_json(cls):
        """
        parse desc from request
        :return parsed arg as dict
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            name=CashModel.JSON_BALANCE_STR,
            type=float,
            required=True,
            trim=True,
            help='Balance amount is missing')
        current_app.logger.debug('func: parse_request_json, args={}'.format(dict(parser.parse_args())))
        result = parser.parse_args(strict=False)  # only the one argument can be in the request
        # validation on parse data
        # TODO implement validations
        return result

    def json(self) -> dict:
        """
        create JSON for the stock details
        """
        return {
            'id': self.id,
            'balance': self.balance
        }

    def save_details(self) -> bool:
        """
        insert cash balance
        :return: True for success, False for failure
        """
        current_app.logger.debug('func: save_details, self={}'.format(self))
        if self.query.first():
            # cash row already created. not to create more then one row
            return False
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except IntegrityError:  # unique constraint violation
            current_app.logger.debug('func: save_details, exception: IntegrityError, self: {}'.format(self))
            db.session.rollback()
            return False

    def update_details(self, balance=0.0) -> bool:
        """
        update or insert cash balance
        :return: True for success, False for failure
        """
        current_app.logger.debug('func: update_details1, self={}'.format(self))
        if cash := CashModel.get_details():
            # cash row already created. update balance
            self.id = cash.id
            self.query.filter_by(id=self.id).update(dict(balance=self.balance))
            db.session.commit()
            current_app.logger.debug('func: update_details2.1, self={}'.format(CashModel.get_details()))
            return True
        else:
            try:
                db.session.add(self)
                db.session.commit()
                current_app.logger.debug('func: update_details4, self={}'.format(self))
                return True
            except IntegrityError:  # unique constraint violation
                current_app.logger.debug('func: update_details5, exception: IntegrityError, self: {}'.format(self))
                db.session.rollback()
                return False

    @classmethod
    def get_details(cls):
        return cls.query.get(1)
