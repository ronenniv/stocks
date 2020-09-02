from ma import ma
from models.positions import PositionsModel
from marshmallow import post_load, fields, validates, ValidationError

NOT_VALID_COST = 'Not a valid unit cost number'
NOT_POSITIVE_VALUE = 'Not a position value'


class PositionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PositionsModel
        ordered = True

    id = ma.auto_field(dump_only=True)
    quantity = ma.auto_field()
    position_date = ma.Date(data_key='date')  # position_date will be called date in payload
    unit_cost = ma.auto_field()
    stock_id = ma.auto_field(dump_only=True)

    @validates('unit_cost')
    def validate_unit_cost(self, value):
        value = float(value)
        if value != round(value, 2):
            raise ValidationError(NOT_VALID_COST)
        
    @validates('quantity')
    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError(NOT_POSITIVE_VALUE)
