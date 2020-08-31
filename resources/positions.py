from typing import Dict, List

import logging

from flask_restful import Resource

from http import HTTPStatus

from models.positions import PositionsModel, QUANTITY, POSITION_DATE, UNIT_COST

MESSAGE = 'message'


class Position(Resource):

    @classmethod
    def get(cls, symbol: str):
        """
        GET request - no json required
        """
        symbol = symbol.upper()
        logging.debug('func: get, symbol={}'.format(symbol))

        if positions_list := PositionsModel.find_by_symbol(symbol):
            # positions for symbol exist in DB
            return [position.json() for position in positions_list]
        else:
            return {MESSAGE: f'Positions for symbol {symbol} not found'}, HTTPStatus.NOT_FOUND

    @classmethod
    def post(cls, symbol: str):
        """
        POST request - json required
        {date: YYYY-MM-DD,
        quantity: int,
        unit_cost: float}
        """
        symbol = symbol.upper()
        position_args = PositionsModel.parse_request_json()
        position = PositionsModel(symbol,
                                  position_args[QUANTITY],
                                  position_args[POSITION_DATE],
                                  position_args[UNIT_COST])
        if position.save_details():
            # position saved to DB
            return position.json(), HTTPStatus.CREATED
        else:
            # error with saving positions
            return {MESSAGE: f'Position cannot be saved check if stock {symbol} exist'}

    '''
    @classmethod
    def put(cls, symbol):
        """
        PUT request - json required
        {date: symbol name, desc: description}
        """
        stock_req = StockModel.parse_request_json_with_symbol()
        stock = StockModel(**stock_req)
        stock.save_stock_details()
        return stock.json()
    '''

    @classmethod
    def delete(cls, symbol: str):
        """
        DEL request
        {position_id: int}
        """
        symbol = symbol.upper()
        position_id = PositionsModel.parse_request_json_position_id()['position_id']
        if position := PositionsModel.find_by_position_id(position_id):
            # position exist in DB
            return position.json() if position.del_position(symbol) \
                       else {MESSAGE: f'Error when trying to delete position {position_id}'}, HTTPStatus.BAD_REQUEST
        else:
            # position id not found in DB
            return {MESSAGE: f'Position {position_id} not found'}, HTTPStatus.NOT_FOUND


class PositionsList(Resource):

    @classmethod
    def get(cls):
        """
        GET request - no json required
        """
        return {'positions': [position.json() for position in PositionsModel.query.all()]}
