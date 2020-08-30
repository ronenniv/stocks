from flask_restful import Resource

from http import HTTPStatus

from models.cash import CashModel

MESSAGE = 'message'
CASH_NOT_FOUND = 'Cash balance not found'
ERROR_SAVE_BAL = 'Error in saving balance'
ERROR_UPDATE_BAL = 'Error in updating balance'


class Cash(Resource):

    def get(self):
        """
        GET request - no json required
        """
        cash = CashModel.get_details()  # None if no cash in DB
        return cash.json() if cash else ({MESSAGE: CASH_NOT_FOUND}, HTTPStatus.BAD_REQUEST)

    def post(self):
        """
        POST request
        {balance: amount}
        """
        cash = CashModel()
        cash.balance = cash.parse_balance_from_json()  # get balance from JSON
        return cash.json() if cash.save_details() else ({MESSAGE: ERROR_SAVE_BAL}, HTTPStatus.BAD_REQUEST)

    def put(self):
        """
        PUT request
        {balance: amount}
        """
        cash = CashModel()
        cash.balance = cash.parse_balance_from_json()

        return cash.json() if cash.update_details() \
            else ({MESSAGE: ERROR_UPDATE_BAL}, HTTPStatus.BAD_REQUEST)
