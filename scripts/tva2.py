import traceback
import pandas as pd
import tabula

from utils import standardizeFuels, standardizeFields, createJoinKey, sendEmail

def getTVAQueue():

        # Check for errors during code execution
        # If anything changes with the access link, or some other scenario,
        # The script will instead use backup data to send to main.py
    try:
        #### Check if data needs to be updated ####

        # Because TVA publishes a new report every few months, this script checks to see
        # if a new link has been found
        url_check = 'http://www.oasis.oati.com/woa/docs/TVA/TVAdocs/QueueTransition_-_Election_-_final.pdf'

        tabula.read_pdf(url_check, pages = 'all', pandas_options={'header': 1})

    except Exception as e:
        error = traceback.format_exc()
        # Send email notification
        sendEmail('Error raised in tva.py', error)

    tva_backup = pd.read_csv('data/individual_queues/tva_active_projects.csv')
    return tva_backup
    
#getTVAQueue().to_csv(f"C:/Users/zleig/Downloads/tempTVA2.csv", index=None)
