from flask_restful import Resource

from http import HTTPStatus

from concurrent.futures import ThreadPoolExecutor

import logging

from models.stock import StockModel


class Stock(Resource):

    def get(self, symbol):
        """
        GET request - no json required
        """
        symbol = symbol.upper()
        if stock := StockModel.find_by_symbol(symbol):
            # stock exist in DB
            return stock.detailed_json()
        else:
            return {'message': f'Stock {symbol} not found'}, HTTPStatus.NOT_FOUND

    def post(self, symbol):
        """
        POST request - json required
        {desc: description}
        """
        symbol = symbol.upper()
        stock = StockModel(symbol, StockModel.parse_request_json()[StockModel.JSON_DESC_STR])
        if stock.save_details():
            # stock created in DB
            return stock.json(), HTTPStatus.CREATED
        else:
            return {'message': f'Stock {symbol} already exist'}, HTTPStatus.BAD_REQUEST

    def put(self, symbol):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        symbol = symbol.upper()
        stock_req = StockModel.parse_request_json_with_symbol()  # get symbol, desc from payload
        if stock := StockModel.find_by_symbol(symbol):
            # stock is exist, then need to update symbol and desc
            return stock.json() if stock.update_symbol_and_desc(**stock_req) \
                else ({'message': f'Error when updating stock {symbol}'}, HTTPStatus.BAD_REQUEST)
        else:
            # stock not found, then create new one
            stock = StockModel(**stock_req)
            return stock.json() if stock.save_details() \
                else ({'message': f'Error when saving stock {symbol}'}, HTTPStatus.BAD_REQUEST)

    def delete(self, symbol):
        """
        DEL request - no json required
        """
        symbol = symbol.upper()
        if stock := StockModel.find_by_symbol(symbol):
            # stock exist in DB
            return stock.detailed_json() if stock.del_stock() \
                else ({'message': f'Error when trying to delete stock {symbol}'}, HTTPStatus.CONFLICT)
        else:
            return {'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND


class StockList(Resource):

    def get(self):
        # create list of all stocks
        stocks_list = StockModel.query.all()
        logging.debug(f"StocksList.get, stocks_list={stocks_list}")
        executor = ThreadPoolExecutor()
        # create json for each stock
        # to support thread need to provide current_app for debugging
        stocks_futures = [executor.submit(stock.detailed_json) for stock in stocks_list]
        return {'stocks': [stock.result() for stock in stocks_futures]}
