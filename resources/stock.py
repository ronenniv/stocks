from flask import current_app # for debugging

from flask_restful import Resource

from http import HTTPStatus

from models.stock import StockModel


class Stock(Resource):

    def get(self, symbol):
        """
        GET request - no json required
        """
        if stock := StockModel.find_by_symbol(symbol):
            current_app.logger.debug('func: get, stock={}'.format(stock.json()))
        return stock.detailed_json() if stock else ({'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND)

    def post(self, symbol):
        """
        POST request - json required
        {desc: description}
        """
        stock = StockModel(symbol, StockModel.parse_request_json()[StockModel.JSON_DESC_STR])
        if stock.save_details():
            return stock.json(), HTTPStatus.CREATED
        else:
            return {'message': 'Stock {} already exist'.format(symbol)}, HTTPStatus.BAD_REQUEST

    def put(self, symbol):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        stock_req = StockModel.parse_request_json_with_symbol()  # get symbol, desc
        if stock := StockModel.find_by_symbol(symbol):
            # stock is existing, then need to update symbol and desc
            current_app.logger.debug('func: put, stock found')
            return stock.json() if stock.update_symbol_and_desc(**stock_req) \
                else ({'message': 'error when saving stock {}'.format(symbol)}, HTTPStatus.BAD_REQUEST)
        else:
            current_app.logger.debug('func: put, stock not found')
            # stock not found, then create new one
            stock = StockModel(**stock_req)
            return stock.json() if stock.save_details() \
                else ({'message': 'error when saving stock {}'.format(symbol)}, HTTPStatus.BAD_REQUEST)

    def delete(self, symbol):
        """
        DEL request - no json required
        """
        if stock := StockModel.find_by_symbol(symbol):
            return stock.json() if stock.del_stock() else ({'message': 'error when delete'}, HTTPStatus.CONFLICT)
        else:
            return {'message': 'Stock {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND


class StockList(Resource):

    def get(self):
        return {'stocks': [stock.detailed_json() for stock in StockModel.query.all()]}