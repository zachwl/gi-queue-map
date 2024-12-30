import requests

import pandas as pd
import geopandas as gpd
import fiona

from modules import miso
from modules.tools import config
import modules.tools.utils

def main():

    #Get the MISO Queue
    miso_queue = miso.getMISOQueue()

    all_queued_projects = pd.concat([miso_queue])

    all_queued_projects_by_county = (
        all_queued_projects.groupby(["join_key", "Fuel"])["Nameplate Capacity"]
        .sum()
        .unstack(fill_value=0)  # Transform fuel_type into columns
        .rename(columns={
            "Solar": "total_solar",
            "Solar/Storage": "total_hybrid",
            "Storage": "total_storage",
            "Wind": "total_wind",
            "Natural Gas": "total_natural_gas",
            "Other": "total_other"
        })
        .reset_index()  # Reset index for a clean DataFrame
    )
    # Calculate total nameplate capacity for each county
    total_capacity = all_queued_projects.groupby("join_key")["capacity"].sum().rename("total_capacity")

    # Calculate the number of RTOs for each county
    rto_count = all_queued_projects.groupby("join_key")["iso_utility"].nunique().rename("rto_count")

    # Merge additional metrics into the aggregated DataFrame
    all_queued_projects_by_county = all_queued_projects_by_county.merge(total_capacity, on="join_key").merge(rto_count, on="join_key").copy()

    all_queued_projects_by_county.to_csv('countyAggTest.csv', index = None)

    print('AllDone')
if __name__ == "__main__":
    main()