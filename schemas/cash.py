from marshmallow import post_load, validates, ValidationError

from globals.constants import *
from ma import ma
from models.cash import CashModel

from decimal import Decimal


class CashSchema(ma.SQLAlchemySchema):
    class Meta:
        model = CashModel
        dump_only = ('id',)  # dont load id
        load_only = ('id',)  # dont dump id

    id = ma.auto_field()
    balance = ma.Float()  # type in DB is Decimal but due to json dump limitation, it's defined as float in schema

    @post_load
    def make_cash_model(self, data, **kwargs):
        return CashModel(id=1, **data)

    @validates(BALANCE)
    def validate_balance(self, value):
        value = float(value)
        if value != round(value, 2):
            raise ValidationError(NOT_VALID_BALANCE)
