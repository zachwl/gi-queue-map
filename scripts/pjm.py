import os
import xml.etree.ElementTree as ET
import requests
import pandas as pd
from config import fuel_indicies, standard_fields
from utils import standardizeFuels, standardizeFields

def getPJMQueue():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    #'''
    url = 'https://www.pjm.com/pub/planning/downloads/xml/PlanningQueues.xml'
    response = requests.get(url)

    xml_content = response.content
    root = ET.fromstring(xml_content)
    data = []
    for project in root.findall(".//Project"):
        project_data = {}
        for child in project:
            project_data[child.tag] = child.text
        data.append(project_data)

    # Step 4: Convert the list of dictionaries into a pandas DataFrame
    pjm_df = pd.DataFrame(data)
    #'''
    #pjm_df = pd.read_csv('tempPJMfromXML.csv')

    pjm_active_projects = pjm_df[pjm_df['Status'] == 'Active'].copy()
    pjm_active_projects['MWEnergy'] = pd.to_numeric(pjm_active_projects['MWEnergy'], errors='coerce')
    pjm_active_projects['County'] = pjm_active_projects['County'].str.replace(r' County', '', regex=True)
    pjm_active_projects['Name'] = pjm_active_projects['Name'] + ' / ' + pjm_active_projects['CommercialName']

    ### Standardize Columns
    #pjm_cols_to_keep = ['ProjectNumber', 'Name', 'State', 'County', 'TransmissionOwner', 'MWEnergy', 'Fuel', 'SubmittedDate', 'ProjectedInServiceDate']
    pjm_relevant_fields = ['ProjectNumber', 'Name', 'MWEnergy', 'Fuel', 'SubmittedDate', 'ProjectedInServiceDate', 'County', 'State', 'TransmissionOwner']
    pjm_active_projects = standardizeFields(pjm_active_projects, standard_fields, pjm_relevant_fields)

    fuel_indicies['Solar'] = (pjm_active_projects['fuel'] == 'Solar')
    fuel_indicies['Storage'] = (pjm_active_projects['fuel'] == 'Storage')
    fuel_indicies['Solar/Storage'] = (pjm_active_projects['fuel'] == 'Solar; Storage') # Will need to add more logic to this to improve accuracy
    fuel_indicies['Wind'] = (pjm_active_projects['fuel'] == 'Wind') | (pjm_active_projects['fuel'] == 'Offshore Wind')
    fuel_indicies['Natural Gas'] = (pjm_active_projects['fuel'] == 'Natural Gas')
    
    ####Could be a function in utils in the future
    fuel_indicies['Other'] = ~(fuel_indicies['Solar'] | fuel_indicies['Storage'] | fuel_indicies['Solar/Storage'] | fuel_indicies['Wind'] | fuel_indicies['Natural Gas'])

    #Standardize the fuel types
    pjm_active_projects = standardizeFuels(pjm_active_projects, fuel_indicies)

    pjm_active_projects['iso_utility'] = 'PJM'

    ####Could be a function in utils in the future
    pjm_active_projects['join_key'] = (pjm_active_projects['county'] + '_' + pjm_active_projects['state']).str.lower()

    pjm_active_projects.to_csv(f'../data/individual_queues/pjm_active_projects.csv', index = False)
    return pjm_active_projects
#getPJMQueue().to_csv('tempPJMfromXML.csv', index=False)