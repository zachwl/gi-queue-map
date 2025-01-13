import pandas as pd
import geopandas as gpd
import miso, pjm, isone, nyiso, soco, tva, duke

from utils import createJoinKey, sendEmail

def main():

    #### Download dataframes from all ISOs/utilties ####

    # Download a copy of each dataset (either new data or copied from backup)
    miso_queue = miso.getMISOQueue()
    pjm_queue = pjm.getPJMQueue()
    isone_queue = isone.getISONEQueue()
    nyiso_queue = nyiso.getNYISOQueue()
    soco_queue = soco.getSOCOQueue()
    tva_queue = tva.getTVAQueue()
    duke_queue = duke.getDukeQueue()

    #### Process the data ####

    # Concatenate the data to create long dataset
    all_queued_projects = pd.concat([
        miso_queue, 
        pjm_queue, 
        isone_queue, 
        nyiso_queue, 
        soco_queue,
        tva_queue,
        duke_queue])

    # Export as json for use in interactive web page elements
    all_queued_projects.reset_index().to_json(f'data/all_queued_projects.json', index = None, orient = 'records', indent = 2)

    # Aggregate based on county and fuel types
    # Returns metrics for each fuel type by county
    all_queued_projects_by_county = (
        all_queued_projects.groupby(["join_key", "fuel"])["capacity"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={
            "Solar": "total_solar",
            "Solar+Storage": "total_hybrid",
            "Storage": "total_storage",
            "Wind": "total_wind",
            "Natural Gas": "total_natural_gas",
            "Other": "total_other"
        })
        .reset_index()
    )

    #### Add additional data ###

    # Calculate total queued capacity for each county
    total_capacity = all_queued_projects.groupby("join_key")["capacity"].sum().rename("total_capacity")

    # Calculate the number of RTOs for each county
    rto_count = all_queued_projects.groupby("join_key")["iso_utility"].nunique().rename("rto_count")

    # Merge additional metrics into the aggregated DataFrame
    all_queued_projects_by_county = all_queued_projects_by_county.merge(total_capacity, on="join_key").merge(rto_count, on="join_key").copy()

    #### Spatializing Queue Data ####

    # Read in pre-cleaned spatial layer of US counties and give it a join_key
    counties = gpd.read_file(f'data/simplified_counties.geojson')
    counties = createJoinKey(counties)

    # Merge county spatial with aggregate county data using join_key
    joined_data = all_queued_projects_by_county.merge(counties, on = 'join_key', how='outer')

    # Add back geometry
    spatialized_data = gpd.GeoDataFrame(joined_data, geometry=joined_data['geometry'])

    # Sort by rto_count to help with rendering in the web page
    spatialized_data.fillna(value = {'rto_count': 0}, inplace=True)
    spatialized_data.sort_values('rto_count', ascending=True, inplace=True)

    # Export as geojson for use in script.js
    spatialized_data.to_file(f'data/agg_county_data.geojson', driver = 'GeoJSON')
    sendEmail("GI Queue Map", "Execution of main.py successful")

if __name__ == "__main__":
    main()
