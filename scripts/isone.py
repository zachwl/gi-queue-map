import traceback
import requests
import datetime
from io import BytesIO
import pandas as pd

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getISONEQueue():

    # Check for errors during code execution
    # If anything changes with the access link, or some other scenario,
    # The script will instead use backup data to send to main.py
    try:
        #### Import data from ISONE ####

        # The ISONE data download links include:
        # Date in ticks
        # Project Status Type
        # Jurisdiction
        
        # The following is a system to reverse engineer the date in ticks
        # This is fed into the link to retrieve the data
        current_date = datetime.datetime.now().date()
        midnight = datetime.datetime.combine(current_date, datetime.time.min)
        net_epoch = datetime.datetime(1, 1, 1)
        time_difference = midnight - net_epoch
        # Convert this time difference to .NET ticks (100-nanosecond intervals)
        net_ticks = int(time_difference.total_seconds() * 1e7) 

        # URL to the Excel file (should point directly to file)
        # By specifying "A" we are going to retrieve only active projects
        url = f'https://irtt.iso-ne.com/reports/exportpublicqueue?ReportDate={net_ticks}&Status=A&Jurisdiction='
        
        # Get the data
        response = requests.get(url)
        excel_file = BytesIO(response.content)
        isone_active_projects = pd.read_excel(excel_file, header=4, engine='openpyxl')


        #### Clean the existing columns ####

        # Remove all projects that are not generation interconnection
        isone_active_projects = isone_active_projects[isone_active_projects['Type'] == 'G'].copy()
        # Remove any stray instances of the word "County" in order to clean the county column
        # Might turn this into a function in the future
        isone_active_projects['County'] = isone_active_projects['County'].str.replace(r' (County|Parish)$', '', regex=True)
        # If two or more counties are listed, then only use the first one
        # This system is not perfect, so in the future, I might add a way to split that projects generation evenly across all counties it is located in
        isone_active_projects['County'] = isone_active_projects['County'].str.split('/').str[0]
        # Trim down the values for queue date and in service date
        isone_active_projects['Requested'] = isone_active_projects['Requested'].astype(str).str[:10]
        isone_active_projects['Op Date'] = isone_active_projects['Op Date'].astype(str).str[:10]
        # Round the Net MW values to nearest whole number to avoid long floats
        isone_active_projects['Net MW'] = isone_active_projects['Net MW'].round(0)

        #### Standardize Columns ####

        # These are the 9 columns that I want to keep from the NYISO data
        isone_relevant_columns = ['Position', 
                                'Alternative Name', 
                                'Net MW', 
                                'Fuel Type', 
                                'Requested', 
                                'Op Date', 
                                'County', 
                                'State', 
                                'TO Report']
        # This function filters down the active sites dataset to the 9 specific fields
        # Then, it renames the columns to standardized ones defined in config.py
        # The columns get sorted in the process
        isone_active_projects = standardizeFields(isone_active_projects, isone_relevant_columns)

        #### Standardize Fuel Types ####

        # Find indices for the most common fuel types
        solar_indices = (isone_active_projects['fuel'] == 'SUN')
        storage_indices = (isone_active_projects['fuel'] == 'BAT')
        ss_indices = (isone_active_projects['fuel'] == 'SUN BAT')
        wind_indices = (isone_active_projects['fuel'] == 'WND')
        gas_indices = (isone_active_projects['fuel'] == 'NG')

        # Find indices for less common fuels that do not match the predefined set of fuel types
        other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
        # Create list object for these indicies
        indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]
        # This function standardizes the fuel types 
        # This is necessary so we can aggregate all of the dataframe from every ISO/utility
        isone_active_projects = standardizeFuels(isone_active_projects, indices_list)

        #### Final Steps ####

        # Create new column to highlight which RTO/utility this data came from
        isone_active_projects['iso_utility'] = 'ISONE'


        # Once CSV is fully created, bring over the locations of the offshore wind projects
        isone_backup_df = pd.read_csv(f'data/individual_queues/isone_active_projects.csv')
        # Extract wind projects
        isone_wind_projects = isone_backup_df[isone_backup_df['fuel'] == 'Wind']
        #print(len(isone_wind_projects))
        index = isone_wind_projects['id']
        counties = isone_wind_projects['county']
        data = {'id': index, 'county': counties}

        df_for_update = pd.DataFrame(data = data)
        df_for_update.set_index('id', inplace = True, drop = True)
        #df_for_update.to_csv('C:/Users/zleig/Downloads/df_for_update.csv', index = True)
        isone_active_projects.set_index('id', inplace = True, drop = False)

        isone_active_projects.update(df_for_update)

        # Create a common key from county name and state abbr
        # This will allow the data to be joined to spatial layer later
        isone_active_projects = createJoinKey(isone_active_projects)
        missing_county_test = isone_active_projects[(isone_active_projects['county'].isna()) & (isone_active_projects['fuel'] == 'Wind')]
        if len(missing_county_test) > 0:
            sendEmail('Attention needed for ISONE', 'There are wind projects with missing counties')
        # Export to CSV
        # This will act as a "backup" in case the next run fails
        isone_active_projects.to_csv(f'data/individual_queues/isone_active_projects.csv', index = False)

        return isone_active_projects
    
    # If the above code throws an error, fetch the backup data and return that instead   
    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in isone.py', error)
        isone_backup = pd.read_csv('data/individual_queues/isone_active_projects.csv')
        return isone_backup

#getISONEQueue().to_csv('C:/Users/zleig/Downloads/tempisone3.csv', index = False)
