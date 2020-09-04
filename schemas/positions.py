from marshmallow import validates, ValidationError, post_dump

from globals.constants import *
from ma import ma
from models.positions import PositionsModel

NOT_VALID_COST = 'Not a valid unit cost number'
NOT_POSITIVE_VALUE = 'Not a position value'


class PositionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PositionsModel
        ordered = True

    __envelope__ = {"single": None, "many": "positions"}  # for dumping many as dict with key 'positions'

    id = ma.auto_field(dump_only=True)
    quantity = ma.auto_field()
    position_date = ma.Date(data_key='date', required=True)  # position_date will be called date in payload
    unit_cost = ma.auto_field()
    stock_id = ma.auto_field(dump_only=True)

    def get_envelope_key(self, many):
        """Helper to get the envelope key."""
        key = self.__envelope__["many"] if many else self.__envelope__["single"]
        #assert key is not None, "Envelope key undefined"
        return key

    @post_dump(pass_many=True)
    def wrap_with_envelope(self, data, many, **kwargs):
        key = self.get_envelope_key(many)
        return {key: data}

    @validates(UNIT_COST)
    def validate_unit_cost(self, value):
        value = float(value)
        if value != round(value, 2):
            raise ValidationError(NOT_VALID_COST)
        
    @validates(QUANTITY)
    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError(NOT_POSITIVE_VALUE)
