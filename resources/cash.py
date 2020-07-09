from flask import current_app  # for debugging

from flask_restful import Resource

from http import HTTPStatus

from models.cash import CashModel


class Cash(Resource):

    def get(self):
        """
        GET request - no json required
        """
        cash = CashModel.get_details()  # None if no cash in DB
        return cash.json() if cash else ({'message': 'Cash balance not found'}, HTTPStatus.BAD_REQUEST)

    def post(self):
        """
        POST request
        {balance: amount}
        """
        cash = CashModel()
        cash.balance = cash.parse_balance_from_json()  # get balance from JSON
        return cash.json() if cash.save_details() else ({'message': 'Error in saving balance'}, HTTPStatus.BAD_REQUEST)

    def put(self):
        """
        PUT request
        {balance: amount}
        """
        cash = CashModel()
        cash.balance = cash.parse_balance_from_json()

        return cash.json() if cash.update_details() \
            else ({'message': 'Error in updating balance'}, HTTPStatus.BAD_REQUEST)
