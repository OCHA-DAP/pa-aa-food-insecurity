import geopandas as gpd
import shapefile as shp
import matplotlib.pyplot as plt
import pandas as pd
import rtree
import seaborn as sns
import matplotlib
import numpy as np
import warnings

def get_new_name(name, n_dict):
    if name in n_dict.keys():
        return n_dict[name]
    else:
        return name

def merge_ipcstatus(cs_path,ml1_path,ml2_path,adm2c):
    cs = pd.read_csv(cs_path,index_col=0)
    ml1 = pd.read_csv(ml1_path,index_col=0)
    ml2 = pd.read_csv(ml2_path,index_col=0)

    # merge the CS, ML1 and ML2 in one df
    df_ipc = cs.merge(ml1[['date', adm2c, 'ML1']], on=[adm2c, 'date'], how='left')
    df_ipc = df_ipc.merge(ml2[['date', adm2c, 'ML2']], on=[adm2c, 'date'], how='left')
    df_ipc['date'] = pd.to_datetime(df_ipc['date'])
    return df_ipc

def load_popdata(pop_path,pop_adm1c,pop_adm2c,admin2_mapping=None,admin1_mapping=None):
    # import population data (not clear where data comes from)
    df_pop = pd.read_csv(pop_path)
    # remove whitespace at end of string
    df_pop[pop_adm2c] = df_pop[pop_adm2c].str.rstrip()
    if admin2_mapping:
        df_pop[pop_adm2c] = df_pop[pop_adm2c].apply(lambda x: get_new_name(x, admin2_mapping))
    if admin1_mapping:
        df_pop[pop_adm1c] = df_pop[pop_adm1c].apply(lambda x: get_new_name(x, admin1_mapping))
    print("Total population: ",df_pop.Total.sum())
    return df_pop

def get_adjusted(row,perc_dict):
    year = str(row['date'].year)
    adjustment = perc_dict[year]
    return row['Total']*adjustment

def merge_ipcpop(df_ipc,df_pop,pop_adm1c,pop_adm2c,ipc_adm1c,ipc_adm2c):
    df_ipcp = df_ipc.merge(df_pop[[pop_adm1c, pop_adm2c, 'Total']], how='left',
                           left_on=[ipc_adm1c,ipc_adm2c], right_on=[pop_adm1c, pop_adm2c])

    #dict to indicate relative increase in population over the years
    pop_dict = {'2009': 11500000, '2010': 11890000, '2011': 12290000, '2012': 12710000, '2013': 13130000,
                '2014': 13570000, '2015': 14010000, '2016': 14450000, '2017': 14900000, '2018': 14900000,
                '2019': 14900000, '2020': 14900000}
    # estimate percentage of population at given year in relation to 2020 estimate
    perc_dict = {k: v / pop_dict['2020'] for k, v in pop_dict.items()}

    df_ipcp['adjusted_population'] = df_ipcp.apply(lambda x: get_adjusted(x,perc_dict), axis=1)
    if df_ipcp[df_ipcp.date=="2019-10"].Total.sum()!=df_pop.Total.sum():
        warnings.warn("Population data merged with IPC doesn't match the original population numbers")

    return df_ipcp


def main():
    cs_path='Data/ethiopia_admin2_fewsnet_20090701_20191001_CS.csv'
    ml1_path='Data/ethiopia_admin2_fewsnet_20090701_20191001_ML1.csv'
    ml2_path='Data/ethiopia_admin2_fewsnet_20090701_20191001_ML2.csv'
    pop_path='Data/eth_admpop_adm2_2020.csv'
    pop_adm2c="admin2Name_en"
    pop_adm1c = "admin1Name_en"
    ipc_adm1c = "ADM1_EN"
    ipc_adm2c="ADM2_EN"
    #mapping from population data to ipc data in Admin2 names (so names that don't correspond)
    admin2_mapping = {'Etang Special': 'Etang Special woreda', 'Zone 4  (Fantana Rasu)': 'Zone 4 (Fantana Rasu)'}

    df_allipc=merge_ipcstatus(cs_path,ml1_path,ml2_path,ipc_adm2c)
    df_pop=load_popdata(pop_path, pop_adm1c, pop_adm2c, admin2_mapping=admin2_mapping)
    df_ipcpop=merge_ipcpop(df_allipc,df_pop,pop_adm1c,pop_adm2c,ipc_adm1c,ipc_adm2c)

if __name__=='__main__':
    main()