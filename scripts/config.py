import pandas as pd

standard_fields = ['id',
                    'name', 
                    'capacity', 
                    'fuel', 
                    'submitted_date', 
                    'service_date', 
                    'county', 
                    'state', 
                    'transmission_owner']

standard_fuels = ['Solar', 'Storage', 'Solar+Storage', 'Wind', 'Natural Gas', 'Other']
'''
fuel_indicies = {'Solar': pd.Series(),
                'Storage': pd.Series(),
                'Solar/Storage': pd.Series(),
                'Wind': pd.Series(),
                'Natural Gas': pd.Series(),
                'Other': pd.Series()}

'''