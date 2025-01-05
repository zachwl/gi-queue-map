import traceback
import xml.etree.ElementTree as ET
import requests
import pandas as pd

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getPJMQueue():

    # Check for errors during code execution
    # If anything changes with the access link, or some other scenario,
    # The script will instead use backup data to send to main.py
    try:
        #### Import data from PJM ####

        # Link to PJM New Services queue
        url = 'https://www.pjm.com/pub/planning/downloads/xml/PlanningQueues.xml'
        response = requests.get(url)
        xml_content = response.content
        # Extract XML content
        root = ET.fromstring(xml_content)
        data = []
        for project in root.findall(".//Project"):
            project_data = {}
            for child in project:
                project_data[child.tag] = child.text
            data.append(project_data)
        pjm_df = pd.DataFrame(data)

        #### Clean the existing columns ####

        # Filter only "Active Projects"
        pjm_active_projects = pjm_df[pjm_df['Status'] == 'Active'].copy()
        # Filter only generation interconnection project
        # This removes projects that are transmission buildouts/updgrades
        pjm_active_projects = pjm_active_projects[pjm_active_projects['ProjectType'] == 'Generation Interconnection'].copy()
        # Convert capacity to float
        pjm_active_projects['MWEnergy'] = pd.to_numeric(pjm_active_projects['MWEnergy'], errors='coerce')
        # Remove any stray instances of the word "County" in order to clean the county column
        # Might turn this into a function in the future
        pjm_active_projects['County'] = pjm_active_projects['County'].str.replace(r' County', '', regex=True)
        # If two or more counties are listed, then only use the first one
        # This system is not perfect, so in the future, I might add a way to split that projects generation evenly across all counties it is located in
        pjm_active_projects['Name'] = pjm_active_projects['Name'] + ' / ' + pjm_active_projects['CommercialName']

        #### Standardize Columns ####

        # These are the 9 columns that I want to keep from the PJM data
        pjm_relevant_fields = ['ProjectNumber', 
                                'Name', 
                                'MWEnergy',
                                'Fuel',
                                'SubmittedDate',
                                'ProjectedInServiceDate',
                                'County',
                                'State',
                                'TransmissionOwner']
        # This function filters down the active sites dataset to the 9 specific fields
        # Then, it renames the columns to standardized ones defined in config.py
        # The columns get sorted in the process
        pjm_active_projects = standardizeFields(pjm_active_projects, pjm_relevant_fields)

        #### Standardize Fuel Types ####

        # Find indices for the most common fuel types
        solar_indices = (pjm_active_projects['fuel'] == 'Solar')
        storage_indices = (pjm_active_projects['fuel'] == 'Storage')
        ss_indices = (pjm_active_projects['fuel'] == 'Solar; Storage')
        wind_indices = (pjm_active_projects['fuel'] == 'Wind') | (pjm_active_projects['fuel'] == 'Offshore Wind')
        gas_indices = (pjm_active_projects['fuel'] == 'Natural Gas')
        
        # Find indices for less common fuels that do not match the predefined set of fuel types
        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
        # Create list object for these indicies
        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]
        
        # This function standardizes the fuel types 
        # This is necessary so we can aggregate all of the dataframe from every ISO/utility
        pjm_active_projects = standardizeFuels(pjm_active_projects, indices_list)

        #### Final Steps ####

        # Create new column to highlight which RTO/utility this data came from
        pjm_active_projects['iso_utility'] = 'PJM'
        # Create a common key from county name and state abbr
        # This will allow the data to be joined to spatial layer later
        pjm_active_projects = createJoinKey(pjm_active_projects)
        # Export to CSV
        # This will act as a "backup" in case the next run fails
        pjm_active_projects.to_csv(f'data/individual_queues/pjm_active_projects.csv', index = False)
        
        return pjm_active_projects

    # If the above code throws an error, fetch the backup data and return that instead
    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in pjm.py', error)
        pjm_backup = pd.read_csv('data/individual_queues/pjm_active_projects.csv')
        return pjm_backup
