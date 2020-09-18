import pandas as pd
import numpy as np
import warnings


def get_new_name(name, n_dict):
    if name in n_dict.keys():
        return n_dict[name]
    else:
        return name


def merge_ipcstatus(cs_path, ml1_path, ml2_path, adm1c, adm2c):
    """
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
    # import population data (not clear where data comes from)
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
    df_pop.rename(columns={pop_col: "Total"}, inplace=True)
    return df_pop


def create_histpopdict(
    df_data, histpop_path="Data/Worldbank_TotalPopulation.csv", country="Ethiopia"
):
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
    year = str(row["date"].year)
    adjustment = perc_dict[year]
    if pd.isna(row["Total"]):
        return row["Total"]
    else:
        return int(row["Total"] * adjustment)


def merge_ipcpop(df_ipc, df_pop, pop_adm1c, pop_adm2c, ipc_adm1c, ipc_adm2c):
    df_ipcp = df_ipc.merge(
        df_pop[[pop_adm1c, pop_adm2c, "Total"]],
        how="left",
        left_on=[ipc_adm1c, ipc_adm2c],
        right_on=[pop_adm1c, pop_adm2c],
    )

    # dict to indicate relative increase in population over the years
    pop_dict = create_histpopdict(df_ipcp)
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

    return df_ipcp


def aggr_admin1(df, adm1c):
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


def get_trigger(row, status, level, perc):
    # range till 6 cause 5 is max level
    cols = [f"{status}_{l}" for l in range(level, 6)]
    if np.isnan(row[f"pop_{status}"]):
        return np.nan
    if row[cols].sum() >= row[f"pop_{status}"] / (100 / perc):
        return 1
    else:
        return 0


def get_trigger_increase(row, level, perc):
    # range till 6 cause 5 is max level
    cols_ml1 = [f"ML1_{l}" for l in range(level, 6)]
    cols_cs = [f"CS_{l}" for l in range(level, 6)]
    if row[["pop_CS", "pop_ML1"]].isnull().values.any():
        return np.nan
    if row[cols_ml1].sum() == 0:
        return 0
    if row[cols_ml1].sum() >= row[cols_cs].sum() * (1 + (perc / 100)):
        return 1
    else:
        return 0


def main():
    COUNTRY = "ethiopia"  # "malawi"  #
    RESULT_FOLDER = f"{COUNTRY}/Data/FewsNetPopulation/"
    fnfolder = f"{COUNTRY}/Data/FewsNetAdmin2/"
    START_DATE = "20090701"
    END_DATE = "20200801"
    cs_path = f"{fnfolder}{COUNTRY}_admin2_fewsnet_{START_DATE}_{END_DATE}_CS.csv"
    ml1_path = f"{fnfolder}{COUNTRY}_admin2_fewsnet_{START_DATE}_{END_DATE}_ML1.csv"
    ml2_path = f"{fnfolder}{COUNTRY}_admin2_fewsnet_{START_DATE}_{END_DATE}_ML2.csv"

    POP_FILE = "eth_admpop_adm2_2020.csv"  # "Population_OCHA_2018/mwi_pop_adm2_32_districts.csv"  #
    POP_PATH = f"{COUNTRY}/Data/{POP_FILE}"
    pop_adm1c = "admin1Name_en"  # "ADM1_EN"  #
    pop_adm2c = "admin2Name_en"  # "ADM2_EN32"  #
    ipc_adm1c = "ADM1_EN"  # "ADMIN1" #
    ipc_adm2c = "ADM2_EN"  # "ADMIN2" #
    POP_COL = "Total"  # "p2019pop"  #
    # mapping from population data to ipc data in Admin2 names (so names that don't correspond)
    admin2_mapping = {
        "Etang Special": "Etang Special woreda",
        "Zone 4  (Fantana Rasu)": "Zone 4 (Fantana Rasu)",
    }
    # admin2_mapping = None
    admin1_mapping = None

    # Ethiopia other shapefile
    # admin2_mapping = {'Zone 1 (Awsi Rasu)': 'Awusi', 'Zone 2 (Kilbet Rasu)': 'Kilbati', 'Zone 3 (Gabi Rasu)': 'Gabi',
    #                   'Zone 4  (Fantana Rasu)': 'Fanti', 'Zone 5 (Hari Rasu)': 'Khari', 'Central': 'Central Tigray',
    #                   'Eastern': 'East Tigray', 'North Western': 'Northwest Tigray',
    #                   'South Eastern': 'Southeast Tigray',
    #                   'Western': 'West Tigray', 'Southern': 'South Tigray', 'Mejenger': 'Mezhenger', 'Nuwer':
    #                       'Nuer', 'Etang Special': 'Itang', 'Agnewak': 'Agniwak', 'Dire Dawa rural': 'Dire Dawa',
    #                   'Dire Dawa urban': 'Dire Dawa', 'North Wello': 'North Wollo', 'Wag Hamra': 'Wag Himra',
    #                   'Liban': 'Liben', 'Siti': 'Sitti', 'Shabelle': 'Shebelle', 'Doolo': 'Dollo',
    #                   'Mao Komo': 'Mao-Komo',
    #                   'Halaba Special': 'Alaba', 'Gamo': 'Gamo Gofa', 'Gofa': 'Gamo Gofa', 'Guraghe': 'Gurage',
    #                   'Kefa': 'Keffa', 'Dawuro': 'Dawro', 'Ilu Aba Bora': 'Ilubabor'}
    #
    # admin1_mapping = {'SNNP': 'SNNPR'}

    df_allipc = merge_ipcstatus(cs_path, ml1_path, ml2_path, ipc_adm1c, ipc_adm2c)
    df_pop = load_popdata(
        POP_PATH,
        pop_adm1c,
        pop_adm2c,
        POP_COL,
        admin2_mapping=admin2_mapping,
        admin1_mapping=admin1_mapping,
    )
    df_ipcpop = merge_ipcpop(
        df_allipc, df_pop, pop_adm1c, pop_adm2c, ipc_adm1c, ipc_adm2c
    )
    df_ipcpop.to_csv(
        f"{RESULT_FOLDER}{COUNTRY}_admin2_fewsnet_population_{START_DATE}_{END_DATE}.csv"
    )
    df_adm1 = aggr_admin1(df_ipcpop, ipc_adm1c)
    df_adm1.to_csv(
        f"{RESULT_FOLDER}{COUNTRY}_admin1_fewsnet_population_{START_DATE}_{END_DATE}.csv"
    )


if __name__ == "__main__":
    main()
