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
        current_app.logger.debug('func: get, stock={}'.format(stock.json()))
        return stock.detailed_json() if stock else ({'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND)

    def post(self, symbol):
        """
        POST request - json required
        {desc: description}
        """
        stock = StockModel(symbol, StockModel.parse_request_json()[StockModel.JSON_DESC_STR])
        if stock.save_stock_details():
            return stock.json(), HTTPStatus.CREATED
        else:
            return {'message': 'Stock {} already exist'.format(symbol)}, HTTPStatus.BAD_REQUEST

    def put(self, symbol):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        stock_req = StockModel.parse_request_json_with_symbol()
        stock = StockModel(**stock_req)
        return stock.json() if stock.save_stock_details() else ({'message': 'error when saving stock {}'.format(symbol)}, HTTPStatus.BAD_REQUEST)

    def delete(self, symbol):
        """
        DEL request - no json required
        """
        stock = StockModel.find_by_symbol(symbol)
        if stock:
            return stock.json() if stock.del_stock() else ({'message': 'error when delete'}, HTTPStatus.CONFLICT)
        else:
            return {'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND


class StockList(Resource):

    def get(self):
        return {'stocks': [stock.detailed_json() for stock in StockModel.query.all()]}