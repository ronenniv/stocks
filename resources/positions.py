from typing import Dict, List

import logging

from flask import request
from flask_restful import Resource

from http import HTTPStatus

from models.positions import PositionsModel, SYMBOL
from schemas.positions import PositionSchema

from marshmallow import ValidationError

MESSAGE = 'message'
POSITION_ID_NOT_FOUND = 'Position id {} not found'
POSITION_ERR_DEL = 'Error when trying to delete position {}'
POSITION_ERR_SAVE = 'Position cannot be saved check if stock {} exist'
POSITION_SYMBOL_NOT_FOUND = 'Positions for symbol {} not found'

position_schema = PositionSchema()
position_list_schema = PositionSchema(many=True)


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
            return position_list_schema.dump(positions_list)
        else:
            return {MESSAGE: POSITION_SYMBOL_NOT_FOUND.format(symbol)}, HTTPStatus.NOT_FOUND

    @classmethod
    def post(cls, symbol: str):
        """
        POST request - json required
        {date: YYYY-MM-DD,
        quantity: int,
        unit_cost: float}
        """
        symbol = symbol.upper()
        position_json = request.get_json()
        try:
            position = PositionsModel(**position_schema.load(position_json))
        except ValidationError as err:
            logging.error(err.messages)

        if position.save_details(symbol):
            # position saved to DB
            return position_schema.dump(position), HTTPStatus.CREATED
        else:
            # error with saving positions
            return {MESSAGE: POSITION_ERR_SAVE.format(symbol)}


class PositionID(Resource):

    @classmethod
    def delete(cls, position_id: int):
        """
        DEL request
        {position_id: int}
        """
        if position := PositionsModel.find_by_position_id(position_id):
            # position exist in DB
            if position.del_position(position.stock.symbol):
                return position_schema.dump(position), HTTPStatus.OK
            else:
                # position couldnt be deleted
                return {MESSAGE: POSITION_ERR_DEL.format(position_id)}, HTTPStatus.BAD_REQUEST
        else:
            # position id not found in DB
            return {MESSAGE: POSITION_ID_NOT_FOUND.format(position_id)}, HTTPStatus.NOT_FOUND


class PositionsList(Resource):

    @classmethod
    def get(cls):
        """
        GET request - no json required
        """
        return {'positions': position_list_schema.dump(PositionsModel.query.all())}
