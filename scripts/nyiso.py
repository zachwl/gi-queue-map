import os
import requests
from io import BytesIO
import pandas as pd

from config import fuel_indicies, standard_fields
from utils import standardizeFuels, standardizeFields

def getNYISOQueue():

    url = 'https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx'

#    Send a GET request to fetch the content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
    # Load the Excel content into a DataFrame
        excel_file = BytesIO(response.content)
        nyiso_active_projects = pd.read_excel(excel_file, engine='openpyxl')
    else:
        print(f"Failed to fetch the file. Status code: {response.status_code}")

    ### Clean Data ###

    nyiso_active_projects = nyiso_active_projects[pd.to_numeric(nyiso_active_projects['Queue Pos.'], errors='coerce').notna()].copy()
    nyiso_active_projects = nyiso_active_projects[~nyiso_active_projects['Type/ Fuel'].isin(['AC', 'DC','L'])].copy()
    nyiso_active_projects['County'] = nyiso_active_projects['County'].str.replace(r' (County|Parish)$', '', regex=True)
    nyiso_active_projects['County'] = nyiso_active_projects['County'].str.replace('St-Lawrence', 'St. Lawrence', regex=True)

    nyiso_active_projects['County'] = nyiso_active_projects['County'].str.split('/').str[0]
    nyiso_active_projects['County'] = nyiso_active_projects['County'].str.split(',').str[0]

    #nyiso_cols_to_keep = ['Queue Pos.', 'Project Name', 'Date of IR', 'SP (MW)', 'Type/ Fuel', 'County', 'State', 'Utility', 'Proposed COD']
    nyiso_relevant_fields = ['Queue Pos.', 'Project Name', 'SP (MW)', 'Type/ Fuel', 'Date of IR', 'Proposed COD', 'County', 'State', 'Utility']

    nyiso_active_projects = standardizeFields(nyiso_active_projects, standard_fields, nyiso_relevant_fields)

    fuel_indicies['Solar'] = (nyiso_active_projects['fuel'] == 'S')
    fuel_indicies['Solar/Storage'] = (nyiso_active_projects['fuel'] == 'CR')
    fuel_indicies['Storage'] = (nyiso_active_projects['fuel'] == 'ES')
    fuel_indicies['Wind'] = ((nyiso_active_projects['fuel'] == 'W') | (nyiso_active_projects['fuel'] == 'OSW'))
    fuel_indicies['Natural Gas'] = (nyiso_active_projects['fuel'] == 'NG')

    fuel_indicies['Other'] = ~(fuel_indicies['Solar'] | fuel_indicies['Storage'] | fuel_indicies['Solar/Storage'] | fuel_indicies['Wind'] | fuel_indicies['Natural Gas'])

    nyiso_active_projects = standardizeFuels(nyiso_active_projects, fuel_indicies)

    nyiso_active_projects['iso_utility'] = 'NYISO'
    nyiso_active_projects['join_key'] = (nyiso_active_projects['county'] + '_' + nyiso_active_projects['state']).str.lower()

    nyiso_active_projects.to_csv(f'data/individual_queues/nyiso_active_projects.csv', index = False)

    return nyiso_active_projects

#getNYISOQueue().to_csv('C:/Users/zleig/Downloads/nyiso_testing.csv', index = False)