import pandas as pd
import os
import geopandas as gpd
from rasterstats import zonal_stats
import numpy as np
from utils import parse_args, parse_yaml, config_logger
from pathlib import Path
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)


def population_region(df, pop_path):
    """
    Calculate population per geometry in df
    Args:
        df: GeoPandas DataFrame with the regions of interest
        pop_path: path to the population raster file

    Returns:
        df: GeoPandas DataFrame with the population per region
    """
    # get total population per admin
    df_pop = df.copy()
    df_pop["pop"] = pd.DataFrame(
        zonal_stats(vectors=df["geometry"], raster=pop_path, stats="sum")
    )["sum"]
    return df_pop


def merge_fewsnet_population(fews_path, adm_path, pop_path, date, period, adm1c, adm2c):
    """
    Compute the population per IPC phase per adm2 region for the data defined in fews_path
    Args:
        fews_path: path to the shapefile with FewsNet data
        adm_path: path to the shapefile with admin2 boundaries
        pop_path: path to the raster file with population data
        date: date of the data defined in fews_path
        period: type of FewsNet prediction: CS (current), ML1 (near-term projection) or ML2 (medium-term projection)
        adm1c: column name of the admin1 level name, in adm_path data
        adm2c: column name of the admin2 level name, in adm_path data

    Returns:
        df_gp: DataFrame with the population per IPC phase per Admin2
    """
    df_fews = gpd.read_file(fews_path)
    df_adm = gpd.read_file(adm_path)
    # get fewsnet area (livelihood) per admin region in df_adm (generally admin2)
    # overlay takes really long to compute, but could not find a better method
    df_fewsadm = gpd.overlay(df_adm, df_fews, how="intersection")

    # calculate population per area resulting from the overlay
    # in pop_path, the value per cell is the population of that cell, so we want the sum of them
    # in the calculation a cell is considered to belong to an area if the center of that cell is inside the area.
    # see https://pythonhosted.org/rasterstats/manual.html#rasterization-strategy
    df_fewsadm = df_fewsadm.merge(
        population_region(df_fewsadm, pop_path)[[adm2c, "pop"]], on=adm2c
    )
    df_fewsadm["pop2"] = pd.DataFrame(
        zonal_stats(vectors=df_fewsadm["geometry"], raster=pop_path, stats="sum")
    )["sum"]
    # convert the period values (1 to 5) to str
    df_fewsadm[period] = df_fewsadm[period].astype(int).astype(str)
    df_g = df_fewsadm.groupby([adm1c, adm2c, period], as_index=False).sum()
    # set the values of period as columns (1,2,3,4,5,99)
    df_gp = df_g.pivot(index=[adm1c, adm2c], columns=period, values="pop")
    df_gp = df_gp.add_prefix(f"{period}_")
    df_gp.columns.name = None
    df_gp = df_gp.reset_index()
    df_gp["date"] = pd.to_datetime(date, format="%Y%m")
    return df_gp


def combine_fewsnet_projections(
    country_iso3,
    dates,
    folder_fews,
    folder_pop,
    admin_path,
    shp_adm1c,
    shp_adm2c,
    region,
    regionabb,
    country_iso2,
    result_folder,
    start_date,
    end_date,
):
    """
    Retrieve all FewsNet data, and calculate the population per IPC phase per date-admin combination
    The results are saved to a csv, one containing the admin2 calculations and one the admin1.
    Args:
        country_iso3: string with iso3 code
        dates: list of dates for which FewsNet data should be included
        folder_fews: path to folder that contains the FewsNet data
        folder_pop: path to folder that contains the population data
        admin_path: path to the shapefile with admin2 boundaries
        shp_adm1c: column name of the admin1 level name, in adm_path data
        shp_adm2c: column name of the admin2 level name, in adm_path data
        region: region that the fewsnet data covers, e.g. "east-africa"
        regionabb: abbreviation of the region that the fewsnet data covers, e.g. "EA"
        iso2_code: iso2 code of the country of interest
        result_folder: path to folder to which to save the output
        start_date: first date that is included in the data
        end_date: last date that is included in the data
    """
    # all periods in the FewsNet data
    period_list = ["CS", "ML1", "ML2"]
    df = gpd.GeoDataFrame()
    # initialize progress bar
    pbar = tqdm(dates)
    # loop over dates
    for d in pbar:
        df_fews_list = []
        for period in period_list:
            pbar.set_description(f"Processing date {d}, period {period}")
            # path to fewsnet data
            # sometimes fewsnet publishes per region, sometimes per country
            fews_path = None
            fews_region_path = f"{folder_fews}{region}{d}/{regionabb}_{d}_{period}.shp"
            fews_country_path = (
                f"{folder_fews}{country_iso2}_{d}/{country_iso2}_{d}_{period}.shp"
            )
            if os.path.exists(fews_region_path):
                fews_path = fews_region_path
            elif os.path.exists(fews_country_path):
                fews_path = fews_country_path

            # path to population data
            pop_path = f"{folder_pop}/{country_iso3.lower()}_ppp_{d[:4]}_1km_Aggregated_UNadj.tif"

            if fews_path and os.path.exists(pop_path):
                df_fews = merge_fewsnet_population(
                    fews_path, admin_path, pop_path, d, period, shp_adm1c, shp_adm2c
                )
                df_fews_list.append(df_fews)
            elif not fews_path:
                logger.warning(
                    f"FewsNet file for {d} and {period} not found. Skipping to next date and period."
                )
            elif not os.path.exists(pop_path):
                logger.warning(
                    f"Worldpop file for {d} not found. Skipping to next date"
                )

        if df_fews_list:
            # concat the dfs of the different "periods", with an unique entry per date-adm1-adm2 combination
            df_listind = [
                df.set_index([shp_adm1c, shp_adm2c, "date"]) for df in df_fews_list
            ]
            df_comb = pd.concat(df_listind, axis=1).reset_index()

            # add ipc_cols that are not present in the data (commonly level 5 columns)
            ipc_cols = [f"{period}_{i}" for period in period_list for i in range(1, 6)]
            for i in ipc_cols:
                if i not in df_comb.columns:
                    df_comb[i] = np.nan

            # calculate population per period over all IPC levels
            for period in period_list:
                # population that has an IPC level assigned
                df_comb[f"pop_{period}"] = df_comb[
                    [f"{period}_{i}" for i in range(1, 6)]
                ].sum(axis=1, min_count=1)
                # all columns that contain "period", i.e. also the 99 valued columns
                period_cols = [c for c in df_comb.columns if period in c]
                # total population in the admin region that is included in the FewsNet data (i.e. also including the 99 values)
                df_comb[f"pop_Total_{period}"] = df_comb[period_cols].sum(
                    axis=1, min_count=1
                )

            # there can be a slight disperancy between the fewsnet and admin shapefile. Since we take the intersection, some areas might then be lost
            # here we calculate the total population based on the admin shape, and compare it to the total population of the overlay of the admin and fewsnet shapefiles
            # if the disperancy is larger than 1 percent, we raise a warning
            df_adm = gpd.read_file(admin_path)
            df_pop_check = df_comb.merge(
                population_region(df_adm, pop_path)[[shp_adm2c, "pop"]], on=shp_adm2c
            )
            pop_diff = (
                (df_pop_check["pop"].sum() - df_comb[f"pop_Total_CS"].sum())
                / df_comb[f"pop_Total_CS"].sum()
                * 100
            )
            if pop_diff > 1:
                logger.warning(f"Population for date {d} differs with {pop_diff:.2f}%")

            df = df.append(df_comb, ignore_index=True)

    if not df.empty:
        # set general admin names
        df.rename(columns={shp_adm1c: "ADMIN1", shp_adm2c: "ADMIN2"}, inplace=True)
        # TODO: decide what kind of filename we want to use for the output, i.e. do we always want to overwrite the output or not
        df.to_csv(
            f"{result_folder}{country_iso3.lower()}_admin2_fewsnet_worldpop_{start_date}_{end_date}.csv"
        )
        # aggregate to admin1 by summing (and set to nan if no data for a date-adm1 combination
        df_adm1 = (
            df.drop("ADMIN2", axis=1)
            .groupby(["date", "ADMIN1"])
            .agg(lambda x: np.nan if x.isnull().all() else x.sum())
            .reset_index()
        )
        df_adm1.rename(columns={"pop_ADMIN2": "pop_ADMIN1"}, inplace=True)
        df_adm1.to_csv(
            f"{result_folder}{country_iso3.lower()}_admin1_fewsnet_worldpop_{start_date}_{end_date}.csv"
        )
    else:
        logger.warning("No data found for the given dates")


def main(country_iso3, config_file="config.yml"):
    """
    Define parameters and call functions
    Args:
        country_iso3: string with iso3 code
        config_file: path to config file
    """
    parameters = parse_yaml(config_file)[country_iso3]

    country = parameters["country_name"]
    region = parameters["region"]
    regioncode = parameters["regioncode"]
    country_iso2 = parameters["iso2_code"]
    dates = parameters["fewsnet_dates"]
    admin2_shp = parameters["path_admin2_shp"]
    shp_adm1c = parameters["shp_adm1c"]
    shp_adm2c = parameters["shp_adm2c"]
    start_date = parameters["start_date"]
    end_date = parameters["end_date"]
    # TODO: to make variables more generalizable with a config.py. Inspiration from pa-covid-model-parameterization
    # pop_dir = os.path.join(config.DIR_PATH, country, config.POP_DIR)
    FOLDER_FEWSNET = "Data/FewsNetRaw/"
    FOLDER_POP = f"{country}/Data/WorldPop"
    ADMIN2_PATH = f"{country}/Data/{admin2_shp}"
    RESULT_FOLDER = f"{country}/Data/FewsNetWorldPop/"
    # create output dir if it doesn't exist yet
    Path(RESULT_FOLDER).mkdir(parents=True, exist_ok=True)
    combine_fewsnet_projections(
        country_iso3,
        dates,
        FOLDER_FEWSNET,
        FOLDER_POP,
        ADMIN2_PATH,
        shp_adm1c,
        shp_adm2c,
        region,
        regioncode,
        country_iso2,
        RESULT_FOLDER,
        start_date,
        end_date,
    )


if __name__ == "__main__":
    args = parse_args()
    config_logger(level="warning")
    main(args.country_iso3.upper())
