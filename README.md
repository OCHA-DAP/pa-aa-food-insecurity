# pa-aa-pilots

Drought-related food insecurity in Chad, Somalia, Ethiopia and Malawi. 

## Getting started


### Computation for existing country
FewsNet
1. Run `convert_fewsnet_to_admin2.py` giving the country iso3 as arg
2. Run `fewsnet_combined.py` giving the country iso3 as arg

3. Do your analysis. The jupyter notebooks in `ethiopia/` can guide as examples

### Adding a new country
FewsNet
1. Make sure the regional FewsNet data is included in Data/FewsNetRaw. Can be downloaded from https://fews.net/fews-data/333
2. Download a shapefile of the regional boundaries and place this directory/file in "country_name" -- "Data" . Can for example use the one provided by UN OCHA (search on data.humdata.org) or FewsNet (https://fews.net/fews-data/334)  
3. Download regional population data for one year. Often available by UN OCHA on data.humdata.org
4. Add the country-specific variables to `config.yml`
GlobalIPC
1. Download data from http://www.ipcinfo.org/ipc-country-analysis/population-tracking-tool/en/
2. Change column names to be compatible with the ipynb notebooks. An example can be found in `ethiopia/Data/GlobalIPC_newcolumnnames.xlsx`

## Ethiopia
Required data
- IPC factors (current and predictions). Using historical data from 2009. Can be downloaded from https://fews.net/fews-data/333
- Admin2 boundaries: Use UN population boundaries https://data.humdata.org/dataset/ethiopia-cod-ab# or FewsNet boundaries https://fews.net/fews-data/334?tid=26
- Current population. Given the name, it seems it is downloaded from https://data.humdata.org/dataset/ethiopia-population-data-_-admin-level-0-3 . 
- Historical population. For now using country totals, can be retrieved from https://data.worldbank.org/indicator/SP.POP.TOTL?locations=ET More detailed data exists at https://www.worldpop.org/project/categories?id=3


## Development
### How to setup code for development?
After cloning the repo, run `pre-commit install` to enable format checking when committing changes.