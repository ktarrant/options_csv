import pandas as pd
import pickle
from urllib.request import urlopen
from bs4 import BeautifulSoup
import argparse
from collections import OrderedDict
import logging

log = logging.getLogger(__name__)

def load_symbol(symbol):
    url = "http://www.marketwatch.com/investing/index/{}/options".format(symbol)
    log.debug("Loading webpage: {}".format(url))
    with urlopen(url) as urlobj:
        soup = BeautifulSoup(urlobj.read(), "lxml")
    return soup

def pack_columns(cols, headers, prefix):
    prefixed_headers = [prefix + "_" + header for header in headers]
    if len(cols) < len(headers):
        cols += [None] * (len(headers) - len(cols))
    cols = cols[:len(headers)]
    return [(header, col) for header, col in zip(prefixed_headers, cols)]

def _checkItemWasFound(item_to_check, item_name, parent_name="webpage"):
    if item_to_check is None:
        raise Exception("Failed to find item '{}' in '{}'".format(item_name, parent_name))
    else:
        log.debug("Found item '{}' in '{}'".format(item_name, parent_name))

def parse_options(soup, keep_clean=True):
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
    log.debug("Found main headers: {}".format(main_headers))

    # Now process all of the rows and extract the pricing information from them
    rows = options.findAll('tr', {'class': 'chainrow'})
    log.debug("Found {} rows in options table.".format(len(rows)))
    calls_are_itm = True
    current_expiration = None
    expiration_label = None
    for row in rows:
        if "heading" in row["class"] and "Expires" in row.text:
            if current_expiration is None:
                current_expiration = row.text.strip()
                expiration_label = current_expiration.replace("Expires ", "")
                log.debug("Current expiration: {}".format(expiration_label))
            if row.text.strip() != current_expiration:
                # TODO: Support extracting all expirations, not just the front one!
                break

        elif "aright" in row['class']:
            # this is a row containing option data. get the strike column first.
            strike_col = text_clean(row.find('td', {'class': 'strike-col'}).text)
            log.debug("Processing row with strike: {}".format(strike_col))

            results = OrderedDict([(strike_header, strike_col)])

            # add a prefix as a call or put depending on whether we know (by tracking our progress)
            # whether calls are itm yet or not
            prefix_order = ["call", "put"]
            extract_order = ["inthemoney", ""] if calls_are_itm else ["", "inthemoney"]
            for prefix, extract in zip(prefix_order, extract_order):
                cols = unpack_cols(row.findAll('td', {'class': extract}))
                results.update(pack_columns(cols, main_headers, prefix))

            # yield a dictionary of this row
            log.debug("Processed option row for strike: {}".format(strike_col))
            yield results

        elif "stockprice" in row['class']:
            # We have reached the stock price in the table, so we know calls are no longer itm
            # (and we skip this row)
            log.debug("Processed current stock price.")
            calls_are_itm = False
        else:
            # We don't know or care how to process this row.
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parses a MarketWatch options chain into a CSV made by pandas.")
    parser.add_argument("--symbol", default="spx", help="Symbol to look up.")
    parser.add_argument("--out", default=None, help="Output file. Default is [symbol].csv")
    parser.add_argument("--verbose", action="store_true", help="Print debug information")

    args=parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    # first lets get this output file straight
    if args.out is None:
        args.out = ".".join([args.symbol, "csv"])
    soup = load_symbol(args.symbol)
    df = pd.DataFrame(parse_options(soup))
    df.to_csv(args.out)