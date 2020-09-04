from http import HTTPStatus

from flask import request
from flask_restful import Resource

from globals.constants import *
from models.cash import CashModel
from schemas.cash import CashSchema

cash_schema = CashSchema()


class Cash(Resource):

    @classmethod
    def get(cls):
        """
        GET request - no json required
        """
        cash = CashModel.get_details()  # None if no cash in DB
        return cash_schema.dump(cash) if cash else ({MESSAGE: CASH_NOT_FOUND}, HTTPStatus.BAD_REQUEST)

    @classmethod
    def post(cls):
        """
        POST request
        {balance: amount}
        """
        cash_json = request.get_json()
        cash = cash_schema.load(cash_json)
        return cash_schema.dump(cash) if cash.save_details() else ({MESSAGE: ERROR_SAVE_BAL}, HTTPStatus.BAD_REQUEST)

    @classmethod
    def put(cls):
        """
        PUT request
        {balance: amount}
        """
        cash_json = request.get_json()
        cash = cash_schema.load(cash_json)

        return cash_schema.dump(cash) if cash.update_details() \
            else ({MESSAGE: ERROR_UPDATE_BAL}, HTTPStatus.BAD_REQUEST)

    @classmethod
    def delete(cls):
        """DEL request"""
        return {MESSAGE: CASH_DEL} if CashModel.del_balance() else ({MESSAGE: ERROR_CASH_DEL}, HTTPStatus.BAD_REQUEST)
