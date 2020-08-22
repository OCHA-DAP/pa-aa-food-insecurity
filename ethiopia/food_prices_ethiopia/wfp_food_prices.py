#!/usr/local/bin/python3

"""Chart of food prices for major staple crops in Ethiopia. Figure based on the
WFP dataset: https://data.humdata.org/dataset/ethiopia-cod-ab 
"""

import pandas as pd
from pandas.plotting import register_matplotlib_converters

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from datetime import datetime


def rem_df_rows(raw_df, col='', vals=[]):
    if col and vals:
        raw_df = raw_df[raw_df[col].str.contains('|'.join(vals), case=False)]
    else:
        print('No rows dropped...')
    return raw_df


def pre_process_dtes(df):
    df[['year', 'month', 'day']] = df['date'].str.split('-', expand=True)
    return df


def pre_process_whole_retail(df):
    df_whole = df[df['cmname'].str.contains('wholesale', case=False)]
    df_retail = df[df['cmname'].str.contains('retail', case=False)]
    return df_whole, df_retail


def aggregate_df_mean(df, columns):
    return df.groupby(columns).mean().reset_index()


def split_by_unique(df, col):
    df_dict = {}
    for item in df[col].unique():
        name = item[:20]
        df_tmp = pd.DataFrame(columns=df.columns)
        for _, row in df.iterrows():
            if row[col] == item:
                df_tmp = df_tmp.append(row, ignore_index=True)
        df_dict[name] = df_tmp
    return df_dict


def convert_dte(df, col):
    df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
    return df


def df_start_yr(df, yr):
    return df[df['date'].dt.year >= yr]


def make_plot(df, unique_col, price_type, plt_title, plt_y_label, colours):
    plt_dict = {}
    df_dct = split_by_unique(df, unique_col)
    count = 0
    for df_name in df_dct.keys():
        plt_dict[df_name] = {
            'chart': df_dct[df_name], 'x': 'date', 'y': ['price'],
            'legend': {'price': price_type.title()+' Prices - ['+df_name + ']'},
            'colours': {'price': colours[count]},
            'line_style': '-', 'line_width': 2}
        if count < len(colours):
            count += 1
        else:
            count = 0
    line_charts(plt_dict, title=plt_title, y_label=plt_y_label)


def line_charts(chart_dict, title='', x_label='', y_label=''):
    figure(figsize=(15, 8))
    for item in chart_dict.keys():
        chart_data = chart_dict[item]
        chart = chart_data['chart']
        x = chart_data['x']
        y = chart_data['y']
        legend = chart_data['legend']
        colours = chart_data['colours']
        line_style = chart_data['line_style']
        line_width = chart_data['line_width']
        for point in y:
            plt.plot(chart[x], chart[point], label=legend[point], alpha=0.75,
                     color=colours[point], linestyle=line_style,
                     linewidth=line_width)

    if title:
        plt.title(title)
    if x_label:
        plt.xlabel(x_label)
    if y_label:
        plt.ylabel(y_label)

    plt.legend()
    plt.show()


def main():
    plt.style.use('seaborn-pastel')
    register_matplotlib_converters()

    med_file = 'wfp_food_median_prices_ethiopia.csv'
    mean_file = 'wfp_food_prices_ethiopia.csv'

    colour_dict = {0: '#8AAAEB', 1: '#80D5EB', 2: '#ADDDCE', 3: '#70AE98',
                   4: '#E6B655', 5: '#CA7E8D', 6: '#AE8967', 7: '#9E6B55'}

    full_med_df = pd.read_csv(med_file, header=0, skiprows=[1])
    full_mean_df = pd.read_csv(mean_file, header=0, skiprows=[1])

    agri_items = ['teff', "wheat", "barley", "corn", "sorghum", 'millet']

    med_df = rem_df_rows(full_med_df, 'cmname', agri_items)
    mean_df = rem_df_rows(full_mean_df, 'cmname', agri_items)

    required_cols = ['cmname', 'date', 'price']
    sort_cols = ['cmname', 'date']

    med_df = convert_dte(med_df, 'date')
    mean_df = convert_dte(mean_df, 'date')

    med_df = df_start_yr(med_df, 2010)
    mean_df = df_start_yr(mean_df, 2010)

    agg_med_df = aggregate_df_mean(med_df, sort_cols)
    agg_mean_df = aggregate_df_mean(mean_df, sort_cols)

    agg_med_df = agg_med_df[required_cols]
    agg_mean_df = agg_mean_df[required_cols]

    agg_whole_med_df, agg_retail_med_df = pre_process_whole_retail(agg_med_df)
    agg_whole_mean_df, agg_retail_mean_df = pre_process_whole_retail(
        agg_mean_df)

    if not agg_whole_med_df.empty:
        make_plot(agg_whole_med_df, 'cmname', 'median',
                  'Median Food Prices - Ethiopia', 'Ethiopian Birr (ETB)',
                  colour_dict)

    if not agg_retail_med_df.empty:
        make_plot(agg_retail_med_df, 'cmname', 'median',
                  'Median Food Prices - Ethiopia', 'Ethiopian Birr (ETB)',
                  colour_dict)

    if not agg_whole_mean_df.empty:
        make_plot(agg_whole_mean_df, 'cmname', 'mean',
                  'Mean Food Prices - Ethiopia', 'Ethiopian Birr (ETB)',
                  colour_dict)

    if not agg_retail_mean_df.empty:
        make_plot(agg_retail_mean_df, 'cmname', 'mean',
                  'Mean Food Prices - Ethiopia', 'Ethiopian Birr (ETB)',
                  colour_dict)

    #     med_df_dct = split_by_unique(agg_median_df, 'cmname')
    #     plot_charts = {}
    #     count = 0
    #     for df_name in med_df_dct.keys():
    #         plot_charts[df_name] = {
    #             'chart': med_df_dct[df_name], 'x': 'date', 'y': ['price'],
    #             'legend': {'price': 'Median Prices - [' + df_name + ']'},
    #             'colours': {'price': colour_dict[count]},
    #             'line_style': '-', 'line_width': 2}
    #         if count < 7:
    #             count += 1
    #         else:
    #             count = 0
    #     line_charts(plot_charts, title='Median Food Prices - Ethiopia',
    #                 y_label='Ethiopian Birr (ETB)')

    # mean_df_dct = split_by_unique(agg_mean_df, 'cmname')
    # plot_charts = {}
    # count = 0
    # for df_name in mean_df_dct.keys():
    #     plot_charts[df_name] = {
    #         'chart': mean_df_dct[df_name], 'x': 'date', 'y': ['price'],
    #         'legend': {'price': 'Mean Prices - [' + df_name + ']'},
    #         'colours': {'price': colour_dict[count]},
    #         'line_style': '-', 'line_width': 2}
    #     if count < 7:
    #         count += 1
    #     else:
    #         count = 0
    # line_charts(plot_charts, title='Mean Food Prices - Ethiopia',
    #             y_label='Ethiopian Birr (ETB)')


if __name__ == "__main__":
    main()
