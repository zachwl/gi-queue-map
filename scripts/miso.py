import os
import requests
import pandas as pd
from config import fuel_indicies, standard_fields
from utils import standardizeFuels, standardizeFields

def getMISOQueue():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    #Request the data from the MISO API
    miso_url = 'https://www.misoenergy.org/api/giqueue/getprojects'
    response = requests.get(miso_url)
    raw_data = response.json()
    miso_df = pd.DataFrame(raw_data)

    #Clean the existing columns
    miso_active_projects = miso_df[miso_df['applicationStatus'] == 'Active'].copy()
    miso_active_projects['county'] = miso_active_projects['county'].str.replace(r' (County|Parish)$', '', regex=True)
    miso_active_projects['county'] = miso_active_projects['county'].str.split(',').str[0]

    #miso_active_projects['summerNetMW'] = pd.to_numeric(miso_active_projects['summerNetMW'], errors='coerce')
    #miso_active_projects['summerNetMW'] = pd.to_numeric(miso_active_projects['summerNetMW'], errors='coerce')
    #standard_fields = ['id', 'name', 'capacity', 'fuel', 'submitted_date', 'service_date', 'county', 'state', 'transmission_owner']

    miso_relevant_fields = ['projectNumber', 'poiName', 'summerNetMW', 'fuelType', 'queueDate', 'inService', 'county', 'state', 'transmissionOwner']


    miso_active_projects = standardizeFields(miso_active_projects, standard_fields, miso_relevant_fields)

    #########
    # Standardize Fuel Types
    #########
    #Get all relevant indicies
    #Access methods for these will vary by RTO/utility

    fuel_indicies['Solar'] = (miso_active_projects['fuel'] == 'Solar')
    fuel_indicies['Storage'] = (miso_active_projects['fuel'] == 'Battery Storage')
    fuel_indicies['Solar/Storage'] = (miso_active_projects['fuel'] == 'Hybrid') # Will need to add more logic to this to improve accuracy
    fuel_indicies['Wind'] = (miso_active_projects['fuel'] == 'Wind')
    fuel_indicies['Natural Gas'] = (miso_active_projects['fuel'] == 'Gas')
    
    ####Could be a function in utils in the future
    fuel_indicies['Other'] = ~(fuel_indicies['Solar'] | fuel_indicies['Storage'] | fuel_indicies['Solar/Storage'] | fuel_indicies['Wind'] | fuel_indicies['Natural Gas'])

    #Standardize the fuel types
    miso_active_projects = standardizeFuels(miso_active_projects, fuel_indicies)

    miso_active_projects['iso_utility'] = 'MISO'

    ####Could be a function in utils in the future
    miso_active_projects['join_key'] = (miso_active_projects['county'] + '_' + miso_active_projects['state']).str.lower()

    miso_active_projects.to_csv(f'../data/individual_queues/miso_active_projects.csv', index = False)

    return miso_active_projects