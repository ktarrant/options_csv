from django.db import models

class Leg(models.Model):
    BUY_OR_SELL_CHOICES = (("buy", "Buy"), ("sell", "Sell"),)
    OPEN_OR_CLOSE_CHOICES = (("open", "Open"), ("close", "Close"),)
    INSTRUMENT_CHOICES = (
        ("call", "Call"),
        ("put", "Put"),
        ("stock", "Stock"),
        ("fut", "Futures"),
    )

    symbol = models.CharField(max_length=16)
    exec_date = models.DateTimeField("date executed")
    buy_or_sell = models.CharField(
        max_length=4,
        choices=BUY_OR_SELL_CHOICES,
        default="buy",
    )
    open_or_close = models.CharField(
        max_length=5,
        choices=OPEN_OR_CLOSE_CHOICES,
        default="open",
    )
    instrument = models.CharField(
        max_length=5,
        choices=INSTRUMENT_CHOICES,
        default="call",
    )
    quantity = models.PositiveIntegerField()
    execution_price = models.FloatField()
    execution_fees = models.FloatField(default=0)
    expiration_date = models.DateTimeField("expiration", null=True)
    margin = models.FloatField(null=True)
    underlying_price = models.FloatField(null=True)