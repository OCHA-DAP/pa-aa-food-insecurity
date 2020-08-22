#import

import geopandas as gpd
import pandas as pd
from datetime import date

DATES = ['200907','200910','201001','201004','201007','201010','201101', '201104', '201107', '201110',
       '201201', '201204', '201207', '201210', '201301', '201304', '201307', '201310', '201401', '201404', '201407',
       '201410', '201501', '201504', '201507', '201510', '201602', '201606','201610',
       '201706', '201710', '201802', '201806', '201810', '201812','201902', '201906', '201910']

PATH = '../../FEWSNET/East Africa/EA_proj/'
STATUS = 'ML2' # choice of CS, ML1, ML2
ADMIN2_SHP = 'ET_Admin2_2014/ET_Admin2_2014.shp'
REGION = 'east-africa'
today = date.today()
COUNTRY = 'ethiopia'

regions = {'west-africa': 'WA', 'east-africa': 'EA'}

def return_max_cs(date, admin2, df, STATUS):
    sub = df.loc[(df['date']==date)&(df['ADMIN2']==admin2)]
    mx = sub['area'].max()
    row = sub[['date', 'ADMIN0', 'ADMIN1', 'ADMIN2', STATUS]].loc[sub['area']==mx]
    return row

def shapefiles_to_df():
    df = gpd.GeoDataFrame()
    for d in DATES:
        shape = PATH+REGION + d + '/'+regions[REGION] +'_'+ d + '_' + STATUS +'.shp'
        gdf = gpd.read_file(shape)
        gdf['date'] = pd.to_datetime(d, format='%Y%m')
        df = df.append(gdf, ignore_index=True)
    return df

def merge_admin2(shape_df):
    admin2 = gpd.read_file(ADMIN2_SHP)
    overlap = gpd.overlay(admin2, shape_df, how='intersection')
    overlap = overlap.drop_duplicates()
    overlap['area'] = overlap['geometry'].area
    columns = ['ADMIN0', 'ADMIN1', 'ADMIN2', 'date', STATUS, 'geometry', 'area']
    overlap = overlap[columns]
    return overlap



def main():
    shape = shapefiles_to_df()
    overlap = merge_admin2(shape)
    new_df = pd.DataFrame(columns=['date', 'ADMIN0', 'ADMIN1', 'ADMIN2', STATUS])
    for d in overlap['date'].unique():
        for a in overlap['ADMIN2'].unique():
            row = return_max_cs(d, a, overlap, STATUS)
            new_df = new_df.append(row)
    new_df.to_csv(COUNTRY + '_admin2_fewsnet_' + STATUS + str(today) + '.csv')
    return new_df

if __name__=='__main__':
    main()