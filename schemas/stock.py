from ma import ma
from models.stock import StockModel
from schemas.positions import PositionSchema
from marshmallow import post_load, fields, validates, ValidationError
import typing

NOT_VALID_SYMBOL = 'Not a valid symbol'
NOT_VALID_DESC = 'Not a valid description'
# maximum length for string fields
SYMBOL_MAX_LEN = 5  # maximum len of symbol string
DESC_MAX_LEN = 30  # maximum len of description string


class SymbolUpper(fields.Field):
    def _deserialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        return value.upper()


class StockSchema(ma.SQLAlchemySchema):
    class Meta:
        model = StockModel
        ordered = True
        positions = ma.Nested(PositionSchema, many = True)

    id = ma.auto_field(dump_only=True)
    symbol = SymbolUpper()
    desc = ma.auto_field()
    quantity = ma.auto_field(missing=0)
    unit_cost = ma.auto_field(missing=0)
    stop_quote = ma.auto_field(missing=0)

    @validates('symbol')
    def validate_symbol(self, value):
        if len(value) > SYMBOL_MAX_LEN and not value.isalpha():
            raise ValidationError(NOT_VALID_SYMBOL)

    @validates('desc')
    def validate_desc(self, value):
        if len(value) > DESC_MAX_LEN and not value.isprintable():
            raise ValidationError(NOT_VALID_DESC)
