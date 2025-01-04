import os
import requests
import datetime
from io import BytesIO
import pandas as pd

from config import fuel_indicies, standard_fields
from utils import standardizeFuels, standardizeFields

def getISONEQueue():

    #script_dir = os.path.dirname(os.path.abspath(__file__))
    #os.chdir(script_dir)

    # Get the current date and set the time to midnight
    current_date = datetime.datetime.now().date()
    midnight = datetime.datetime.combine(current_date, datetime.time.min)
    # .NET epoch start (January 1, 0001)
    net_epoch = datetime.datetime(1, 1, 1)

    # Calculate the difference in time between the .NET epoch and the current date at midnight
    time_difference = midnight - net_epoch

    # Convert this time difference to .NET ticks (100-nanosecond intervals)
    net_ticks = int(time_difference.total_seconds() * 1e7)  # Convert seconds to ticks
    #print(f"Current date at midnight in .NET ticks: {int(net_ticks)}")

    # URL to the Excel file (make sure this points directly to the file)
    url = f'https://irtt.iso-ne.com/reports/exportpublicqueue?ReportDate={net_ticks}&Status=A&Jurisdiction='
    # Send a GET request to fetch the content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Load the Excel content into a DataFrame
        excel_file = BytesIO(response.content)
        isone_df = pd.read_excel(excel_file, header=4, engine='openpyxl')
    else:
        print(f"Failed to fetch the file. Status code: {response.status_code}")

    ### Clean the data
    isone_active_projects = isone_df[isone_df['Type'] == 'G'].copy()
    isone_active_projects['County'] = isone_active_projects['County'].str.replace(r' (County|Parish)$', '', regex=True)
    isone_active_projects['County'] = isone_active_projects['County'].str.split('/').str[0]

    ### Standardize Fields

    #isone_cols_to_keep = ['Position', 'Requested', 'Alternative Name', 'Fuel Type', 'Net MW', 'County', 'State', 'Op Date', 'TO Report']
    isone_relevant_columns = ['Position', 'Alternative Name', 'Net MW', 'Fuel Type', 'Requested', 'Op Date', 'County', 'State', 'TO Report']

    isone_active_projects = standardizeFields(isone_active_projects, standard_fields, isone_relevant_columns)


    fuel_indicies['Solar'] = (isone_active_projects['fuel'] == 'SUN')
    fuel_indicies['Solar/Storage'] = (isone_active_projects['fuel'] == 'SUN BAT')
    fuel_indicies['Storage'] = (isone_active_projects['fuel'] == 'BAT')
    fuel_indicies['Wind'] = (isone_active_projects['fuel'] == 'WND')
    fuel_indicies['Natural Gas'] = (isone_active_projects['fuel'] == 'NG')

    fuel_indicies['Other'] = ~(fuel_indicies['Solar'] | fuel_indicies['Storage'] | fuel_indicies['Solar/Storage'] | fuel_indicies['Wind'] | fuel_indicies['Natural Gas'])

    isone_active_projects = standardizeFuels(isone_active_projects, fuel_indicies)

    isone_active_projects['iso_utility'] = 'PJM'

    ####Could be a function in utils in the future
    isone_active_projects['join_key'] = (isone_active_projects['county'] + '_' + isone_active_projects['state']).str.lower()
    
    isone_active_projects.to_csv(f'data/individual_queues/isone_active_projects.csv', index = False)


    return isone_active_projects

#getISONEQueue().to_csv(f'C:/Users/zleig/Downloads/isonetesting.csv', index = False)