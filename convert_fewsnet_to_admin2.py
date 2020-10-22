import geopandas as gpd
import pandas as pd
import os
import numpy as np
from utils import parse_args, parse_yaml
from pathlib import Path


def shapefiles_to_df(path, status, dates, region, regionabb):
    """
    Compile the shapefiles to a dataframe
    Args:
        path: path to directory that contains the FewsNet shapefiles
        status: type of FewsNet prediction: CS (current), ML1 (near-term projection) or ML2 (medium-term projection)
        dates: list of dates for which FewsNet data should be included. The files of these dates have to be present in the directory (path)!
        region: region that the fewsnet data covers, e.g. "east-africa"
        regionabb: abbreviation of the region that the fewsnet data covers, e.g. "EA"

    Returns:
        df: DataFrame that contains all the shapefiles of Fewsnet for the given dates, status and regions
    """
    df = gpd.GeoDataFrame()
    for d in dates:
        # path to fewsnet data
        shape = path + region + d + "/" + regionabb + "_" + d + "_" + status + ".shp"
        if os.path.exists(shape):
            gdf = gpd.read_file(shape)
            gdf["date"] = pd.to_datetime(d, format="%Y%m")
            df = df.append(gdf, ignore_index=True)
    return df


def merge_admin2(df, path_admin, status, adm0c, adm1c, adm2c):
    """
    Merge the geographic boundary information shapefile with the FewsNet dataframe.
    Args:
        df: DataFrame with the Fewsnet data and geometries
        path_admin: path to file with admin(2) boundaries
        status: type of FewsNet prediction: CS (current), ML1 (near-term projection) or ML2 (medium-term)
        adm0c: column name of the admin0 level name, in boundary data
        adm1c: column name of the admin1 level name, in boundary data
        adm2c: column name of the admin2 level name, in boundary data

    Returns:
        overlap: dataframe with the regions per admin2 for each IPC level
    """
    admin2 = gpd.read_file(path_admin)
    admin2 = admin2[[adm0c, adm1c, adm2c, "geometry"]]
    overlap = gpd.overlay(admin2, df, how="intersection")
    overlap = overlap.drop_duplicates()
    overlap["area"] = overlap["geometry"].to_crs("EPSG:3395").area
    columns = [adm0c, adm1c, adm2c, status, "date", "geometry", "area"]
    overlap = overlap[columns]
    return overlap


def return_max_cs(date, df, dfadcol, status, adm0c, adm1c, adm2c):
    """
    Return the IPC value that is assigned to the largest area (in m2) for the given Admin Level 2 region
    It is discussable if this is the best approach to select the IPC admin2 level. One could also try to work with more local population estimates
    Args:
        date: string with the date of the FewsNet analysis
        df: DataFrame that contains the geometrys per IPC level per Admin2 (output from merge_admin2)
        dfadcol: one row of the df
        status: type of FewsNet prediction: CS (current), ML1 (near-term projection) or ML2 (medium-term)
        adm0c: column name of the admin0 level name, in boundary data
        adm1c: column name of the admin1 level name, in boundary data
        adm2c: column name of the admin2 level name, in boundary data


    Returns:
        row: row of the df which has the largest area within the given Admin Level 2 region (defined by dfadcol)
    """
    sub = df.loc[
        (df["date"] == date)
        & (df[adm1c] == dfadcol[adm1c])
        & (df[adm2c] == dfadcol[adm2c])
    ]
    # if there are nan (=0) values we prefer to take the non-nan values, even if those represent a smaller area
    # however if there are only nans (=0s) in an admin2 region, we do return one of those rows
    if len(sub[sub[status] != 0]) > 0:
        sub = sub[sub[status] != 0]
    mx = sub["area"].max()
    row = sub[["date", adm0c, adm1c, adm2c, status]].loc[sub["area"] == mx]
    return row


def gen_csml1m2(
    ipc_path,
    bound_path,
    status,
    dates,
    adm0c,
    adm1c,
    adm2c,
    region,
    regionabb,
):
    """
    Generate a DataFrame with the IPC level per Admin 2 Level, defined by the level that covers the largest area
    The DataFrame includes all the dates given as input, and covers one type of classification given by status
    Args:
        ipc_path: path to the directory with the fewsnet data
        bound_path: path to the file with the admin2 boundaries
        status: type of FewsNet prediction: CS (current), ML1 (near-term projection) or ML2 (medium-term)
        dates: list of dates for which FewsNet data should be included. The files of these dates have to be present in the directory (ipc_path)!
        adm0c: column name of the admin0 level name, in boundary data
        adm1c: column name of the admin1 level name, in boundary data
        adm2c: column name of the admin2 level name, in boundary data
        region: region that the fewsnet data covers, e.g. "east-africa"
        regionabb: abbreviation of the region that the fewsnet data covers, e.g. "EA"

    Returns:
        new_df: DataFrame that contains one row per Admin2-date combination, which indicates the IPC level
    """
    df_ipc = shapefiles_to_df(ipc_path, status, dates, region, regionabb)
    overlap = merge_admin2(df_ipc, bound_path, status, adm0c, adm1c, adm2c)
    # replace other values than 1-5 by 0 (these are 99,88,66 and indicate missing values, nature areas or lakes)
    overlap.loc[overlap[status] >= 5, status] = 0
    new_df = pd.DataFrame(columns=["date", status, adm0c, adm1c, adm2c])

    for d in overlap["date"].unique():
        # all unique combinations of admin1 and admin2 regions (sometimes an admin2 region can be in two admin1 regions)
        df_adm12c = overlap[[adm1c, adm2c]].drop_duplicates()
        for index, a in df_adm12c.iterrows():
            row = return_max_cs(d, overlap, a, status, adm0c, adm1c, adm2c)
            new_df = new_df.append(row)
    new_df.replace(0, np.nan, inplace=True)
    return new_df


def main(country_iso3, config_file="config.yml"):
    """
    This script takes the FEWSNET IPC shapefiles provided by on fews.net and overlays them with an admin2 shapefile, in order
    to provide an IPC value for each admin2 district. In the case where there are multiple values per district, the IPC value
    with the maximum area is selected.

    In FEWSNET IPC, there are 3 possible categories of maps - 'CS' (Current State), 'ML1' (3 months projection), 'ML2' (6 months projection).
    Any one of these is compatible with the script.

    Possible IPC values range from 1 (least severe) to 5 (most severe, famine).

    Set all variables, run the function for the different forecasts, and save as csv
    """
    parameters = parse_yaml(config_file)[country_iso3]

    country = parameters["country_name"]
    region = parameters["region"]
    regioncode = parameters["regioncode"]
    admin2_shp = parameters["path_admin2_shp"]
    adm0c = parameters["adm0c_bound"]
    adm1c = parameters["adm1c_bound"]
    adm2c = parameters["adm2c_bound"]
    PATH_FEWSNET = "Data/FewsNetRaw/"
    PATH_RESULT = f"{country}/Data/FewsNetAdmin2/"
    ADMIN2_PATH = f"{country}/Data/{admin2_shp}"
    STATUS_LIST = ["CS", "ML1", "ML2"]

    # create output dir if it doesn't exist yet
    Path(PATH_RESULT).mkdir(parents=True, exist_ok=True)

    for STATUS in STATUS_LIST:
        df = gen_csml1m2(
            PATH_FEWSNET,
            ADMIN2_PATH,
            STATUS,
            parameters["fewsnet_dates"],
            adm0c,
            adm1c,
            adm2c,
            region,
            regioncode,
        )
        df.to_csv(
            PATH_RESULT
            + country
            + "_admin2_fewsnet_"
            + df.date.min().strftime("%Y%m%d")
            + "_"
            + df.date.max().strftime("%Y%m%d")
            + "_"
            + STATUS
            + ".csv"
        )


if __name__ == "__main__":
    args = parse_args()
    main(args.country_iso3.upper())
