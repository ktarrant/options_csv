import pandas as pd
import pickle
from urllib.request import urlopen
from bs4 import BeautifulSoup
import argparse
from collections import OrderedDict

def load_symbol(symbol):
    url = "http://www.marketwatch.com/investing/index/{}/options".format(symbol)
    cache_file = "pandas_raw_data.csv" 
    with urlopen(url) as urlobj:
        soup = BeautifulSoup(urlobj.read(), "lxml")
    return soup

def pack_columns(cols, headers, prefix):
    prefixed_headers = [prefix + "_" + header for header in headers]
    if len(cols) < len(headers):
        cols += [None] * (len(headers) - len(cols))
    cols = cols[:len(headers)]
    return [(header, col) for header, col in zip(prefixed_headers, cols)]

def parse_options(soup, keep_clean=True):
    options = soup.find('div', {'id':'options'})
    rows = options.findAll('tr', {'class': 'chainrow'})
    text_clean = lambda s: s.strip().replace(",","")
    unpack_cols = lambda cols: [ text_clean(td.text) for td in cols ]
    headers = unpack_cols(rows[0].findAll('td'))
    header_half_len = int(len(headers)/2)
    strike_header = headers[header_half_len]
    main_headers = headers[:header_half_len]
    calls_are_itm = True
    for row in rows[1:]:
        # get the strike column first
        strike_col = text_clean(row.find('td', {'class': 'strike-col'}).text)
        results = OrderedDict([(strike_header, strike_col)])

        # Once we reach the strike price, we know calls are no longer itm (and we skip this row)
        if "Current price as of" in row.text:
            calls_are_itm = False
            continue

        # add a prefix as a call or put depending on whether we know (by tracking our progress)
        # whether calls are itm yet or not
        prefix_order = ["call", "put"]
        extract_order = ["inthemoney", ""] if calls_are_itm else ["", "inthemoney"]
        for prefix, extract in zip(prefix_order, extract_order):
            cols = unpack_cols(row.findAll('td', {'class': extract}))
            results.update(pack_columns(cols, main_headers, prefix))

        # yield a dictionary of this row
        yield results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parses a MarketWatch options chain into a CSV made by pandas.")
    parser.add_argument("--symbol", default="spx", help="Symbol to look up.")
    parser.add_argument("--out", default=None, help="Output file. Default is [symbol].csv")

    args=parser.parse_args()
    # first lets get this output file straight
    if args.out is None:
        args.out = ".".join([args.symbol, "csv"])
    soup = load_symbol(args.symbol)
    df = pd.DataFrame(parse_options(soup))
    df.to_csv(args.out)