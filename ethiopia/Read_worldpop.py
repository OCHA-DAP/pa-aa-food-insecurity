# from rasterstats import zonal_stats
# stats = zonal_stats('ET_Admin2_OCHA_2019/eth_admbnda_ADM1_csa_bofed_20190827.shp', 'eth_ppp_2019_1km_Aggregated_UNadj.tif',sstats=["sum"])
# print(stats)

from rasterstats import zonal_stats
import geopandas as gpd
import pandas as pd
import os
import numpy as np


def read_fewsnet(fews_path, adm_path, pop_path, date, status, adm_cols):
    df_fews = gpd.read_file(fews_path)
    df_adm = gpd.read_file(adm_path)
    df_fewsadm = gpd.overlay(df_adm, df_fews, how="intersection")
    df_fewsadm[f"pop"] = pd.DataFrame(
        zonal_stats(vectors=df_fewsadm["geometry"], raster=pop_path, stats="sum")
    )["sum"]
    df_fewsadm[status] = df_fewsadm[status].astype(int).astype(str)
    df_g = df_fewsadm.groupby(adm_cols + [status], as_index=False).sum()
    df_gp = df_g.pivot(index=adm_cols, columns=status, values="pop")
    df_gp = df_gp.add_prefix(f"{status}_")
    df_gp.columns.name = None
    df_gp = df_gp.reset_index()
    df_gp["date"] = pd.to_datetime(date, format="%Y%m")
    return df_gp


#
def couple(
    fewsdir,
    adm_path,
    pop_path,
    dates,
    region="east-africa",
    regionabb="EA",
    adm_cols=["ADM1_EN", "ADM2_EN"],
):

    # df = gpd.GeoDataFrame()
    for d in dates:
        print(d)
        df_list = []
        for status in ["CS", "ML1", "ML2"]:
            print(status)
            shape_path = (
                fewsdir + region + d + "/" + regionabb + "_" + d + "_" + status + ".shp"
            )
            if os.path.exists(shape_path):
                df_fews = read_fewsnet(
                    shape_path, adm_path, pop_path, d, status, adm_cols
                )
                # print(df_fews)
                # INPUT_FEWS = f'../../Data/FewsNetRaw/east-africa201902/EA_201902_{status}.shp'
                df_list.append(df_fews)
        df_lista = [df.set_index(adm_cols + ["date"]) for df in df_list]
        df_comb = pd.concat(df_lista, axis=1).reset_index()
        s_cols = (
            [f"CS_{i}" for i in range(1, 6)]
            + [f"ML1_{i}" for i in range(1, 6)]
            + [f"ML2_{i}" for i in range(1, 6)]
        )
        for i in s_cols:
            if i not in df_comb.columns:
                df_comb[i] = np.nan
                # df = df.append(gdf, ignore_index=True)
    return df_comb


INPUT_SHP_ADM2 = "Data/ET_Admin2_OCHA_2019/eth_admbnda_adm2_csa_bofed_20190827.shp"
INPUT_SHP_ADM1 = "Data/ET_Admin1_OCHA_2019/eth_admbnda_adm1_csa_bofed_20190827.shp"
INPUT_FEWSCS = "../Data/FewsNetRaw/east-africa201902/EA_201902_CS.shp"
INPUT_FEWSML1 = "../Data/FewsNetRaw/east-africa201902/EA_201902_ML1.shp"
INPUT_FEWSML2 = "../Data/FewsNetRaw/east-africa201902/EA_201902_ML2.shp"
INPUT_TIFF_POP = "Data/WorldPopUNAdj/eth_ppp_2019_1km_Aggregated_UNadj.tif"
FEWSDIR = "../Data/FewsNetRaw/"

df = couple(FEWSDIR, INPUT_SHP_ADM1, INPUT_TIFF_POP, ["201902"], adm_cols=["ADM1_EN"])
df.to_csv("Experiments/Data/worldpop_test.csv")
# dir_path = os.path.dirname(os.path.realpath(__file__))
# print(dir_path)
# ADM1=gpd.read_file(INPUT_SHP)
# FEWSCS=gpd.read_file(INPUT_FEWSCS)
# FEWSML1=gpd.read_file(INPUT_FEWSML1)
# FEWSML2=gpd.read_file(INPUT_FEWSML2)
#
# FEWSCS_ADM1=gpd.overlay(ADM1,FEWSCS,how='intersection')
# FEWSML1_ADM1=gpd.overlay(ADM1,FEWSML1,how='intersection')
# FEWSML2_ADM1=gpd.overlay(ADM1,FEWSML2,how='intersection')
#
# FEWSCS_ADM1['pop'] = pd.DataFrame(zonal_stats(vectors=FEWSCS_ADM1['geometry'], raster=INPUT_TIFF_POP, stats='sum'))['sum']
# FEWSML1_ADM1['pop'] = pd.DataFrame(zonal_stats(vectors=FEWSML1_ADM1['geometry'], raster=INPUT_TIFF_POP, stats='sum'))['sum']
# FEWSML2_ADM1['pop'] = pd.DataFrame(zonal_stats(vectors=FEWSML2_ADM1['geometry'], raster=INPUT_TIFF_POP, stats='sum'))['sum']
#
# FEWSCS_ADM1.to_file('Data/FewsNetAdmin1/FEWSCS_ADM1.shp')
# FEWSML1_ADM1.to_file('Data/FewsNetAdmin1/FEWSML1_ADM1.shp')
# FEWSML2_ADM1.to_file('Data/FewsNetAdmin1/FEWSML2_ADM1.shp')
#
