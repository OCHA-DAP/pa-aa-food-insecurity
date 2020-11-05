import pandas as pd
import numpy as np
import warnings
from utils import parse_args, parse_yaml, config_logger
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def get_new_name(name, n_dict):
    """
    Return the values of a dict if name is in the keys of the dict
    Args:
        name: string of interest
        n_dict: dict with possibly "name" as key

    Returns:

    """
    if name in n_dict.keys():
        return n_dict[name]
    else:
        return name


def merge_ipcstatus(cs_path, ml1_path, ml2_path, adm1c, adm2c):
    """
    Merge the three types of IPC projections (CS, ML1, ML2) to one dataframe
    Args:
        cs_path: path to file with fewsnet data for current situation (CS)
        ml1_path: path to file with fewsnet data for short-term forecast (ML1)
        ml2_path: path to file with fewsnet data for long-term forecast (ML2)
        adm1c: column name of the admin1 level name, in fewsnet data
        adm2c: column name of the admin2 level name, in fewsnet data

    Returns:
        df_ipc: dataframe with the cs, ml1 and ml2 data combined
    """
    cs = pd.read_csv(cs_path, index_col=0)
    ml1 = pd.read_csv(ml1_path, index_col=0)
    ml2 = pd.read_csv(ml2_path, index_col=0)

    # merge the CS, ML1 and ML2 in one df
    df_ipc = cs.merge(
        ml1[["date", adm1c, adm2c, "ML1"]], on=[adm1c, adm2c, "date"], how="left"
    )
    df_ipc = df_ipc.merge(
        ml2[["date", adm1c, adm2c, "ML2"]], on=[adm1c, adm2c, "date"], how="left"
    )
    df_ipc["date"] = pd.to_datetime(df_ipc["date"])
    df_ipc["date"] = df_ipc["date"].dt.date
    return df_ipc


def load_popdata(
    pop_path, pop_adm1c, pop_adm2c, pop_col, admin2_mapping=None, admin1_mapping=None
):
    """

    Args:
        pop_path: path to csv with population counts per admin2 region
        pop_adm1c: column name of the admin1 level name, in population data
        pop_adm2c: column name of the admin1 level name, in population data
        pop_col: column name that contains the population count
        admin2_mapping: dict of admin2level names that don't correspond in FewsNet and population data. Keys are FewsNet names, values population
        admin1_mapping: dict of admin1level names that don't correspond in FewsNet and population data. Keys are FewsNet names, values population

    Returns:
        df_pop: DataFrame with population per admin2/admin1 combination that corresponds with FewsNet names
    """
    # import population data
    df_pop = pd.read_csv(pop_path)
    # remove whitespace at end of string
    df_pop[pop_adm2c] = df_pop[pop_adm2c].str.rstrip()
    if admin2_mapping:
        df_pop[pop_adm2c] = df_pop[pop_adm2c].apply(
            lambda x: get_new_name(x, admin2_mapping)
        )
    if admin1_mapping:
        df_pop[pop_adm1c] = df_pop[pop_adm1c].apply(
            lambda x: get_new_name(x, admin1_mapping)
        )
    no_popdata = df_pop.loc[df_pop[pop_col].isin([0, np.nan]), pop_adm2c].values
    if len(no_popdata) > 0:
        logger.warning(f"No population data for {', '.join(no_popdata)}")
    # 0 is here treated as missing data, since it is not realistic that a region has no population and will make calculations later on easier
    df_pop[pop_col] = df_pop[pop_col].replace(0, np.nan)

    df_pop.rename(columns={pop_col: "Total"}, inplace=True)
    return df_pop


def create_histpopdict(
    df_data, country, histpop_path="Data/Worldbank_TotalPopulation.csv"
):
    """
    Retrieve the historical national population for the years that are present in df_data
    Args:
        df_data: DataFrame of interest
        country: Country of interest
        histpop_path: path to csv with historical national population

    Returns:
        dict with national population for each year
    """
    df_histpop = pd.read_csv(histpop_path, header=2)
    df_histpop.set_index("Country Name", inplace=True)
    df_histpopc = df_histpop.loc[country]
    data_years = [
        str(i)
        for i in range(df_data["date"].min().year, df_data["date"].max().year + 1)
    ]
    y_nothist = np.setdiff1d(data_years, df_histpopc.index)
    y_hist = np.setdiff1d(data_years, y_nothist)
    df_histpopc = df_histpopc[y_hist]
    for y in y_nothist:
        df_histpopc[y] = df_histpopc[df_histpopc.index.max()]

    return df_histpopc.to_dict()


def get_adjusted(row, perc_dict):
    """
    Compute the subnational population, adjusted to the country's national population of that year
    """
    year = str(row["date"].year)
    adjustment = perc_dict[year]
    if pd.isna(row["Total"]):
        return row["Total"]
    else:
        return int(row["Total"] * adjustment)


def merge_ipcpop(df_ipc, df_pop, country, pop_adm1c, pop_adm2c, ipc_adm1c, ipc_adm2c):
    """

    Args:
        df_ipc: DataFrame with IPC data
        df_pop: DataFrame with subnational population data
        country: Name of country of interest
        pop_adm1c: column name of the admin1 level name, in population data
        pop_adm2c: column name of the admin1 level name, in population data
        ipc_adm1c:  column name of the admin1 level name, in IPC data
        ipc_adm2c:  column name of the admin2 level name, in IPC data

    Returns:
        df_ipcp: DataFrame with IPC level and population per admin2 region, where the population is adjusted to historical national averages
    """
    df_ipcp = df_ipc.merge(
        df_pop[[pop_adm1c, pop_adm2c, "Total"]],
        how="left",
        left_on=[ipc_adm1c, ipc_adm2c],
        right_on=[pop_adm1c, pop_adm2c],
    )

    # dict to indicate relative increase in population over the years
    pop_dict = create_histpopdict(df_ipcp, country=country)
    # estimate percentage of population at given year in relation to the national population given by the subnational population file
    pop_tot_subn = df_ipcp[df_ipcp.date == df_ipcp.date.unique()[0]]["Total"].sum()
    perc_dict = {k: v / pop_tot_subn for k, v in pop_dict.items()}

    df_ipcp["adjusted_population"] = df_ipcp.apply(
        lambda x: get_adjusted(x, perc_dict), axis=1
    )
    if df_ipcp[df_ipcp.date == df_ipcp.date.max()].Total.sum() != df_pop.Total.sum():
        warnings.warn(
            f"Population data merged with IPC doesn't match the original population numbers. Original:{df_pop.Total.sum()}, Merged:{df_ipcp[df_ipcp.date == df_ipcp.date.max()].Total.sum()}"
        )

    # add columns with population in each IPC level for CS, ML1 and ML2
    for status in ["CS", "ML1", "ML2"]:
        for level in [1, 2, 3, 4, 5]:
            ipc_id = "{}_{}".format(status, level)
            df_ipcp[ipc_id] = np.where(
                df_ipcp[status] == level,
                df_ipcp["adjusted_population"],
                (np.where(np.isnan(df_ipcp[status]), np.nan, 0)),
            )
        df_ipcp[f"pop_{status}"] = df_ipcp[[f"{status}_{i}" for i in range(1, 6)]].sum(
            axis=1, min_count=1
        )
        df_ipcp[f"pop_{status}"] = df_ipcp[f"pop_{status}"].replace(0, np.nan)

    return df_ipcp


def aggr_admin1(df, adm1c):
    """
    Aggregate dataframe to admin1 level
    Args:
        df: DataFrame of interest
        adm1c: column name of the admin1 level name in df

    Returns:
        df_adm: dataframe with number of people in each IPC class per Admin1 region
    """
    cols_ipc = [f"{s}_{l}" for s in ["CS", "ML1", "ML2"] for l in range(1, 6)]
    df_adm = (
        df[["date", "Total", "adjusted_population", adm1c] + cols_ipc]
        .groupby(["date", adm1c])
        .agg(lambda x: np.nan if x.isnull().all() else x.sum())
        .reset_index()
    )
    for status in ["CS", "ML1", "ML2"]:
        df_adm[f"pop_{status}"] = df_adm[[f"{status}_{i}" for i in range(1, 6)]].sum(
            axis=1, min_count=1
        )

    return df_adm


def main(country_iso3, config_file="config.yml"):
    """
    This script takes as input FewsNet IPC levels on Admin2 level, merges these with population data, and aggregates to Admin1
    Results are saved to CSVs
    Args:
        country_iso3: ISO3 code of country of interest
        config_file: path to config file with country specific variables
    """
    parameters = parse_yaml(config_file)[country_iso3]
    country = parameters["country_name"]

    RESULT_FOLDER = f"{country}/Data/FewsNetCombined/"
    # create output dir if it doesn't exist yet
    Path(RESULT_FOLDER).mkdir(parents=True, exist_ok=True)
    fnfolder = f"{country}/Data/FewsNetAdmin2/"
    start_date = parameters["start_date"]
    end_date = parameters["end_date"]
    cs_path = f"{fnfolder}{country}_admin2_fewsnet_{start_date}_{end_date}_CS.csv"
    ml1_path = f"{fnfolder}{country}_admin2_fewsnet_{start_date}_{end_date}_ML1.csv"
    ml2_path = f"{fnfolder}{country}_admin2_fewsnet_{start_date}_{end_date}_ML2.csv"

    pop_file = parameters["pop_filename"]
    POP_PATH = f"{country}/Data/{pop_file}"
    pop_adm1c = parameters["adm1c_pop"]
    pop_adm2c = parameters["adm2c_pop"]
    ipc_adm1c = parameters["adm1c_bound"]
    ipc_adm2c = parameters["adm2c_bound"]
    pop_col = parameters["pop_col"]
    admin1_mapping = parameters["admin1_mapping"]
    admin2_mapping = parameters["admin2_mapping"]

    df_allipc = merge_ipcstatus(cs_path, ml1_path, ml2_path, ipc_adm1c, ipc_adm2c)
    df_pop = load_popdata(
        POP_PATH,
        pop_adm1c,
        pop_adm2c,
        pop_col,
        admin2_mapping=admin2_mapping,
        admin1_mapping=admin1_mapping,
    )
    df_ipcpop = merge_ipcpop(
        df_allipc,
        df_pop,
        country.capitalize(),
        pop_adm1c,
        pop_adm2c,
        ipc_adm1c,
        ipc_adm2c,
    )
    df_ipcpop.to_csv(
        f"{RESULT_FOLDER}{country}_admin2_fewsnet_combined_{start_date}_{end_date}.csv"
    )
    df_adm1 = aggr_admin1(df_ipcpop, ipc_adm1c)
    df_adm1.to_csv(
        f"{RESULT_FOLDER}{country}_admin1_fewsnet_combined_{start_date}_{end_date}.csv"
    )


if __name__ == "__main__":
    args = parse_args()
    config_logger(level="warning")
    main(args.country_iso3.upper())
