import re
import traceback
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getSOCOQueue():

    # Check for errors during code execution
    # If anything changes with the access link, or some other scenario,
    # The script will instead use backup data to send to main.py
    try:
        #### Import Data from SoCo ####

        #### Configure options for web driver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")  # Open the browser in maximized mode
        driver = webdriver.Chrome(service=Service("/usr/bin/chromium-driver"),options=options)
        url = "https://app.powerbi.com/view?r=eyJrIjoiN2U3YjcxMDAtZTgzMy00N2RjLWFlZDctYmM0YzY2NGNmZTMzIiwidCI6ImMwYTAyZTJkLTExODYtNDEwYS04ODk1LTBhNGEyNTJlYmYxNyIsImMiOjN9"
        driver.get(url)

        wait = WebDriverWait(driver, 10)

        # Navigate to correct page
        span_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/report-embed/div/div/div[2]/logo-bar/div/div/div/logo-bar-navigation/span/a"))
        )
        span_element.click()

        active_gen_button = wait.until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/report-embed/div/div/div[2]/logo-bar/div/div/div/logo-bar-navigation/section/div[1]/div/div/ul/li[2]/button"))
        )
        active_gen_button.click()

        #### Get number of projects
        text_element = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "value"))
        )
        # Retrieve the text value
        text_value = text_element.text
        num_projects = int(text_value)

        data = []
        #table = driver.find_element(By.CLASS_NAME, "mid-viewport")
        table = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "mid-viewport"))
        )
        headers = driver.find_elements(By.CSS_SELECTOR, f'div[role="columnheader"]')
        col_names = [header.text for header in headers]
        for i in range(num_projects):

            try:
                # Try to locate the row
                row = table.find_element(By.CSS_SELECTOR, f'div[role="row"][row-index="{i}"]')
                #row = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'div[role="row"][row-index="{i}"]')))
            except NoSuchElementException:
                # If row is not found, scroll down and retry
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 500;", table)
                time.sleep(0.5)  # Small delay to allow the page to load
                row = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'div[role="row"][row-index="{i}"]')))

            cells = row.find_elements(By.CSS_SELECTOR, 'div[role="gridcell"]')

            # Process and log each cell's content
            cell_texts = []
            for cell in cells:
                cell_content = cell.text.strip()  # Get the text and remove extra whitespace
                cell_texts.append(cell_content)
            data.append(cell_texts)
        soco_active_projects = pd.DataFrame(data = data, columns = col_names)


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
                                'Queue Date\n ', 
                                'In-Service Requested', 
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
        print(error)
        # Send email notification
        sendEmail('Error raised in soco.py', error)
        soco_backup = pd.read_csv('data/individual_queues/soco_active_projects.csv')
        return soco_backup

#getSOCOQueue().to_csv(f"C:/Users/zleig/Downloads/tempsoco.csv", index = False)