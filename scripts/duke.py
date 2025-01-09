import requests
import traceback
import pandas as pd
from io import BytesIO

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail, findNewURL

#### Function to import data ####

# Since both DEP and DEC publich their reports with the same formatting,
# it is better to create one function to import both of them at the same time
def importDuke(url):
    response = requests.get(url)
    excel_file = BytesIO(response.content)
    # The active projects are in the first sheet
    # Gets read by default
    duke_df = pd.read_excel(excel_file, engine='openpyxl')
    # Find header row
    # Necessary because the headers are slightly different between DEP and DEC
    header_row_index = duke_df[duke_df.iloc[:, 1] == "OPCO"].index[0]

    # Set that row as the header
    df_cleaned = duke_df.iloc[header_row_index + 1:-2].reset_index(drop=True)  # Rows below the header row
    df_cleaned.columns = duke_df.iloc[header_row_index]  # Set the column names
    return df_cleaned

def getDukeQueue():

    # Check for errors during code execution
        # If anything changes with the access link, or some other scenario,
        # The script will instead use backup data to send to main.py
    try:
        #### Check if data needs to be updated ####
        dep_url = findNewURL('DEP')
        dec_url = findNewURL('DEC')

        if (dep_url is None) or (dec_url is None):
            duke_backup = pd.read_csv('data/individual_queues/duke_active_projects.csv')
            return duke_backup
        else:
            dep_df = importDuke(dep_url)
            dec_df = importDuke(dec_url)

            duke_df = pd.concat([dec_df, dep_df])

            ### Begin clean up ###
            duke_active_projects = duke_df[~duke_df['Operational Status'].isin(["Withdrawn", "Commercial Operation - Commercial Operation Date Declared"])].copy()
            duke_active_projects['POI'] = duke_active_projects['Transmission Line'].astype(str) + duke_active_projects['Substation Name'].astype(str)

            duke_relevant_fields = [
                'Source System Unique ID',
                'POI',
                'Installed Capacity MW AC',
                'Energy Source Type',
                'Queue Issued Date',
                'Duke Estimated Startup Date',
                'Facility County',
                'Facility State',
                'OPCO'
            ]
            duke_active_projects = standardizeFields(duke_active_projects, duke_relevant_fields)

            solar_indices = (duke_active_projects['fuel'] == 'Solar')
            storage_indices = (duke_active_projects['fuel'] == 'Battery')
            ss_indices = (duke_active_projects['fuel'] == 'Solar+Storage')
            wind_indices = (duke_active_projects['fuel'] == 'Wind')
            gas_indices = (duke_active_projects['fuel'] == 'Natural Gas')

            # Find indices for less common fuels that do not match the predefined set of fuel types
            other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
            # Create list object for these indicies
            indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]

            duke_active_projects = standardizeFuels(duke_active_projects, indices_list)
            
            #### Final Steps ####

            # Create new column to highlight which RTO/utility this data came from
            duke_active_projects['iso_utility'] = duke_active_projects['transmission_owner']
            # Create a common key from county name and state abbr
            # This will allow the data to be joined to spatial layer later
            duke_active_projects = createJoinKey(duke_active_projects)
            # Export to CSV
            # This will act as a "backup" in case the next run fails
            duke_active_projects.to_csv(f'data/individual_queues/duke_active_projects.csv', index = False)
            return duke_active_projects
    except:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in duke.py', error)
        duke_backup = pd.read_csv('data/individual_queues/duke_active_projects.csv')
        return duke_backup

#getDukeQueue().to_csv('C:/Users/zleig/Downloads/duketemp.csv', index = False)