import re
import requests
from datetime import datetime, timedelta
import pandas as pd
from config import standard_fuels

#script_dir = os.path.dirname(os.path.abspath(__file__))
#os.chdir(script_dir)

def createJoinKey(df):
    df['join_key'] = (df['county'].str.replace(r'[ .-]', '', regex=True) + '_' + df['state']).str.lower()
    return df

def standardizeFields(df, standard_columns, input_columns):
    # Create a mapping from standard_columns to input_columns using zip
    column_mapping = dict(zip(standard_columns, input_columns))
    
    # Subset the DataFrame to include only the input columns
    subset_columns = []

    # Loop through each standard column name
    for col in standard_columns:
        # Use the mapping to find the corresponding column name in the input DataFrame
        mapped_column = column_mapping[col]
        # Add the mapped column name to the list
        subset_columns.append(mapped_column)

    # Use the list of mapped column names to subset the DataFrame
    df_subset = df[subset_columns]  
    
    # Rename the columns to the standard column names
    df_subset.columns = standard_columns
    
    # Return the standardized DataFrame
    return df_subset

def standardizeFuels(projects, fuel_indices):
    fuel_index_dict = zip(standard_fuels, fuel_indices)
    for fuel, indices in fuel_index_dict:
        projects.loc[indices, 'fuel'] = fuel
    return projects

def isURLValid(url):
    try:
        request = requests.get(url)
        if request.status_code == 200:
            return True
        else:
            return False
    except:
        return False

def findNewURL(utility):
    #Access the download settings that track working urls and data updates
    ds_path = f"download_settings.csv"
    download_settings = pd.read_csv(ds_path, index_col='name')

    #Read data from download settings
    base_url = download_settings.loc[utility]['base_url']
    last_updated = download_settings.loc[utility]['last_updated']
    date_format = download_settings.loc[utility]['date_format']

    #Convert tracker to datetime object
    date_tracker = datetime.strptime(last_updated, "%m/%d/%Y")

    #If the URL on file is already working, return None to indicate no update is necessary
    if isURLValid(base_url.format(date_tracker.strftime(date_format))):
        print("Data up to date")
        return None

    #If the URL on file does not work anymore, loop through all possible dates to find something new
    while date_tracker < datetime.now():
        #Create URL for testing
        formatted_date = date_tracker.strftime(date_format)
        full_url = base_url.format(formatted_date)
        #If the URL is valid, that means that the dataset needs to be updated
        if isURLValid(full_url):
            print("Found valid URL: " + full_url)
            correct_date = date_tracker.strftime("%m/%d/%Y")
            #Update download settings to reflect changes
            download_settings.loc[utility, 'last_updated'] = correct_date
            #Save changes
            download_settings.to_csv(ds_path)
            print("updated file")
            #Return the new URL so the module can update the data
            return full_url
        else:
            #If no valid URL found, try the next day
            date_tracker = date_tracker + timedelta(days=1)
    print("Needs attention - no valid URL found")
    with open(f"scripts/script_data/temp_errors.txt", "w") as text_file:
        text_file.write("Needs attention - no valid URL found for: " + utility)
    return None

#findNewURL('TVA')
