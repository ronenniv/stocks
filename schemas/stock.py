from ma import ma
from models.stock import StockModel
from schemas.positions import PositionSchema
from marshmallow import fields, validates, ValidationError
import typing

from globals.constants import *


class SymbolUpper(fields.Field):
    def _deserialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """make symbol upper"""
        return value.upper()


class PriceConvert(fields.Field):
    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """for current price to be float or str for ERR"""
        return value


class StockSchema(ma.SQLAlchemySchema):
    class Meta:
        model = StockModel
        ordered = True
        positions = ma.Nested(PositionSchema, many=True)

    id = ma.auto_field(dump_only=True)
    symbol = SymbolUpper(required=True)
    desc = ma.auto_field(required=True)
    quantity = ma.auto_field(missing=0)  # missing for default value
    unit_cost = ma.auto_field(missing=0)  # missing for default value
    stop_quote = ma.auto_field(missing=0)  # missing for default value
    price = PriceConvert(dump_only=True)

    @validates(SYMBOL)
    def validate_symbol(self, value):
        if len(value) > SYMBOL_MAX_LEN or not value.isalpha():
            raise ValidationError(NOT_VALID_SYMBOL)

    @validates(DESC)
    def validate_desc(self, value):
        if len(value) > DESC_MAX_LEN or not value.isprintable():
            raise ValidationError(NOT_VALID_DESC)
