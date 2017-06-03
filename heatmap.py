import plotly.plotly as py
import plotly.graph_objs as go
from options_csv import OUTPUT_FILENAME_PREFIX_FORMAT
import re
import os
import pandas as pd

def build_heatmap(openInt_df):
    trace = go.Heatmap(z=openInt_df.fillna(0).as_matrix(),
                       x=openInt_df.columns,
                       y=openInt_df.index)
    data=[trace]
    layout = go.Layout(
        zaxis=dict(
            type='log',
            autorange=True
        )
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='expiration-heatmap')

def build_colorscale(openInt_df):
    data = [{
        'x': openInt_df.columns,
        'y': openInt_df.index,
        'z': openInt_df.fillna(0).as_matrix(),
        'type': 'heatmap',
        'colorscale': [
            # [0, 'rgb(250, 250, 250)'],        #0
            # [1./10000, 'rgb(200, 200, 200)'], #10
            # [1./1000, 'rgb(150, 150, 150)'],  #100
            # [1./100, 'rgb(100, 100, 100)'],   #1000
            # [1./10, 'rgb(50, 50, 50)'],       #10000
            # [1., 'rgb(0, 0, 0)'],             #100000
            [0, 'rgb(250, 250, 250)'],        #0
            [1./16.0, 'rgb(200, 200, 200)'], #10
            [1./8.0, 'rgb(150, 150, 150)'],  #100
            [1./4.0, 'rgb(100, 100, 100)'],   #1000
            [1./2.0, 'rgb(50, 50, 50)'],       #10000
            [1., 'rgb(0, 0, 0)'],             #100000
        ],
        'colorbar': {
            'tick0': 0,
            'tickmode': 'array',
            'tickvals': [0, 1000, 10000, 100000]
        }
        }]

    layout = {'title': 'Log Colorscale'}

    fig = {'data': data, 'layout': layout}

    py.plot(fig, filename='expiration-heatmap')                                                                                                                                                   

def get_combined_options_data(csv_date, symbol, indir):
    expected_prefix = OUTPUT_FILENAME_PREFIX_FORMAT.format(date=csv_date, ticker=symbol)
    options_tables = {}
    for root, dirs, files in os.walk(indir):
        for file in files:
            if file.startswith(str(csv_date)) and file.endswith(".csv"):
                expiration_with_ext = file.split("_")[-1]
                expiration = expiration_with_ext.split(".")[0][3:]
                filename = os.path.join(root, file)
                options_table = pd.DataFrame.from_csv(filename)
                options_tables[expiration] = options_table
    return pd.Panel(options_tables)


if __name__ == "__main__":
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="Makes a heatmap from a sequence of expirations")
    parser.add_argument("--symbol", default="spx", help="Symbol in CSV files")
    parser.add_argument("--indir", default=os.getcwd(), help="Directory to look for CSV files")
    args = parser.parse_args()
    # TODO: Add date selection (just use today for now...)
    args.csv_date = datetime.date.today()

    options_panel = get_combined_options_data(args.csv_date, args.symbol, args.indir)
    print(options_panel)
    call_openInt = options_panel.minor_xs('call_Open Int.')
    print(call_openInt)
    build_colorscale(call_openInt)

