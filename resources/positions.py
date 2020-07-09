from flask import current_app  # for debugging

from flask_restful import Resource

from http import HTTPStatus

from models.positions import PositionsModel


class Position(Resource):

    def get(self, symbol):
        """
        GET request - no json required
        """
        symbol = symbol.upper()
        current_app.logger.debug('func: get, symbol={}'.format(symbol))

        if positions_list := PositionsModel.find_by_symbol(symbol):
            # positions for symbol exist in DB
            return [position.json() for position in positions_list]
        else:
            return {'message': f'Positions for symbol {symbol} not found'}, HTTPStatus.NOT_FOUND

    def post(self, symbol):
        """
        POST request - json required
        {date: YYYY-MM-DD,
        quantity: int,
        unit_cost: float}
        """
        symbol = symbol.upper()
        position_args = PositionsModel.parse_request_json()
        position = PositionsModel(symbol,
                                  position_args[PositionsModel.JSON_QUANTITY_STR],
                                  position_args[PositionsModel.JSON_DATE_STR],
                                  position_args[PositionsModel.JSON_UNIT_COST_STR])
        if position.save_details():
            # position saved to DB
            return position.json(), HTTPStatus.CREATED
        else:
            # error with saving positions
            return {'message': f'Position cannot be saved check if stock {symbol} exist'}

    '''
    def put(self, symbol):
        """
        PUT request - json required
        {date: symbol name, desc: description}
        """
        stock_req = StockModel.parse_request_json_with_symbol()
        stock = StockModel(**stock_req)
        stock.save_stock_details()
        return stock.json()
    '''

    def delete(self, symbol):
        """
        DEL request
        {position_id: int}
        """
        symbol = symbol.upper()
        position_id = PositionsModel.parse_request_json_position_id()['position_id']
        if position := PositionsModel.find_by_position_id(position_id):
            # position exist in DB
            return position.json() if position.del_position(symbol) \
                       else {'message': f'Error when trying to delete position {position_id}'}, HTTPStatus.BAD_REQUEST
        else:
            # position id not found in DB
            return {'message': f'Position {position_id} not found'}, HTTPStatus.NOT_FOUND


class PositionsList(Resource):

    def get(self):
        """
        GET request - no json required
        """
        return {'positions': [position.json() for position in PositionsModel.query.all()]}
