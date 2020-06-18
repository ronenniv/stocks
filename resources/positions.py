from flask import current_app # for debugging

from flask_restful import Resource

from http import HTTPStatus

from models.positions import PositionsModel


class Position(Resource):

    def get(self, symbol):
        """
        GET request - no json required
        """
        current_app.logger.debug('in get position')
        positions_list = PositionsModel.find_by_symbol(symbol)
        if positions_list:
            result = [position.json() for position in positions_list]
            return result
        else:
            return {'message': 'Positions for symbol {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND
'''
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
'''