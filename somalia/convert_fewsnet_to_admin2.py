#import

import geopandas as gpd
import pandas as pd
from datetime import date

PATH = './east-africa202004/EA_202004_'
STATUS = 'ML2' # choice of CS, ML1, ML2
ADMIN2_SHP = 'som_adm_undp_shp/Som_Admbnda_Adm2_UNDP.shp'
REGION = 'east-africa'
today = date.today()
COUNTRY = 'somalia'

regions = {'west-africa': 'WA', 'east-africa': 'EA'}

def return_max_cs(date, admin2, df, STATUS):
    sub = df.loc[(df['date']==date)&(df['admin2Name']==admin2)]
    mx = sub['area'].max()
    row = sub[['date', 'admin0Name', 'admin1Name', 'admin2Name', STATUS]].loc[sub['area']==mx]
    return row

def shapefiles_to_df():
    df = gpd.GeoDataFrame()
    shape = PATH + STATUS + '.shp'
    gdf = gpd.read_file(shape)
    df = df.append(gdf, ignore_index=True)
    print(df)
    return df

def merge_admin2(shape_df):
    admin2 = gpd.read_file(ADMIN2_SHP)
    overlap = gpd.overlay(admin2, shape_df, how='intersection')
    overlap = overlap.drop_duplicates()
    overlap['area'] = overlap['geometry'].area
    columns = ['admin0Name', 'admin1Name', 'admin2Name', 'date', STATUS, 'geometry', 'area']
    overlap = overlap[columns]
    print(overlap.columns)
    return overlap



def main():
    shape = shapefiles_to_df()
    overlap = merge_admin2(shape)
    new_df = pd.DataFrame(columns=['date', 'admin0Name', 'admin1Name', 'admin2Name', STATUS])
    for d in overlap['date'].unique():
        for a in overlap['admin2Name'].unique():
            row = return_max_cs(d, a, overlap, STATUS)
            new_df = new_df.append(row)
    new_df.to_csv(COUNTRY + '_admin2_fewsnet_' + STATUS + str(today) + '.csv')
    return new_df

if __name__=='__main__':
    main()