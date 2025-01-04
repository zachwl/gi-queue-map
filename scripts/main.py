import pandas as pd
import geopandas as gpd
import miso, pjm, isone, nyiso

from utils import createJoinKey, sendEmail

def main():

    #script_dir = os.path.dirname(os.path.abspath(__file__))
    #os.chdir(script_dir)

    #Get the MISO Queue
    miso_queue = miso.getMISOQueue()
    pjm_queue = pjm.getPJMQueue()
    isone_queue = isone.getISONEQueue()
    nyiso_queue = nyiso.getNYISOQueue()

    all_queued_projects = pd.concat([miso_queue, pjm_queue, isone_queue, nyiso_queue])

    all_queued_projects.reset_index().to_json(f'data/all_queued_projects.json', index = None)

    all_queued_projects_by_county = (
        all_queued_projects.groupby(["join_key", "fuel"])["capacity"]
        .sum()
        .unstack(fill_value=0)  # Transform fuel_type into columns
        .rename(columns={
            "Solar": "total_solar",
            "Solar+Storage": "total_hybrid",
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

    #all_queued_projects_by_county.to_csv(f'C:/Users/zleig/Downloads/countyAggtest.csv', index = None)

    ###############################
    ### Spatializing Queue Data ###
    ###############################

    counties = gpd.read_file(f'data/simplified_counties.geojson')
    counties = createJoinKey(counties)

    joined_data = all_queued_projects_by_county.merge(counties, on = 'join_key', how='outer')

    spatialized_data = gpd.GeoDataFrame(joined_data, geometry=joined_data['geometry'])

    spatialized_data.fillna(value = {'rto_count': 0}, inplace=True)
    spatialized_data.sort_values('rto_count', ascending=True, inplace=True)

    #joined_data_geo.to_file('sampleisoneData.gpkg', driver='GPKG')
    spatialized_data.to_file(f'data/agg_county_data.geojson', driver = 'GeoJSON')
    sendEmail("Live from New York", "It's Saturday Night!")

if __name__ == "__main__":
    main()
