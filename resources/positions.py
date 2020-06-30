from flask import current_app # for debugging

from flask_restful import Resource

from http import HTTPStatus

from models.positions import PositionsModel


class Position(Resource):

    def get(self, symbol):
        """
        GET request - no json required
        """
        current_app.logger.debug('func: get, symbol={}'.format(symbol))

        if positions_list := PositionsModel.find_by_symbol(symbol):
            result = [position.json() for position in positions_list]
            return result
        else:
            return {'message': 'Positions for symbol {} not found'.format(symbol)}, HTTPStatus.NOT_FOUND

    def post(self, symbol):
        """
        POST request - json required
        {desc: description}
        """

        position_args = PositionsModel.parse_request_json()
        position = PositionsModel(symbol,
                                  position_args[PositionsModel.JSON_QUANTITY_STR],
                                  position_args[PositionsModel.JSON_DATE_STR],
                                  position_args[PositionsModel.JSON_UNIT_COST_STR])
        current_app.logger.debug('func: post before save position, position={}'.format(position.json()))
        position.save_details()
        current_app.logger.debug('func: post after save position, position={}'.format(position.json()))
        return position.json(), HTTPStatus.CREATED

    '''
    def put(self, symbol):
        """
        PUT request - json required
        {symbol: symbol name, desc: description}
        """
        stock_req = StockModel.parse_request_json_with_symbol()
        stock = StockModel(**stock_req)
        stock.save_stock_details()
        return stock.json()
    '''

    def delete(self, symbol):
        """
        DEL request - no json required
        """
        position_id = PositionsModel.parse_request_json_position_id()['position_id']
        current_app.logger.debug('func: delete, position_id={}'.format(position_id))
        if position := PositionsModel.find_by_position_id(position_id):
            current_app.logger.debug('func: delete, position={}'.format(position))
            return position.json() if position.del_position(symbol) \
                       else \
                       {'message': 'error when trying to delete position {}'.format(position_id)}, \
                        HTTPStatus.BAD_REQUEST
        else:
            return {'message': 'Position {} not found'.format(position_id)}, HTTPStatus.NOT_FOUND
