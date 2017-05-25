import pandas as pd
import numpy as np
import plotly.plotly as py
import plotly.graph_objs as go
import argparse

# Make a string clean for use a as a filename
clean_filename = lambda s: "".join([c for c in s if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def make_hbar_plot(options_table, symbol, parameter):
    data = [
        go.Bar(
            name=otype,
            x=options_table['{}_{}'.format(otype, parameter)],
            y=options_table['Strike'],
            orientation='h',
            marker={
                "color": color,
            },
        )
        for otype, color in [("call", "green"), ("put", "red")]
    ]

    layout = go.Layout(
        title="{} - {}".format(symbol, parameter),
        barmode='stack'
    )
    fig = go.Figure(data=data, layout=layout)
    return py.plot(fig, filename=clean_filename("{}_{}".format(symbol, parameter)))

if __name__ == "__main__":
    typical_params = ["Ask", "Bid", "Change", "Last", "Open Int.", "Symbol", "Vol"]
    parser = argparse.ArgumentParser(description="Plots a parameter from an options CSV")
    parser.add_argument("--csv", default="spx.csv", help="CSV file to pull parameter from")
    parser.add_argument("--param", default="Open Int.",
        help="Parameter to pull and plot. Typical params are {} ".format(typical_params))

    args = parser.parse_args()
    options_table = pd.DataFrame.from_csv(args.csv)
    url = make_hbar_plot(options_table, args.csv.split(".")[0], args.param)
