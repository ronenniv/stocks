import logging
from http import HTTPStatus

from flask import request
from flask_restful import Resource

from globals.constants import *
from models.positions import PositionsModel
from schemas.positions import PositionSchema

position_schema = PositionSchema()
position_list_schema = PositionSchema(many=True)


class Position(Resource):

    @classmethod
    def get(cls, symbol: str):
        """
        GET request - no json required
        """
        symbol = symbol.upper()
        logging.debug(f'func: get, {symbol=}')

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
        position = PositionsModel(**position_schema.load(position_json))
        if position.save_details(symbol):
            # position saved to DB
            return position_schema.dump(position), HTTPStatus.CREATED
        else:
            # error with saving positions
            return {MESSAGE: POSITION_ERR_SAVE.format(symbol)}, HTTPStatus.BAD_REQUEST


class PositionID(Resource):

    @classmethod
    def delete(cls, position_id: int):
        """
        DEL request
        {position_id: int}
        """
        if position := PositionsModel.find_by_position_id(position_id):
            # position exist in DB
            if position.del_position():
                return position_schema.dump(position), HTTPStatus.OK
            else:
                # position couldn't be deleted
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
        return position_list_schema.dump(PositionsModel.query.all())
