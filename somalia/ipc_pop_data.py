#!/usr/local/bin/python3
"""
Plot the % Population of Somalia that are categorized in each IPC level over
time.
The IPC (Integrated Food Security Phase Classification) has 5 levels:
    Level 1: Minimal - Level 2: Stressed - Level 3: Crisis - Level 4: Emergency
    - Level 5: Famine
"""

import pandas as pd
from pandas.plotting import register_matplotlib_converters

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from datetime import datetime

plt.style.use("seaborn-pastel")
register_matplotlib_converters()

input_file = "IPC Population Figures Tracking Sheet.xlsx"
country = "Somalia"


def str_range_to_date(date_str):
    """
    Takes a date range string in the form "MMM - MMM YYYY", e.g.
    "Oct - Dec 2019". It returns a list with two datetime objects from the
    first day in each of the months.
    """
    str_lst = date_str.split()
    str_dt1 = "01-" + str_lst[0] + "-" + str_lst[3]
    str_dt2 = "01-" + str_lst[2] + "-" + str_lst[3]

    dt1 = datetime.strptime(str_dt1, "%d-%b-%Y")
    dt2 = datetime.strptime(str_dt2, "%d-%b-%Y")

    return [dt1, dt2]


def xl_pop_sheet_extract(xl_file, country):
    """
    Extract the required data columns from the IPC Population Figures Tracking
    Sheet spreadsheet based on country. The current numbers for population
    in each IPC level plus the first projection columns are included in the
    returned dataframe.
    """

    col_heads = [
        "country",
        "pop",
        "date",
        "rev_pop",
        "%pop",
        "period",
        "IPC1-pop",
        "IPC1-%rev_pop",
        "IPC2-pop",
        "IPC2-%rev_pop",
        "IPC3-pop",
        "IPC3-%rev_pop",
        "IPC4-pop",
        "IPC4-%rev_pop",
        "IPC5-pop",
        "IPC5-%rev_pop",
        "IPC3>-pop",
        "IPC3>-%rev_pop",
        "P-period",
        "P-IPC1-pop",
        "P-IPC1-%rev_pop",
        "P-IPC2-pop",
        "P-IPC2-%rev_pop",
        "P-IPC3-pop",
        "P-IPC3-%rev_pop",
        "P-IPC4-pop",
        "P-IPC4-%rev_pop",
        "P-IPC5-pop",
        "P-IPC5-%rev_pop",
        "P-IPC3>-pop",
        "P-IPC3>-%rev_pop",
    ]
    col_heads_new_order = [
        "country",
        "pop",
        "date",
        "dt-str",
        "rev_pop",
        "%pop",
        "period",
        "period-str",
        "IPC1-pop",
        "IPC1-%rev_pop",
        "IPC2-pop",
        "IPC2-%rev_pop",
        "IPC3-pop",
        "IPC3-%rev_pop",
        "IPC4-pop",
        "IPC4-%rev_pop",
        "IPC5-pop",
        "IPC5-%rev_pop",
        "IPC3>-pop",
        "IPC3>-%rev_pop",
        "P-st-period",
        "P-st-period-str",
        "P-end-period",
        "P-end-period-str",
        "P-IPC1-pop",
        "P-IPC1-%rev_pop",
        "P-IPC2-pop",
        "P-IPC2-%rev_pop",
        "P-IPC3-pop",
        "P-IPC3-%rev_pop",
        "P-IPC4-pop",
        "P-IPC4-%rev_pop",
        "P-IPC5-pop",
        "P-IPC5-%rev_pop",
        "P-IPC3>-pop",
        "P-IPC3>-%rev_pop",
    ]

    xl_dump = pd.read_excel(xl_file, header=[2], usecols="B,D:T,W:AI")
    ipc_pop = xl_dump.loc[xl_dump["Country"] == country]
    ipc_pop.columns = col_heads

    for idx, row in ipc_pop.iterrows():
        dt = row["date"].to_pydatetime()
        ipc_pop.loc[idx, "date"] = dt
        ipc_pop.loc[idx, "dt-str"] = dt.strftime("%Y-%m-%d")

    for idx, row in ipc_pop.iterrows():
        if type(row["period"]) == pd.datetime:
            dt = row["period"]
            ipc_pop.loc[idx, "period"] = dt
            ipc_pop.loc[idx, "period-str"] = dt.strftime("%Y-%m-%d")
        else:
            dt_range_str = row["period"]
            start_dt, end_dt = str_range_to_date(dt_range_str)
            mid_dt = start_dt + (end_dt - start_dt) / 2
            ipc_pop.loc[idx, "period"] = mid_dt
            ipc_pop.loc[idx, "period-str"] = mid_dt.strftime("%Y-%m-%d")

    for idx, row in ipc_pop.iterrows():
        dt_range_str = row["P-period"]
        start_dt, end_dt = str_range_to_date(dt_range_str)
        ipc_pop.loc[idx, "P-st-period"] = start_dt
        ipc_pop.loc[idx, "P-st-period-str"] = start_dt.strftime("%Y-%m-%d")
        ipc_pop.loc[idx, "P-end-period"] = end_dt
        ipc_pop.loc[idx, "P-end-period-str"] = end_dt.strftime("%Y-%m-%d")

    ipc_pop = ipc_pop[col_heads_new_order]

    return ipc_pop


def line_chart(df_ipc, ipc_list=[True, True, True, True, True]):
    """
    df_ipc: dataframe containing IPC data
    ip_list: Positional list of IPC categories to show in the line chart
    """

    proj_threshold = df_ipc.loc[df_ipc["P-IPC3>-pop"] / df_ipc["pop"] >= 0.2]
    threshold = df_ipc.loc[df_ipc["IPC3>-pop"] / df_ipc["pop"] >= 0.2]

    figure(figsize=(15, 8))
    if ipc_list[0]:
        plt.plot(
            df_ipc["period"],
            df_ipc["IPC1-pop"],
            label="IPC 1",
            alpha=0.75,
            color="#ADDDCE",
            linestyle="-",
            linewidth=4,
        )
        plt.plot(
            df_ipc["P-end-period"],
            df_ipc["P-IPC1-pop"],
            color="#ADDDCE",
            label="Projected",
            linestyle=":",
            linewidth=2,
        )
    if ipc_list[1]:
        plt.plot(
            df_ipc["period"],
            df_ipc["IPC2-pop"],
            label="IPC 2",
            alpha=0.75,
            color="#70AE98",
            linestyle="-",
            linewidth=4,
        )
        plt.plot(
            df_ipc["P-end-period"],
            df_ipc["P-IPC2-pop"],
            color="#70AE98",
            label="Projected",
            linestyle=":",
            linewidth=2,
        )
    if ipc_list[2]:
        plt.plot(
            df_ipc["period"],
            df_ipc["IPC3-pop"],
            label="IPC 3",
            alpha=0.75,
            color="#E6B655",
            linestyle="-",
            linewidth=4,
        )
        plt.plot(
            df_ipc["P-end-period"],
            df_ipc["P-IPC3-pop"],
            color="#E6B655",
            label="Projected",
            linestyle=":",
            linewidth=2,
        )
    if ipc_list[3]:
        plt.plot(
            df_ipc["period"],
            df_ipc["IPC4-pop"],
            label="IPC 4",
            alpha=0.75,
            color="#CA7E8D",
            linestyle="-",
            linewidth=4,
        )
        plt.plot(
            df_ipc["P-end-period"],
            df_ipc["P-IPC4-pop"],
            color="#CA7E8D",
            label="Projected",
            linestyle=":",
            linewidth=2,
        )
    if ipc_list[4]:
        plt.plot(
            df_ipc["period"],
            df_ipc["IPC5-pop"],
            label="IPC 5",
            alpha=0.75,
            color="#9E6B55",
            linestyle="-",
            linewidth=4,
        )
        plt.plot(
            df_ipc["P-end-period"],
            df_ipc["P-IPC5-pop"],
            color="#9E6B55",
            label="Projected",
            linestyle=":",
            linewidth=2,
        )
    plt.title("Population at each IPC Phase in Somalia")
    plt.ylabel("Population")

    for k, v in proj_threshold.iterrows():
        plt.axvspan(v["P-st-period"], v["P-end-period"], color="gray", alpha=0.25)

    for d in threshold["period"]:
        plt.axvline(d, linewidth=3, color="brown", alpha=0.75)

    plt.legend()

    plt.show()


if __name__ == ("__main__"):
    som_ipc_pop = xl_pop_sheet_extract(input_file, country)

    # print(som_ipc_pop.head())
    # print(som_ipc_pop.columns)
    # print(som_ipc_pop[['date', 'dt-str', 'P-st-period', 'P-st-period-str',
    #                    'P-end-period', 'P-end-period-str']])
    print(som_ipc_pop[["period", "P-st-period", "P-end-period-str"]])

    line_chart(som_ipc_pop, [False, False, True, True, True])
