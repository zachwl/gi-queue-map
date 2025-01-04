import xml.etree.ElementTree as ET
import requests
import pandas as pd
from config import standard_fields
from utils import standardizeFuels, standardizeFields, createJoinKey

def getPJMQueue():

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
    #pjm_df = pd.read_csv('tempPJMfromXML.csv')

    pjm_active_projects = pjm_df[pjm_df['Status'] == 'Active'].copy()
    pjm_active_projects = pjm_df[pjm_df['ProjectType'] == 'Generation Interconnection'].copy()

    pjm_active_projects['MWEnergy'] = pd.to_numeric(pjm_active_projects['MWEnergy'], errors='coerce')
    pjm_active_projects['County'] = pjm_active_projects['County'].str.replace(r' County', '', regex=True)
    pjm_active_projects['Name'] = pjm_active_projects['Name'] + ' / ' + pjm_active_projects['CommercialName']

    ### Standardize Columns
    #pjm_cols_to_keep = ['ProjectNumber', 'Name', 'State', 'County', 'TransmissionOwner', 'MWEnergy', 'Fuel', 'SubmittedDate', 'ProjectedInServiceDate']
    pjm_relevant_fields = ['ProjectNumber', 'Name', 'MWEnergy', 'Fuel', 'SubmittedDate', 'ProjectedInServiceDate', 'County', 'State', 'TransmissionOwner']
    pjm_active_projects = standardizeFields(pjm_active_projects, standard_fields, pjm_relevant_fields)

    solar_indices = (pjm_active_projects['fuel'] == 'Solar')
    storage_indices = (pjm_active_projects['fuel'] == 'Storage')
    ss_indices = (pjm_active_projects['fuel'] == 'Solar; Storage') # Will need to add more logic to this to improve accuracy
    wind_indices = (pjm_active_projects['fuel'] == 'Wind') | (pjm_active_projects['fuel'] == 'Offshore Wind')
    gas_indices = (pjm_active_projects['fuel'] == 'Natural Gas')
    
    ####Could be a function in utils in the future
    other_indices = ~(solar_indices | storage_indices | ss_indices | wind_indices | gas_indices)
    indices_list = [solar_indices, storage_indices, ss_indices, wind_indices, gas_indices, other_indices]

    #Standardize the fuel types
    pjm_active_projects = standardizeFuels(pjm_active_projects, indices_list)

    pjm_active_projects['iso_utility'] = 'PJM'

    ####Could be a function in utils in the future
    pjm_active_projects = createJoinKey(pjm_active_projects)

    pjm_active_projects.to_csv(f'data/individual_queues/pjm_active_projects.csv', index = False)
    return pjm_active_projects

#getPJMQueue().to_csv('C:/Users/zleig/Downloads/tempPJM.csv', index=False)
