"""
This script takes the FEWSNET IPC shapefiles provided by on fews.net and overlays them with an admin2 shapefile, in order
to provide an IPC value for each admin2 district. In the case where there are multiple values per district, the IPC value
with the maximum area is selected.

The configurations are set up inside the script. For usability, they should eventually be set up in a config file or
passed externally.

In FEWSNET IPC, there are 3 possible categories of maps - 'CS' (Current State), 'ML1' (3 months projection), 'ML2' (6 months projection).
Any one of these is compatible with the script.

Possible IPC values range from 1 (least severe) to 5 (most severe, famine).

"""

# Imports

import geopandas as gpd
import pandas as pd
import os
import numpy as np


def shapefiles_to_df(path, status, dates, region, regionabb):
    """
    Compile the shapefiles to a dataframe
    """
    df = gpd.GeoDataFrame()
    for d in dates:
        shape = path + region + d + "/" + regionabb + "_" + d + "_" + status + ".shp"
        if os.path.exists(shape):
            gdf = gpd.read_file(shape)
            gdf["date"] = pd.to_datetime(d, format="%Y%m")
            df = df.append(gdf, ignore_index=True)
    return df


def merge_admin2(df, path_admin, status, adm0c, adm1c, adm2c):
    """
    Merge the geographic boundary information shapefile with the IPC shapefile.
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
    Return the maximum IPC value in an admin2 district.
    """
    sub = df.loc[
        (df["date"] == date)
        & (df[adm1c] == dfadcol[adm1c])
        & (df[adm2c] == dfadcol[adm2c])
    ]
    # if there are nan (=0) values we prefer to take the non-nan values, even if those represent a smaller area
    if len(sub[sub[status] != 0]) > 0:
        sub = sub[sub[status] != 0]
    mx = sub["area"].max()
    row = sub[["date", adm0c, adm1c, adm2c, status]].loc[sub["area"] == mx]
    return row


# def return_max_cs(date, df, dfadcol, status, adm0c, adm1c, adm2c):
#     """
#     Return the maximum IPC value in an admin2 district.
#     """
#     sub = df.loc[
#         (df["date"] == date)
#         & (df[adm1c] == dfadcol[adm1c])
#         & (df[adm2c] == dfadcol[adm2c])
#     ]
#     mx = sub[status].max()
#     print(mx)
#     print(date)
#     row = sub[["date", adm0c, adm1c, adm2c, status]].loc[sub[status] == mx].iloc[0]
#     # print(row)
#     return row


def gen_csml1m2(
    ipc_path,
    bound_path,
    status,
    dates,
    adm0c="ADM0_EN",
    adm1c="ADM1_EN",
    adm2c="ADM2_EN",
    region="east-africa",
    regionabb="EA",
):
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


def main():
    """
    Import the FEWSNET IPC maps, select the appropriate geographic boundary, select the max IPC category.
    Saves a CSV to file and returns the dataframe.
    """

    DATES = [
        "200907",
        "200910",
        "201001",
        "201004",
        "201007",
        "201010",
        "201101",
        "201104",
        "201107",
        "201110",
        "201201",
        "201204",
        # "201207", #no data for Malawi
        "201210",
        "201301",
        "201304",
        "201307",
        "201310",
        "201401",
        "201404",
        "201407",
        "201410",
        "201501",
        "201504",
        "201507",
        "201510",
        "201602",
        "201606",
        "201610",
        "201706",
        "201710",
        "201802",
        "201806",
        "201810",
        "201812",
        "201902",
        "201906",
        "201910",
        # "202002",
        # "202003",
        # "202004",
        # "202005",
        # "202006",
        # "202007",
        # "202008"
    ]
    STATUS_LIST = ["CS", "ML1", "ML2"]
    COUNTRY = "malawi"  # "ethiopia"
    REGION = "southern-africa"  # "east-africa"
    REGIONCODE = "SA"  # "EA"
    PATH = "Data/FewsNetRaw/"
    PATH_RESULT = f"{COUNTRY}/Data/FewsNetAdmin2/"  # OldShp/"
    ADMIN2_SHP = "mwi_adm_nso_20181016_shp/mwi_admbnda_adm2_nso_20181016.shp"  # "ET_Admin2_OCHA_2019/eth_admbnda_adm2_csa_bofed_20190827.shp" # 'ET_Admin2_2014/ET_Admin2_2014.shp'
    ADMIN2_PATH = f"{COUNTRY}/Data/{ADMIN2_SHP}"

    for STATUS in STATUS_LIST:
        df = gen_csml1m2(
            PATH,
            ADMIN2_PATH,
            STATUS,
            DATES,
            adm0c="ADM0_EN",
            adm1c="ADM1_EN",
            adm2c="ADM2_EN",
            region=REGION,
            regionabb=REGIONCODE,
        )
        df.to_csv(
            PATH_RESULT
            + COUNTRY
            + "_admin2_fewsnet_"
            + df.date.min().strftime("%Y%m%d")
            + "_"
            + df.date.max().strftime("%Y%m%d")
            + "_"
            + STATUS
            + ".csv"
        )


if __name__ == "__main__":
    main()
