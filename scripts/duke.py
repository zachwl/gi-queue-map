import requests
import traceback
import pandas as pd
from io import BytesIO

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail, findNewURL

def importDuke(url):
    response = requests.get(url)
    excel_file = BytesIO(response.content)
    # The active projects are in the first sheet
    # Gets read by default
    duke_df = pd.read_excel(excel_file, engine='openpyxl')
    header_row_index = duke_df[duke_df.iloc[:, 1] == "OPCO"].index[0]

    # Set that row as the header
    df_cleaned = duke_df.iloc[header_row_index + 1:-2].reset_index(drop=True)  # Rows below the header row
    df_cleaned.columns = duke_df.iloc[header_row_index]  # Set the column names
    return df_cleaned

def getDukeQueue():
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
        duke_df = duke_df[~duke_df['Operational Status'].isin(["Withdrawn", "Commercial Operation - Commercial Operation Date Declared"])]
        duke_df['POI'] = duke_df['Transmission Line'].astype(str) + duke_df['Substation Name'].astype(str)
        return duke_df
getDukeQueue()