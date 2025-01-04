import traceback
import requests
import pandas as pd

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getMISOQueue():
    try:
        x=1/0
        #Request the data from the MISO API
        miso_url = 'https://www.misoenergy.org/api/giqueue/getprojects'
        response = requests.get(miso_url)
        raw_data = response.json()
        miso_df = pd.DataFrame(raw_data)

        #Clean the existing columns
        miso_active_projects = miso_df[miso_df['applicationStatus'] == 'Active'].copy()
        miso_active_projects = miso_active_projects[miso_active_projects['fuelType'] != 'High Voltage DC'].copy()
        
        miso_active_projects['county'] = miso_active_projects['county'].str.replace(r' (County|Parish)$', '', regex=True)
        miso_active_projects['county'] = miso_active_projects['county'].str.split(',').str[0]

        #miso_active_projects['summerNetMW'] = pd.to_numeric(miso_active_projects['summerNetMW'], errors='coerce')
        #miso_active_projects['summerNetMW'] = pd.to_numeric(miso_active_projects['summerNetMW'], errors='coerce')
        #standard_fields = ['id', 'name', 'capacity', 'fuel', 'submitted_date', 'service_date', 'county', 'state', 'transmission_owner']

        miso_relevant_fields = ['projectNumber', 'poiName', 'summerNetMW', 'fuelType', 'queueDate', 'inService', 'county', 'state', 'transmissionOwner']


        miso_active_projects = standardizeFields(miso_active_projects, miso_relevant_fields)

        #########
        # Standardize Fuel Types
        #########
        #Get all relevant indicies
        #Access methods for these will vary by RTO/utility

        solar_indices = (miso_active_projects['fuel'] == 'Solar')
        storage_indices = (miso_active_projects['fuel'] == 'Battery Storage')
        ss_indices = (miso_active_projects['fuel'] == 'Hybrid') # Will need to add more logic to this to improve accuracy
        wind_indices = (miso_active_projects['fuel'] == 'Wind')
        gas_indices = (miso_active_projects['fuel'] == 'Gas')
        
        #Find indices that do not match the predefined set of fuel types
        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)

        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]

        #Standardize the fuel types
        miso_active_projects = standardizeFuels(miso_active_projects, indices_list)

        miso_active_projects['iso_utility'] = 'MISO'

        ####Could be a function in utils in the future
        #miso_active_projects['join_key'] = (miso_active_projects['county'] + '_' + miso_active_projects['state']).str.lower()
        miso_active_projects = createJoinKey(miso_active_projects)
        miso_active_projects.to_csv(f'data/individual_queues/miso_active_projects.csv', index = False)

        return miso_active_projects
    
    except Exception as e:
        error = traceback.format_exc()
        sendEmail('Error raised in miso.py', error)
        miso_backup = pd.read_csv('data/individual_queues/miso_active_projects.csv')
        return miso_backup
#getMISOQueue().to_csv('C:/Users/zleig/Downloads/tempMISO.csv', index=False)
