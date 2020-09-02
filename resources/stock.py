import logging
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus

from flask_restful import Resource
from flask import request
from marshmallow import ValidationError

from models.stock import StockModel, DESC
from schemas.stock import StockSchema

MESSAGE = 'message'
STOCK_EXIST = 'Stock {} already exist'
STOCK_NOT_FOUND = 'Stock {} not found'
ERROR_UPDATE_STOCK = 'Error when updating stock {}'
ERROR_SAVE_STOCK = 'Error when saving stock {}'
ERROR_DEL_STOCK = 'Error to delete stock {}'

stock_schema = StockSchema()
stock_list_schema = StockSchema(many=True)


class Stock(Resource):

    @classmethod
    def get(cls, symbol: str):
        """
        GET request - no json required
        """
        symbol = symbol.upper()
        if stock := StockModel.find_by_symbol(symbol):
            # stock exist in DB
            return stock_schema.dump(stock)
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
            return stock_schema.dump(stock), HTTPStatus.CREATED
        else:
            return {MESSAGE: STOCK_EXIST.format(symbol)}, HTTPStatus.BAD_REQUEST

    @classmethod
    def put(cls, symbol: str):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        symbol = symbol.upper()
        stock_json = request.get_json()
        if errors := stock_schema.validate(stock_json):
            # errors in payload
            logging.error(errors)
            return {MESSAGE: ERROR_SAVE_STOCK.format(symbol)}, HTTPStatus.BAD_REQUEST
        if stock := StockModel.find_by_symbol(symbol):
            # stock is exist, then need to update symbol and desc
            return stock_schema.dump(stock) if stock.update_symbol_and_desc(**stock_schema.load(stock_json)) \
                else ({MESSAGE: ERROR_UPDATE_STOCK.format(symbol)}, HTTPStatus.BAD_REQUEST)
        else:
            # stock not found, then create new one
            new_stock = stock_schema.load(stock_json)
            stock = StockModel(**new_stock)
            return stock_schema.dump(stock) if stock.save_details() \
                else ({MESSAGE: ERROR_SAVE_STOCK.format(symbol)}, HTTPStatus.BAD_REQUEST)

    @classmethod
    def delete(cls, symbol: str):
        """
        DEL request - no json required
        """
        symbol = symbol.upper()
        if stock := StockModel.find_by_symbol(symbol):
            # stock exist in DB
            return stock if stock.del_stock() \
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
