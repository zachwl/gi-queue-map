import re
import traceback
import pandas as pd
import tabula

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getSOCOQueue():

    # Check for errors during code execution
    # If anything changes with the access link, or some other scenario,
    # The script will instead use backup data to send to main.py
    try:
        #### Import Data from SoCo ####

        # Link to pdf file with active queued projects
        # This acts as a permanent link, but it doesn't get updated very often
        pdf_url = "http://www.oasis.oati.com/woa/docs/SOCO/SOCOdocs/Active-Gen-IC-Requests.pdf"
        tables = tabula.read_pdf(pdf_url, pages='all', multiple_tables=True)
        soco_active_projects = pd.concat(tables, ignore_index=True)

        #### Clean the existing columns ####

        # Create a state column with the last two digits from the location column
        soco_active_projects['state'] = soco_active_projects['Gen Facility Location'].str[-2:]
        # Extract only the county name from the location column
        soco_active_projects['county'] = soco_active_projects['Gen Facility Location'].apply(lambda x: x.split(' County')[0] if ' County' in x else x)
        # Create column for transmission owner (everything is Southern Company)
        soco_active_projects['Transmission Owner'] = 'Southern Company'
        # Because SoCo lists their fuel and facility types in one column,
        # we need to use a function that will extract just the fuel 
        # This function all fuels for each project as a string
        def extractFuels(gentype):
            fuel_list = re.findall(r'\((.*?)\)', gentype)
            fuel_string = ", ".join(fuel_list)
            return fuel_string
        soco_active_projects['temp_fuel'] = soco_active_projects['Gen Type/Size'].apply(extractFuels)

        #### Standardize Columns ####

        # These are the 9 columns that I want to keep from the SoCo data
        soco_relevant_fields = ['Request', 
                                'Proposed POI', 
                                'Total Net MW', 
                                'temp_fuel', 
                                'Queue Date', 
                                'In-Service\rRequested', 
                                'county', 
                                'state', 
                                'Transmission Owner']
        # This function filters down the active sites dataset to the 9 specific fields
        # Then, it renames the columns to standardized ones defined in config.py
        # The columns get sorted in the process
        soco_active_projects = standardizeFields(soco_active_projects, soco_relevant_fields)
        
        #### Standardize Fuel Types ####

        # Find indices for the most common fuel types
        solar_indices = soco_active_projects['fuel'].str.contains('Solar') & ~soco_active_projects['fuel'].str.contains('Batteries')
        storage_indices = soco_active_projects['fuel'].str.contains('Batteries') & ~soco_active_projects['fuel'].str.contains('Solar')
        ss_indices = soco_active_projects['fuel'].str.contains('Solar') & soco_active_projects['fuel'].str.contains('Batteries')
        wind_indices = soco_active_projects['fuel'].str.contains('Wind')
        gas_indices = soco_active_projects['fuel'].str.contains('Natural Gas')

        # Find indices for less common fuels that do not match the predefined set of fuel types
        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
        # Create list object for these indicies
        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]
    
        # This function standardizes the fuel types 
        # This is necessary so we can aggregate all of the dataframe from every ISO/utility
        soco_active_projects = standardizeFuels(soco_active_projects, indices_list)
    
        #### Final Steps ####

        # Create new column to highlight which RTO/utility this data came from
        soco_active_projects['iso_utility'] = 'SoCo'
        # Create a common key from county name and state abbr
        # This will allow the data to be joined to spatial layer later
        soco_active_projects = createJoinKey(soco_active_projects)
        # Export to CSV
        # This will act as a "backup" in case the next run fails
        soco_active_projects.to_csv(f'data/individual_queues/soco_active_projects.csv', index = False)

        return soco_active_projects
    
    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in soco.py', error)
        soco_backup = pd.read_csv('data/individual_queues/soco_active_projects.csv')
        return soco_backup

#getSOCOQueue().to_csv(f"C:/Users/zleig/Downloads/tempsoco.csv", index = False)
