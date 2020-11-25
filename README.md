# pa-aa-pilots

Drought-related food insecurity in Chad, Somalia, Ethiopia and Malawi. 

## Getting started
If using Anaconda, set-up an environment and install the packages from `environment.yml`. 
   ``` bash
   conda env create --file environment.yml --name aafi
   conda activate aafi
   ```
Else install the requirements with 
   ``` bash
   pip install -r requirements.txt
   ```
If an error occurs you might have to install spatialindex, with brew `brew install spatialindex`

### Computation for existing country
1. Run `process_fewsnet.py [Country ISO code]` this will return two csv's with the IPC phases of the FewsNet data for  for the current situation (CS), projections up to four months ahead (ML1) and projections up to 8 months ahead (ML2). One IPC phase is assigned per admin2 together with the population, per admin1 the population per IPC phase is returned, based on the admin2 results.  
2. Run `process_globalipc.py [Country ISO code]` this will return two csv's with the IPC phases of the GlobalIPC data per admin2 and admin1. For each spatial level the population per IPC phase is returned. 
3. Run `IPC_computetrigger.py[Country ISO code]` this will return a csv with processed columns, including if defined triggers are met. The FewsNet and GlobalIPC data are combined in this script, if they are both present
3. Do further analysis. The jupyter notebooks in `ethiopia/` can guide as examples

### Adding a new country
##### General
1. Download the shapefiles of the country, one on admin2 and one on admin1 level. Place the files in `country_name/Data` and set the specific path in the `config.yml`. Generally shapefiles can be found on the [Humanitarian Data Exchange](data.humdata.org)) or [FewsNet](https://fews.net/fews-data/334)  
2. Download regional population data for one year and place it in `country_name/Data`. Often available by UN OCHA on the [Humanitarian Data Exchange](data.humdata.org)
3. Add the country-specific variables to `config.yml`
##### FewsNet
1. Download [all FewsNet IPC classifications](https://fews.net/fews-data/333) that covers the country of interest and place it in `Data/FewsNetRaw`. Check if FewsNet publishes regional classifications that include your country of interest and/or country specific classifications. Both should be included and will be automatically masked to the country shapefile by the code.
##### GlobalIPC
1. Download the excel with country IPC classifications from [the IPC Global tracking tool](http://www.ipcinfo.org/ipc-country-analysis/population-tracking-tool/en/) and save it to `country_name/Data`.
2. Change column names to be compatible with `process_globalipc.py`. An example can be found in `ethiopia/Data/GlobalIPC_newcolumnnames.xlsx`

<!---
## Ethiopia
Required data
- IPC factors (current and predictions). Using historical data from 2009. Can be downloaded from https://fews.net/fews-data/333
- Admin2 boundaries: Use UN population boundaries https://data.humdata.org/dataset/ethiopia-cod-ab# or FewsNet boundaries https://fews.net/fews-data/334?tid=26
- Current population. Given the name, it seems it is downloaded from https://data.humdata.org/dataset/ethiopia-population-data-_-admin-level-0-3 . 
- Historical population. For now using country totals, can be retrieved from https://data.worldbank.org/indicator/SP.POP.TOTL?locations=ET More detailed data exists at https://www.worldpop.org/project/categories?id=3
 - Livelihood zones. Download from https://fews.net/fews-data/335 --->


## Development
### How to setup code for development?
After cloning the repo, run `pre-commit install` to enable format checking when committing changes.