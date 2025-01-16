import traceback
import requests
import pandas as pd

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getMISOQueue():
    # Check for errors during code execution
    # If anything changes with the access link, or some other scenario,
    # The script will instead use backup data to send to main.py
    try:
        #### Request the data from the MISO API ####

        miso_url = 'https://www.misoenergy.org/api/giqueue/getprojects'
        response = requests.get(miso_url)
        raw_data = response.json()
        miso_df = pd.DataFrame(raw_data)

        #### Clean the existing columns ####

        # Filter only "Active Projects"
        miso_active_projects = miso_df[miso_df['applicationStatus'] == 'Active'].copy()
        # Filter out transmission buildouts/upgrades
        # These do not count as generation interconnection
        miso_active_projects = miso_active_projects[miso_active_projects['fuelType'] != 'High Voltage DC'].copy()
        # Remove any stray instances of the word "County" or "Parish" in order to clean the county column
        miso_active_projects['county'] = miso_active_projects['county'].str.replace(r' (County|Parish)$', '', regex=True)
        # If two or more counties are listed, then only use the first one
        # This system is not perfect, so in the future, I might add a way to split that projects generation evenly across all counties it is located in
        miso_active_projects['county'] = miso_active_projects['county'].str.split(',').str[0]
        # Remove unnecessary time from date
        miso_active_projects['queueDate'] = miso_active_projects['queueDate'].str[:10]
        miso_active_projects['inService'] = miso_active_projects['inService'].str[:10]

        #### Standardize column names ####

        # These are the 9 columns that I want to keep from the MISO data
        miso_relevant_fields = ['projectNumber',
                                'poiName', 
                                'summerNetMW', 
                                'fuelType', 
                                'queueDate', 
                                'inService', 
                                'county', 
                                'state', 
                                'transmissionOwner']
        # This function filters down the MISO dataset to the 9 specific fields
        # Then, it renames the columns to standardized ones defined in config.py
        # The columns get sorted in the process
        miso_active_projects = standardizeFields(miso_active_projects, miso_relevant_fields)

        #### Standardize Fuel Types ####

        # Find indices for the most common fuel types
        solar_indices = (miso_active_projects['fuel'] == 'Solar')
        storage_indices = (miso_active_projects['fuel'] == 'Battery Storage')
        ss_indices = (miso_active_projects['fuel'] == 'Hybrid') # Will need to add more logic to this to improve accuracy
        wind_indices = (miso_active_projects['fuel'] == 'Wind')
        gas_indices = (miso_active_projects['fuel'] == 'Gas')
        
        # Find indices for less common fuels that do not match the predefined set of fuel types
        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
        # Create list object for these indicies
        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]

        # This function standardizes the fuel types 
        # This is necessary so we can aggregate all of the dataframe from every ISO/utility
        miso_active_projects = standardizeFuels(miso_active_projects, indices_list)

        #### Final Steps ####

        # Create new column to highlight which RTO/utility this data came from
        miso_active_projects['iso_utility'] = 'MISO'
        # Create a common key from county name and state abbr
        # This will allow the data to be joined to spatial layer later
        miso_active_projects = createJoinKey(miso_active_projects)
        # Export to CSV
        # This will act as a "backup" in case the next run fails
        miso_active_projects.to_csv(f'data/individual_queues/miso_active_projects.csv', index = False)

        return miso_active_projects
    
    # If the above code throws an error, fetch the backup data and return that instead
    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in miso.py', error)
        miso_backup = pd.read_csv('data/individual_queues/miso_active_projects.csv')
        return miso_backup

#getMISOQueue().to_csv('C:/Users/zleig/Downloads/misotest.csv', index = False)
