from flask import current_app # for debugging

from flask_restful import Resource

from http import HTTPStatus

from models.stock import StockModel


class Stock(Resource):

    def get(self, symbol):
        """
        GET request - no json required
        """
        stock = StockModel.find_by_symbol(symbol)
        if stock:
            return stock.json()
        else:
            return {'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND

    def post(self, symbol):
        """
        POST request - json required
        {desc: description}
        """
        stock = StockModel(symbol, StockModel.parse_request_json()[StockModel.JSON_DESC_STR])
        if stock.save_stock_details():
            return stock.json(), HTTPStatus.CREATED
        else:
            return {'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND

    def put(self, symbol):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        stock_req = StockModel.parse_request_json_with_symbol()
        stock = StockModel(**stock_req)
        stock.save_stock_details()
        return stock.json()

    def delete(self, symbol):
        """
        DEL request - no json required
        """
        stock = StockModel.find_by_symbol(symbol)
        if stock:
            stock.del_stock()
            return stock.json()
        else:
            return {'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND


class StockList(Resource):

    def get(self):
        return {'stocks': [stock.json() for stock in StockModel.query.all()]}