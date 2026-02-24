"""Reads the validation status file and presents all the unvalidated data"""

import json
import pandas as pd

# - read the validation status file
validation_info = pd.read_json(r'validation/output/validation_status.json')
validation_info_fields = list(validation_info.keys())

# - remove the index
validation_info_fields.pop(0)

# - Create an empty dataframe to store unvalidated datapoints
unvalidated_dataframe = pd.DataFrame(
    columns=['GESDB ID', 'Field Name', 'Description(s)'])

num_data_points = len(validation_info)

# - search for unvalidated data points
counter = 0
for row in range(num_data_points):
    for field in validation_info_fields:
        if validation_info.loc[row, field][0]['flag'] == 'Unvalidated':
            # - if found, populate the dataframe
            unvalidated_dataframe.loc[counter, 'GESDB ID'] = row + 1
            unvalidated_dataframe.loc[counter, 'Field Name'] = field
            unvalidated_dataframe.loc[counter, 'Description(s)'] =\
                validation_info.loc[row, field][0]['flag_description']
            counter += 1

# - Create excel writer
writer = pd.ExcelWriter(r'output\unvalidated_data.xlsx')
# - Write dataframe to excel sheet named 'marks'
unvalidated_dataframe.to_excel(writer, 'unvalidated_datapoints', index=False)
# - Save the excel file
writer.save()

print('DataFrame is written successfully to Excel Sheet.')