import traceback
import requests
from io import BytesIO
import pandas as pd

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getNYISOQueue():

    try:
        x=1/0
        url = 'https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx'

        #Send a GET request to fetch the content
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
        nyiso_active_projects = nyiso_active_projects[~nyiso_active_projects['Type/ Fuel'].isin(['AC', 'DC', 'L'])].copy()
        #Could be turned into a function in utils in the future
        nyiso_active_projects['County'] = nyiso_active_projects['County'].str.replace(r' (County|Parish)$', '', regex=True)

        nyiso_active_projects['County'] = nyiso_active_projects['County'].str.split('/').str[0]
        nyiso_active_projects['County'] = nyiso_active_projects['County'].str.split(',').str[0]

        #nyiso_cols_to_keep = ['Queue Pos.', 'Project Name', 'Date of IR', 'SP (MW)', 'Type/ Fuel', 'County', 'State', 'Utility', 'Proposed COD']
        nyiso_relevant_fields = ['Queue Pos.', 'Project Name', 'SP (MW)', 'Type/ Fuel', 'Date of IR', 'Proposed COD', 'County', 'State', 'Utility']

        nyiso_active_projects = standardizeFields(nyiso_active_projects, nyiso_relevant_fields)

        solar_indices = (nyiso_active_projects['fuel'] == 'S')
        storage_indices = (nyiso_active_projects['fuel'] == 'ES')
        ss_indices = (nyiso_active_projects['fuel'] == 'CR')
        wind_indices = ((nyiso_active_projects['fuel'] == 'W') | (nyiso_active_projects['fuel'] == 'OSW'))
        gas_indices = (nyiso_active_projects['fuel'] == 'NG')

        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]

        nyiso_active_projects = standardizeFuels(nyiso_active_projects, indices_list)

        nyiso_active_projects['iso_utility'] = 'NYISO'
        nyiso_active_projects = createJoinKey(nyiso_active_projects)

        nyiso_active_projects.to_csv(f'data/individual_queues/nyiso_active_projects.csv', index = False)

        return nyiso_active_projects
    except Exception as e:
        error = traceback.format_exc()
        sendEmail('Error raised in pjm.py', error)
        nyiso_backup = pd.read_csv('data/individual_queues/nyiso_active_projects.csv')
        return nyiso_backup

#getNYISOQueue().to_csv('C:/Users/zleig/Downloads/tempNYISO.csv', index = False)
