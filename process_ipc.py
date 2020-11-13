import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

from utils import parse_args, parse_yaml, config_logger

logger = logging.getLogger(__name__)


def read_ipcglobal(parameters, ipc_path, shp_path):
    """
    Process ipc data and do some checks
    Args:
        parameters: dict with parameters parsed from config
        ipc_path: path to ipc data
        shp_path: path to shapefile

    Returns:
        df_ipc: DataFrame with processed ipc data
    """

    admin_level = parameters["admin_level"]
    # TODO: now assuming column names are already changed in the excel file. Might want to add something to change them automatically but fileformat is rather hard
    # seems ipc file columns are always on line 11
    df_ipc = pd.read_excel(ipc_path, header=[11])
    # remove rows with nan date
    df_ipc = df_ipc[df_ipc["date"].notnull()]

    # replace values in ipc df
    # mainly about differently spelled admin regions
    if "replace_dict" in parameters:
        replace_dict = parameters["replace_dict"]
        df_ipc = df_ipc.replace(replace_dict)

    if len(df_ipc[f"ADMIN{admin_level}"].dropna().unique()) == 0:
        logger.warning(f"No admin {admin_level} regions found in the IPC file")

    shp_admc = parameters[f"shp_adm{admin_level}c"]
    boundaries = gpd.read_file(shp_path)

    # Check that admin level names in the IPC data are all reasonable
    misspelled_names = np.setdiff1d(
        list(df_ipc[f"ADMIN{admin_level}"].dropna()),
        list(boundaries[shp_admc].dropna()),
    )
    if misspelled_names.size > 0:
        logger.warning(
            f"The following admin {admin_level} regions from the IPC file are not found "
            f"in the boundaries file: {misspelled_names}"
        )

    return df_ipc


def main(country_iso3, config_file="config.yml"):
    """
    Define variables and save output
    Args:
        country_iso3: string with iso3 code
        config_file: path to config file
    """
    parameters = parse_yaml(config_file)[country_iso3]
    country = parameters["country_name"]
    admin2_shp = parameters["path_admin2_shp"]
    globalipc_file = parameters["ipc_path"]

    SHP_PATH = f"{country}/Data/{admin2_shp}"
    IPC_PATH = f"{country}/Data/{globalipc_file}"
    RESULT_FOLDER = f"{country}/Data/GlobalIPCProcessed/"
    # create output dir if it doesn't exist yet
    Path(RESULT_FOLDER).mkdir(parents=True, exist_ok=True)

    df_ipc = read_ipcglobal(parameters, IPC_PATH, SHP_PATH)
    df_ipc.to_csv(f"{RESULT_FOLDER}{country}_globalipc_processed.csv")


if __name__ == "__main__":
    args = parse_args()
    config_logger(level="warning")
    main(args.country_iso3.upper())
