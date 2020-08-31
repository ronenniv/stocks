from ma import ma
from models.cash import CashModel
from marshmallow import post_load


class CashSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CashModel
        dump_only = ('id', )  # dont load id
        load_only = ('id', )  # dont dump id

    @post_load
    def make_cash_model(self, data, **kwargs):
        return CashModel(id=1, **data)
