import traceback
import requests
from io import BytesIO
import pandas as pd

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getNYISOQueue():

    # Check for errors during code execution
    # If anything changes with the access link, or some other scenario,
    # The script will instead use backup data to send to main.py
    try:
        #### Import Data from NYISO ####

        # Link to excel file with active queued projects
        # This acts as a permanent link
        url = 'https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx'
        response = requests.get(url)
        excel_file = BytesIO(response.content)
        # The active projects are in the first sheet
        # Gets read by default
        nyiso_active_projects = pd.read_excel(excel_file, engine='openpyxl')

        #### Clean the existing columns ####

        # Remove extra rows in the dataframe that were in the excel file to provide padding
        # Any row that has no queue position value will drop out.
        nyiso_active_projects = nyiso_active_projects[pd.to_numeric(nyiso_active_projects['Queue Pos.'], errors='coerce').notna()].copy()
        # Remove all projects that are not generation interconnection
        nyiso_active_projects = nyiso_active_projects[~nyiso_active_projects['Type/ Fuel'].isin(['AC', 'DC', 'L'])].copy()
        # Remove any stray instances of the word "County" in order to clean the county column
        # Might turn this into a function in the future
        nyiso_active_projects['County'] = nyiso_active_projects['County'].str.replace(r' (County|Parish)$', '', regex=True)
        # If two or more counties are listed, then only use the first one
        # This system is not perfect, so in the future, I might add a way to split that projects generation evenly across all counties it is located in
        nyiso_active_projects['County'] = nyiso_active_projects['County'].str.split('/').str[0]
        nyiso_active_projects['County'] = nyiso_active_projects['County'].str.split(',').str[0]
        # Clean up the queue date column by removing the unneccessary time
        nyiso_active_projects['Date of IR'] = nyiso_active_projects['Date of IR'].astype(str).str[:10]

        #### Standardize Columns ####

        # These are the 9 columns that I want to keep from the NYISO data
        nyiso_relevant_fields = ['Queue Pos.', 
                                'Project Name', 
                                'SP (MW)', 
                                'Type/ Fuel', 
                                'Date of IR', 
                                'Proposed COD', 
                                'County', 
                                'State', 
                                'Utility']
        # This function filters down the active sites dataset to the 9 specific fields
        # Then, it renames the columns to standardized ones defined in config.py
        # The columns get sorted in the process
        nyiso_active_projects = standardizeFields(nyiso_active_projects, nyiso_relevant_fields)
        
        #### Standardize Fuel Types ####

        # Find indices for the most common fuel types
        solar_indices = (nyiso_active_projects['fuel'] == 'S')
        storage_indices = (nyiso_active_projects['fuel'] == 'ES')
        ss_indices = (nyiso_active_projects['fuel'] == 'CR')
        wind_indices = ((nyiso_active_projects['fuel'] == 'W') | (nyiso_active_projects['fuel'] == 'OSW'))
        gas_indices = (nyiso_active_projects['fuel'] == 'NG')
        
        # Find indices for less common fuels that do not match the predefined set of fuel types
        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
        # Create list object for these indicies
        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]
        
        # This function standardizes the fuel types 
        # This is necessary so we can aggregate all of the dataframe from every ISO/utility
        nyiso_active_projects = standardizeFuels(nyiso_active_projects, indices_list)
        
        #### Final Steps ####

        # Create new column to highlight which RTO/utility this data came from
        nyiso_active_projects['iso_utility'] = 'NYISO'
        # Create a common key from county name and state abbr
        # This will allow the data to be joined to spatial layer later
        nyiso_active_projects = createJoinKey(nyiso_active_projects)
        # Export to CSV
        # This will act as a "backup" in case the next run fails
        nyiso_active_projects.to_csv(f'data/individual_queues/nyiso_active_projects.csv', index = False)

        return nyiso_active_projects
    
    # If the above code throws an error, fetch the backup data and return that instead
    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in nyiso.py', error)
        nyiso_backup = pd.read_csv('data/individual_queues/nyiso_active_projects.csv')
        return nyiso_backup
