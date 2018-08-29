import pandas as pd
import datetime
import logging
from collections import OrderedDict

from .models import Leg

logger = logging.getLogger(__name__)

def parse_float(value, error=True):
    try:
        s = value.replace(",", "")
    except AttributeError:
        # it's not a string, pass through
        return value

    try:
        return float(s)
    except ValueError as e:
        if error:
            raise e
        else:
            return value

def load_tastyworks_trades(filename):
    df = pd.read_csv(filename)

    for line_id in df.index:
        row = df.loc[line_id]
        # - Type
        if row["Type"] != "Trade":
            logger.info("Skipping entry with type '{}'".format(row["Type"]))
            continue

        kwargs = OrderedDict()
        # - Date
        kwargs["exec_date"] = row["Date"]
        # - Action
        action = row["Action"]
        try:
            buy_tx, open_tx = action.split("_TO_")
        except ValueError:
            buy_tx = action
            open_tx = ""
        kwargs["buy_or_sell"] = buy_tx.lower()
        kwargs["open_or_close"] = open_tx.lower()
        # - Symbol - not used
        # - Instrument
        # TODO: Process non-options
        if "Option" not in row["Instrument Type"]:
            logger.error("Skipping unimplemented instrument: '{}'".format(row["Instrument Type"]))
            continue
        kwargs["instrument"] = "option"
        # - Description - not used
        # - Value
        kwargs["margin"] = parse_float(row["Value"])
        # - Quantity
        kwargs["quantity"] = int(row["Quantity"])
        # - Average Price
        avg_price = parse_float(row["Average Price"])
        # - Comissions
        # - Fees
        comish = parse_float(row["Commissions"])
        fees = parse_float(row["Fees"])
        kwargs["execution_fees"] = comish + fees
        # - Multiplier
        multiplier = parse_float(row["Multiplier"])
        kwargs["execution_price"] = avg_price / multiplier
        # - Underlying Symbol
        kwargs["symbol"] = row["Underlying Symbol"]
        # - Expiration Date
        exp_date = row["Expiration Date"]
        if exp_date != "":
            m, d, y = exp_date.split("/")
            kwargs["expiration_date"] = datetime.date(year=int(y), month=int(m), day=int(d))

        # TODO: Find a way to get underlying_price

        yield Leg(**kwargs)



if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Parses a CSV file provided by the Tastyworks history page")

    parser.add_argument("file", type=os.path.abspath)

    args = parser.parse_args()