import logging
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus

from flask_restful import Resource

from models.stock import StockModel, DESC

MESSAGE = 'message'
STOCK_EXIST = 'Stock {} already exist'
STOCK_NOT_FOUND = 'Stock {} not found'
ERROR_UPDATE_STOCK = 'Error when updating stock {}'
ERROR_SAVE_STOCK = 'Error when saving stock {}'
ERROR_DEL_STOCK = 'Error to delete stock {}'


class Stock(Resource):

    @classmethod
    def get(cls, symbol: str):
        """
        GET request - no json required
        """
        symbol = symbol.upper()
        if stock := StockModel.find_by_symbol(symbol):
            # stock exist in DB
            return stock.detailed_json()
        else:
            return {MESSAGE: STOCK_NOT_FOUND.format(symbol)}, HTTPStatus.NOT_FOUND

    @classmethod
    def post(cls, symbol: str):
        """
        POST request - json required
        {desc: description}
        """
        symbol = symbol.upper()
        stock = StockModel(symbol, StockModel.parse_request_json()[DESC])
        if stock.save_details():
            # stock created in DB
            return stock.json(), HTTPStatus.CREATED
        else:
            return {MESSAGE: STOCK_EXIST.format(symbol)}, HTTPStatus.BAD_REQUEST

    @classmethod
    def put(cls, symbol: str):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        symbol = symbol.upper()
        stock_req = StockModel.parse_request_json_with_symbol()  # get symbol, desc from payload
        if stock := StockModel.find_by_symbol(symbol):
            # stock is exist, then need to update symbol and desc
            return stock.json() if stock.update_symbol_and_desc(**stock_req) \
                else ({MESSAGE: ERROR_UPDATE_STOCK.format(symbol)}, HTTPStatus.BAD_REQUEST)
        else:
            # stock not found, then create new one
            stock = StockModel(**stock_req)
            return stock.json() if stock.save_details() \
                else ({MESSAGE: ERROR_SAVE_STOCK.format(symbol)}, HTTPStatus.BAD_REQUEST)

    @classmethod
    def delete(cls, symbol: str):
        """
        DEL request - no json required
        """
        symbol = symbol.upper()
        if stock := StockModel.find_by_symbol(symbol):
            # stock exist in DB
            return stock.detailed_json() if stock.del_stock() \
                else ({MESSAGE: ERROR_DEL_STOCK.format(symbol)}, HTTPStatus.CONFLICT)
        else:
            return {MESSAGE: STOCK_NOT_FOUND.format(symbol)}, HTTPStatus.NOT_FOUND


class StockList(Resource):

    @classmethod
    def get(cls):
        # create list of all stocks
        stocks_list = StockModel.query.all()
        logging.debug(f"StocksList.get, stocks_list={stocks_list}")
        executor = ThreadPoolExecutor()
        # create json for each stock
        # to support thread need to provide current_app for debugging
        stocks_futures = [executor.submit(stock.detailed_json) for stock in stocks_list]
        return {'stocks': [stock.result() for stock in stocks_futures]}
