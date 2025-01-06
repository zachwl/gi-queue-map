import traceback
import pandas as pd
import tabula

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail, findNewURL

def getTVAQueue():

        # Check for errors during code execution
        # If anything changes with the access link, or some other scenario,
        # The script will instead use backup data to send to main.py
    try:
        #### Check if data needs to be updated ####

        # Because TVA publishes a new report every few months, this script checks to see
        # if a new link has been found
        url_check = findNewURL("TVA")
        # If the data is still the same as last time, return that same backup data
        if url_check is None:
            tva_backup = pd.read_csv('data/individual_queues/tva_active_projects.csv')
            return tva_backup
        else:
            #### Read in the data and clean in ####

            tva_tables = tabula.read_pdf(url_check, pages = 'all', pandas_options={'header': 1})
            # Because the number of columns changes in the report, we use these tracking variables
            # The last section of the report are projects that are eligible for transitional cluster study
            # This adds an extra column to the table, so we need a variable to track when we've hit it
            reached_ETCS = False
            # This finds the index of that extra column (Transitional Cluster #)
            cluster_index = -1

            # Extract column names
            correct_columns = tva_tables[0].columns

            # Iterate through each page of the pdf to clean the data
            for table in tva_tables:
                if reached_ETCS == True:
                    table.drop(table.columns[cluster_index], axis=1, inplace=True)
                if ('Transitional\rCluster #' in table.columns):
                    reached_ETCS = True
                    cluster_index = table.columns.get_loc('Transitional\rCluster #')
                    table.drop(table.columns[cluster_index], axis=1, inplace=True)
                table.columns = correct_columns

            # Concatenate the table from each page into df
            tva_df = pd.concat(tva_tables, ignore_index=True)

            #### Clean the existing data ####

            # Importing through tabula adds extra rows and columns
            # This removes blank rows
            tva_active_projects = tva_df[~tva_df['Queue #'].isna()]
            # This removes blank columns
            tva_active_projects = tva_active_projects.drop(['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2'], axis=1).copy()
            # Extract only valid projects with valid generation values
            tva_active_projects = tva_active_projects[tva_active_projects['Summer\rMW'] > 0]
            # Add transmission owner column
            tva_active_projects['Transmission Owner'] = 'TVA'
            
            #### Standardize column names ####

            # These are the 9 columns that I want to keep from the MISO data
            tva_relevant_fields = ['Queue #',
                                    'POI',
                                    'Summer\rMW',
                                    'Generator\rType',
                                    'Queue\rDate',
                                    'Requested /\rForecasted\rISD',
                                    'County',
                                    'State',
                                    'Transmission Owner']
            # This function filters down the TVA dataset to the 9 specific fields
            # Then, it renames the columns to standardized ones defined in config.py
            # The columns get sorted in the process
            tva_active_projects = standardizeFields(tva_active_projects, tva_relevant_fields)

            #### Standardize Fuel Types ####

            # Find indices for the most common fuel types
            solar_indices = (tva_active_projects['fuel'] == 'Solar')
            storage_indices = (tva_active_projects['fuel'] == 'Energy\rStorage')
            ss_indices = (tva_active_projects['fuel'] == 'Solar +\rStorage')
            wind_indices = (tva_active_projects['fuel'] == 'Wind')
            gas_indices = (tva_active_projects['fuel'] == 'Gas')

            # Find indices for less common fuels that do not match the predefined set of fuel types
            other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
            # Create list object for these indicies
            indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]

            # This function standardizes the fuel types 
            # This is necessary so we can aggregate all of the dataframe from every ISO/utility
            tva_active_projects = standardizeFuels(tva_active_projects, indices_list)

            #### Final Steps ####

            # Create new column to highlight which RTO/utility this data came from
            tva_active_projects['iso_utility'] = 'TVA'
            # Create a common key from county name and state abbr
            # This will allow the data to be joined to spatial layer later
            tva_active_projects = createJoinKey(tva_active_projects)
            # Export to CSV
            # This will act as a "backup" in case the next run fails
            #tva_active_projects.to_csv(f'data/individual_queues/tva_active_projects.csv', index = False)
            return tva_active_projects
    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in tva.py', error)
        tva_backup = pd.read_csv('data/individual_queues/tva_active_projects.csv')
        return tva_backup
    
#getTVAQueue().to_csv(f"C:/Users/zleig/Downloads/tempTVA.csv", index=None)
