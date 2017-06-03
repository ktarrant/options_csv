import pandas as pd
import pickle
from urllib.request import urlopen
from bs4 import BeautifulSoup
from collections import OrderedDict
import logging
import datetime

# Make a publicly available filename output format
OUTPUT_FILENAME_PREFIX_FORMAT = "{date}_{ticker}"
OUTPUT_FILENAME_SUFFIX_FORMAT = "_exp{expiration}.{extension}"
OUTPUT_FILENAME_FORMAT = OUTPUT_FILENAME_PREFIX_FORMAT + "_" + OUTPUT_FILENAME_SUFFIX_FORMAT

# Make a string clean for use a as a filename
clean_filename = lambda s: "".join([c for c in s if c.isalpha() or c.isdigit() or c==' ']).rstrip()
# Common helper for creating a data header
data_header = lambda prefix, header: prefix + "_" + header

def secure_filename(ticker, expiration, extension="csv"):
    today = datetime.date.today()
    clean_exp = clean_filename(expiration).replace(" ", "-")
    return OUTPUT_FILENAME_FORMAT.format(
        date=today, ticker=ticker, expiration=clean_exp, extension=extension)

log = logging.getLogger(__name__)

def load_symbol(symbol):
    """ Loads the options chain for the index with the given symbol """
    url = "http://www.marketwatch.com/investing/index/{}/options".format(symbol.lower())
    log.info("Loading webpage: {}".format(url))
    with urlopen(url) as urlobj:
        soup = BeautifulSoup(urlobj.read(), "lxml")
    return soup

def _checkItemWasFound(item_to_check, item_name, parent_name="webpage"):
    """ Checks if item_to_check is None, and if it is then throws an Exception. """
    if item_to_check is None:
        raise Exception("Failed to find item '{}' in '{}'".format(item_name, parent_name))
    else:
        log.debug("Found item '{}' in '{}'".format(item_name, parent_name))

def parse_options(soup, symbol, keep_clean=True):
    """ Parses the given marketwatch soup for an options table """
    # Helper lambda functions
    text_clean = lambda s: s.strip().replace(",","")
    unpack_cols = lambda cols: [ text_clean(td.text) for td in cols ]

    # First find the options table to parse
    options = soup.find('div', {'id':'options'})
    _checkItemWasFound(options, 'options_table')

    # Find the first header row in the table
    header_rows = options.select('tr.chainrow.understated')
    header_row = header_rows[0] # TODO: Iterate over all headers to find all tables!
    _checkItemWasFound(header_row, 'header_row', 'options_table')
    # Parse the header row into fields
    headers = unpack_cols(header_row.findAll('td'))
    header_half_len = int(len(headers)/2)
    strike_header = headers[header_half_len]
    main_headers = headers[:header_half_len]
    option_order = ["call", "put"]
    data_headers = lambda option_type: [data_header(option_type, header) for header in main_headers]
    log.info("Found main headers: {}".format(main_headers))

    # Now process all of the rows and extract the pricing information from them
    rows = options.findAll('tr', {'class': 'chainrow'})
    log.debug("Found {} rows in options table.".format(len(rows)))
    calls_are_itm = True
    current_expiration = None
    data_columns = [header for option_type in option_order for header in data_headers(option_type)]
    current_table = None
    for row in rows:
        if "heading" in row["class"] and "Expires" in row.text:
            # Extract the expiration date
            this_expiration = row.text.strip().replace("Expires ", "")

            if current_expiration is not None and this_expiration != current_expiration:
                # We need to close the old file and start a new one
                out_file = secure_filename(symbol, current_expiration)
                current_table.to_csv(out_file)
                log.info("Finshed expiration '{}'; Saved to: {}".format(
                    current_expiration, out_file))

            log.debug("Starting new expiration: {}".format(this_expiration))
            current_expiration = this_expiration
            current_table = pd.DataFrame(columns=(data_columns))

        elif "aright" in row['class']:
            # this is a row containing option data. get the strike column first.
            strike_col = text_clean(row.find('td', {'class': 'strike-col'}).text)
            log.debug("Processing row with strike: {}".format(strike_col))

            results = OrderedDict()

            # add a prefix as a call or put depending on whether we know (by tracking our progress)
            # whether calls are itm yet or not
            extract_order = ["inthemoney", ""] if calls_are_itm else ["", "inthemoney"]
            for option_type, extract in zip(option_order, extract_order):
                cols = unpack_cols(row.findAll('td', {'class': extract}))
                if len(cols) < len(main_headers):
                    cols += [None] * (len(headers) - len(cols))
                cols = cols[:len(headers)]
                entry = [(header, col) for header, col in zip(data_headers(option_type), cols)]
                results.update(entry)

            # add this row to the running table
            strike_value = float(strike_col.replace(",", ""))
            log.debug("Processed option row for strike: {}".format(strike_value))
            current_table.loc[strike_value] = results

        elif "stockprice" in row['class']:
            # We have reached the stock price in the table, so we know calls are no longer itm
            # (and we skip this row)
            log.debug("Processed current stock price.")
            calls_are_itm = False

        else:
            # We don't know or care how to process this row.
            pass


if __name__ == "__main__":
    import os
    import argparse

    parser = argparse.ArgumentParser(
        description="Parses a MarketWatch options chain into a CSV made by pandas.")
    parser.add_argument("--symbol", default="spx", help="Symbol to look up.")
    parser.add_argument("--out", default=os.getcwd(),
        help="Output directory. Default is current dir.")
    parser.add_argument("--info", action="store_true", help="Print additional information")
    parser.add_argument("--verbose", action="store_true", help="Print debug information")

    args=parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.info:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    # first lets get this output file straight
    if args.out is None:
        args.out = ".".join([args.symbol, "csv"])
    soup = load_symbol(args.symbol)
    df = parse_options(soup, args.symbol)