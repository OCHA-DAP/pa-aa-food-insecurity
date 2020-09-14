# pa-aa-pilots

Drought-related food insecurity in Chad, Somalia and Ethiopia. 


## Ethiopia
Required data
- IPC factors (current and predictions). Using historical data from 2009. Can be downloaded from https://fews.net/fews-data/333
- Admin2 boundaries: Use UN population boundaries https://data.humdata.org/dataset/ethiopia-cod-ab# or FewsNet boundaries https://fews.net/fews-data/334?tid=26
- Current population. Given the name, it seems it is downloaded from https://data.humdata.org/dataset/ethiopia-population-data-_-admin-level-0-3 . 
- Historical population. For now using country totals, can be retrieved from https://data.worldbank.org/indicator/SP.POP.TOTL?locations=ET More detailed data exists at https://www.worldpop.org/project/categories?id=3
- Livelihood zones. Download from https://fews.net/fews-data/335


## Development
### How to setup code for development?
After cloning the repo, run `pre-commit install` to enable format checking when committing changes.