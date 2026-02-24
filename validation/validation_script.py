import datetime
import json
import pandas as pd
import numpy as np
from dateutil.parser import parse
from .validation_functions import *
from .errorcodes import *



def validation_detail_builder(validation_statuses_list):
    """
    Inputs a list of tuples containing validation statuses from different
    validation checks and returns a validation result` and a
    combined description.

    Parameters
    ----------
    validation_statuses_list: List 
        A list of tuples from each validation check for the GESDB field being
        checked.

    Returns
    -------
    validation_result : str
        String indicating whether the GESDB field is validated or not.
    description_builder : List
        List of strings containing description about validation errors.
    """

    validation_result = ""
    description_builder = []
    validation_results = []

    # collect all the statues
    for status in validation_statuses_list:
        validation_results.append(status[0].lower())

    # check if there is an 'unvalidated' entry
    if 'unvalidated' in validation_results:
        validation_result = 'Unvalidated'
        # collect the descriptions
        for status in validation_statuses_list:
            if status[0].lower() == 'unvalidated':
                description_builder.append(status[1])
    else:
        validation_result = 'Validated'
        description_builder.append(
            'All validation checks passed. Some optional data may still be missing, check error codes')

    description = "".join(description_builder)

    return validation_result, description


def convert_err_code_to_str(error_list):
    """
    Inputs a list of error codes and returns them combined as a single string.

    Parameters
    ----------
    error_list : List 
        List of error codes.

    Returns
    -------
    error_code_str : str
        A single string with the error codes.
    """
    error_codes_str = ''

    for ctr, _ in enumerate(error_list):
        error_codes_str += (', '.join(error_list[ctr])) + ', '

    # - remove the comma at the end of the string
    error_codes_str = error_codes_str.rstrip(', ')
    # - remove the comma at begining of the string (if any)
    error_codes_str = error_codes_str.lstrip(', ')
    return error_codes_str


def run_validation():
     # - Get today's date
    TODAY = datetime.datetime.now().strftime("%m/%d/%y")

    # ***** Read the database JSON file
    df_GESDB = pd.read_json(r'data\output\processed_data.json')
    # df_GESDB = pd.read_json(r'data/test_data.json')
    gesdb_fields = df_GESDB.keys()

    # ***** Read the GESDB Schema/ Rules
    rules_GESDB = pd.read_csv(r'validation\data\gesdb_data_rules.csv')
    # rules_by_name = rules_GESDB.set_index('Unique Field Name')

    # def get_rule(col_name: str):
    #     try:
    #         return rules_by_name.loc[col_name]
    #     except KeyError:
    #         raise KeyError(
    #             f"Rules CSV missing row for '{col_name}'. "
    #             "Add it under 'Unique Field Name' in validation/data/gesdb_data_rules.csv."
    #         )
    # --- add robust name-based rule lookup + default fallback ---
    import re

    rules_by_name = rules_GESDB.set_index('Unique Field Name')

    def _norm(s: str) -> str:
        # lowercase, strip, and remove spaces around / _ -
        return re.sub(r'\s*([/_-])\s*', r'\1', str(s).strip().lower())

    # Map normalized -> original index name for case/spacing-insensitive lookup
    normalized_index = { _norm(name): name for name in rules_by_name.index }

    missing_rules = set()

    DEFAULT_RULE = pd.Series({
        'Required?': 'O',      # Optional by default
        'Data Type': 'Text',   # Treat as free text
        'Lower Range': 'not applicable',
        'Upper Range': 'not applicable'
    })
    def _coerce_rule(rule: pd.Series) -> pd.Series:
        r = rule.copy()

        # Required? -> 'R' or 'O' (default O)
        req = r.get('Required?', 'O')
        if pd.isna(req) or req == '':
            req = 'O'
        r['Required?'] = str(req).strip().upper()[:1]

        # Data Type -> string (default Text)
        dt = r.get('Data Type', 'Text')
        if pd.isna(dt) or dt == '':
            dt = 'Text'
        r['Data Type'] = str(dt).strip()

        # Ranges -> string 'not applicable' if missing
        for k in ('Lower Range', 'Upper Range'):
            v = r.get(k, 'not applicable')
            if pd.isna(v) or str(v).strip() == '':
                r[k] = 'not applicable'
            else:
                r[k] = str(v).strip()

        return r
    def get_rule(col_name: str):
        # 1) exact match
        if col_name in rules_by_name.index:
            return _coerce_rule(rules_by_name.loc[col_name])
        # 2) normalized (case/spacing around slashes)
        k = _norm(col_name)
        if k in normalized_index:
            return _coerce_rule(rules_by_name.loc[normalized_index[k]])
        # 3) fallback + record for reporting
        missing_rules.add(col_name)
        return _coerce_rule(DEFAULT_RULE)
    
    if missing_rules:
        print("WARNING - No rule rows found for:", sorted(missing_rules))

    # - Count number of data points in the database
    num_data_points = df_GESDB['ID'].count()
    num_data_points = len(df_GESDB)
    
    # num_data_points = 10
    
    # ***** Get the column names and add 'Index' as the first column
    column_names = list(rules_GESDB['Unique Field Name'])
    column_names.insert(0, 'Index')

    # ***** Create an empty list for validation statuses
    validation_statuses = []

    # ****** Create an empty list for accumulation of error codes
    error_codes_list = []

    # ***** Create an empty dataframe to store validation information
    validation_dataFrame = pd.DataFrame(
        index=range(num_data_points),
        columns=column_names,
        dtype=object,
    )
    
    # ***** Create an empty dataframe to store any warning from 
    # additional checks
    warnings_columns_names = ['Warning: Capacity to Power Ratio',
                              'Warning: Dates',
                              'Warning: Technology']
    warning_dataFrame = pd.DataFrame(
        index=range(num_data_points),
        columns=warnings_columns_names,
        dtype=object,
    )
        
    # ***** Tuples to store results from validation scripts
    val_results_data_type = tuple()
    val_results_data_range = tuple()
    val_results_field_status = tuple()
    
    application_field_results = []

    # ***** This section of the code iterates over each field in all
    # of the rows/datapoints. Multiple loops are required to access all the
    # fields and the rows. The outer loop indexed by `row` loops over all the
    # rows in the GESDB. The inner loop indexed by `field` iterates over each
    # field in the selected `row`.

    ROW_COUNTER = 0
    # *** outer loops iterates over each row in the GESDB
    for row in range(num_data_points):
        # 'counter' keeps track of each field being validated, even within \
        # the subfields
        COUNTER = 0
        APPLICATION_ERROR_FLAG = False
        app_error_flag_description = []
        app_error_codes = []
        
        # *** populate `index` of the 'validation_dataFrame' for each row
        validation_dataFrame.loc[row, 'Index'] = int(row)

        # *** inner loop iterates over the fields within each row
        # NOTE: Since the fields `applications` and `subsystems` have
        # sub-fields within them, some further processing is required through
        # if-else statements to access those.
        for field in gesdb_fields:    
            # *** access sub-fields within `Applications` field
            if field.lower() == "applications":
                # - Get the names of the sub-fields within `Applications`
                application_sub_fields = df_GESDB[field][row].keys()
                COUNTER += 1
                # - iterate over 'application_sub_fields'
                for sub_field in application_sub_fields:
                    num_applications = len(df_GESDB[field][row][sub_field])
                    for i in range(num_applications):
                        # >>>>>>> 1. Perform DATA TYPE validation <<<<<<<< #
                        # val_results_data_type = validate_data_type(
                        #     data=df_GESDB[field][row][sub_field][i],
                        #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                        #     required_type=rules_GESDB.iloc[COUNTER]['Data Type'])
                        app_rule = get_rule('Applications')
                        val_results_data_type = validate_data_type(
                            data=df_GESDB[field][row][sub_field][i],
                            required=app_rule['Required?'],
                            required_type=app_rule['Data Type']
                        )

                        val_results_application_list = validate_field_applications(
                            df_GESDB[field][row][sub_field][i])
            
                        # >>>>>>> 2. Perform DATA RANGE validation <<<<<<<< #
                        # NOTE: A data range check for `applications` is not
                        # applicable and this check is skipped

                        # - Store result of validation
                        if val_results_data_type[0].lower() == "unvalidated":
                            APPLICATION_ERROR_FLAG = True
                            app_error_flag_description.append("At least one of the applications has a datatype mismatch")
                            app_error_codes.append(str(DataTypeErrors.CODE_DATA_TYPE_MISMATCH_GENERIC.value))
                        elif val_results_application_list[0].lower() == "unvalidated":
                            APPLICATION_ERROR_FLAG = True
                            app_error_flag_description.append("At least one of the applications is not within the list of valid values")
                            app_error_codes.append(str(ApplicationsFieldError.APPLICATION_INVALID.value))
                        else:
                            pass
                        
                # - Check to see if `APPLICATION_ERROR_FLAG` was raised for
                # any case
                if APPLICATION_ERROR_FLAG:
                    validation_details = {'flag': 'Unvalidated',
                                          'flag_description': "".join(app_error_flag_description),
                                          'error_codes': "".join(app_error_codes),
                                          'timestamp': TODAY
                                          }
                    # >>>>>> 3. Populate the validation dataframe <<<<<<< #
                    validation_dataFrame.loc[row, 'Applications'] = [validation_details]
                else:
                    validation_details = {'flag': 'Validated',
                                          'flag_description': 'Data Type Match, Specified applications are within the list of valid values.',
                                          'error_codes': '',
                                          'timestamp': TODAY
                                          }
                    # >>>>>> 3. Populate the validation dataframe <<<<<<< #
                    validation_dataFrame.loc[row, 'Applications'] = \
                        [validation_details]
            # ***** access sub-fields within "Subsystems" field
            elif field.lower() == "subsystems":
                # - collect all the sub-keys within "Subsystems" field. The
                # sub-fields are:  "Subsystem Name", "ID", "Storage Device",
                # "Power Conversion System", "Balance of System"
                subsystems_fields = list(df_GESDB[field][row][0].keys())
                # - access first two sub fields
                # (these do not have further sub-fields)
                # - access "Subsystem Name"
                validation_statuses.clear()
                error_codes_list.clear()
                # # >>>>>>> 1. Perform DATA TYPE validation <<<<<<<< #
                # val_results_data_type = validate_data_type(
                #     data=df_GESDB[field][row][0][subsystems_fields[0]],
                #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                #     required_type=rules_GESDB.iloc[COUNTER]['Data Type'])

                # # >>>>>>> 2. Perform DATA RANGE validation <<<<<<<< #
                # val_results_data_range = validate_data_range(
                #     data=df_GESDB[field][row][0][subsystems_fields[0]],
                #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                #     lower_range=rules_GESDB.iloc[COUNTER]['Lower Range'],
                #     upper_range=rules_GESDB.iloc[COUNTER]['Upper Range'])
                name_label = subsystems_fields[0]  # typically "Subsystem Name"
                name_rule = get_rule(name_label)

                val_results_data_type = validate_data_type(
                    data=df_GESDB[field][row][0][name_label],
                    required=name_rule['Required?'],
                    required_type=name_rule['Data Type'])

                val_results_data_range = validate_data_range(
                    data=df_GESDB[field][row][0][name_label],
                    required=name_rule['Required?'],
                    lower_range=name_rule['Lower Range'],
                    upper_range=name_rule['Upper Range'])
                
                validation_statuses.append(val_results_data_type)
                validation_statuses.append(val_results_data_range)
                error_codes_list.append(val_results_data_type[2])
                error_codes_list.append(val_results_data_range[2])

                res, des = validation_detail_builder(validation_statuses)
                err_codes = convert_err_code_to_str(error_codes_list)

                validation_details = {'flag': res,
                                      'flag_description': des,
                                      'error_codes': err_codes,
                                      'timestamp': TODAY}

                # >>>>>> 3. Populate the validation dataframe <<<<<<< #
                validation_dataFrame.loc[row, subsystems_fields[0]] = [
                    validation_details]
                # COUNTER += 1
                # - remove "Subsystem Name" that is already accessed
                subsystems_fields.pop(0)

                validation_statuses.clear()
                error_codes_list.clear()
                # access "ID"
                # # >>>>>>> 1. Perform DATA TYPE validation <<<<<<<< #
                # val_results_data_type = validate_data_type(
                #     data=df_GESDB[field][row][0][subsystems_fields[0]],
                #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                #     required_type=rules_GESDB.iloc[COUNTER]['Data Type'])

                # # >>>>>>> 2. Perform DATA RANGE validation <<<<<<<< #
                # val_results_data_range = validate_data_range(
                #     data=df_GESDB[field][row][0][subsystems_fields[0]],
                #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                #     lower_range=rules_GESDB.iloc[COUNTER]['Lower Range'],
                #     upper_range=rules_GESDB.iloc[COUNTER]['Upper Range'])
                id_label_raw = subsystems_fields[0]          # typically "ID"
                id_output_col = f"Subsystem {id_label_raw}"  # you write to this output name
                id_rule = get_rule(id_output_col)

                val_results_data_type = validate_data_type(
                    data=df_GESDB[field][row][0][id_label_raw],
                    required=id_rule['Required?'],
                    required_type=id_rule['Data Type'])

                val_results_data_range = validate_data_range(
                    data=df_GESDB[field][row][0][id_label_raw],
                    required=id_rule['Required?'],
                    lower_range=id_rule['Lower Range'],
                    upper_range=id_rule['Upper Range'])
                
                validation_statuses.append(val_results_data_type)
                validation_statuses.append(val_results_data_range)
                error_codes_list.append(val_results_data_type[2])
                error_codes_list.append(val_results_data_range[2])

                res, des = validation_detail_builder(validation_statuses)
                # - convert error_codes_list to a string
                err_codes = convert_err_code_to_str(error_codes_list)

                validation_details = {'flag': res,
                                      'flag_description': des,
                                      'error_codes': err_codes,
                                      'timestamp': TODAY}

                # >>>>>> 3. Populate the validation dataframe <<<<<<< #
                validation_dataFrame.loc[
                    row, "Subsystem " +
                    subsystems_fields[0]] = [validation_details]
                # COUNTER += 1
                # - remove "ID" that is already accessed
                subsystems_fields.pop(0)
                # - iterate over the remaining 'subsystems_fields':
                # "Storage Device",
                # "Power Conversion System",
                # "Balance of System"
                for sub_field in subsystems_fields:
                    sub_field_keys = df_GESDB[field][row][0][sub_field].keys()
                    # - each of the 'sub_field' have 'sub_sub_field'
                    # - iterate over the 'sub_field_keys' to access
                    # 'sub_sub_field'
                    for sub_sub_field in sub_field_keys:
                        validation_statuses.clear()
                        error_codes_list.clear()
                        # # >>>>>>> 1. Perform DATA TYPE validation <<<<<<<< #
                        # val_results_data_type = validate_data_type(
                        #     data=df_GESDB[field][row][0][sub_field][sub_sub_field],
                        #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                        #     required_type=rules_GESDB.iloc[COUNTER]['Data Type'])

                        # # >>>>>>> 2. Perform DATA RANGE validation <<<<<<<< #
                        # val_results_data_range = validate_data_range(
                        #     data=df_GESDB[field][row][0][sub_field][sub_sub_field],
                        #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                        #     lower_range=rules_GESDB.iloc[COUNTER]['Lower Range'],
                        #     upper_range=rules_GESDB.iloc[COUNTER]['Upper Range'])
                        col_name = f"{sub_field} - {sub_sub_field}"
                        rule = get_rule(col_name)

                        val_results_data_type = validate_data_type(
                            data=df_GESDB[field][row][0][sub_field][sub_sub_field],
                            required=rule['Required?'],
                            required_type=rule['Data Type'])

                        val_results_data_range = validate_data_range(
                            data=df_GESDB[field][row][0][sub_field][sub_sub_field],
                            required=rule['Required?'],
                            lower_range=rule['Lower Range'],
                            upper_range=rule['Upper Range'])
                        
                        validation_statuses.append(val_results_data_type)
                        validation_statuses.append(val_results_data_range)
                        error_codes_list.append(val_results_data_type[2])
                        error_codes_list.append(val_results_data_range[2])
                        
                        # >>> Perform Validation of GESDB field 
                        # `Technology Broad Category` <<< #
                        if sub_sub_field.lower() == 'technology broad category':
                            val_results_field_tech_broad_category = validate_field_tech_broad_category(data=df_GESDB[field][row][0][sub_field][sub_sub_field])
                            validation_statuses.append(val_results_field_tech_broad_category)
                            error_codes_list.append(val_results_field_tech_broad_category[2])

                        if sub_sub_field.lower() == 'technology mid-type':
                            val_results_field_tech_mid_type = validate_field_tech_mid_type(data=df_GESDB[field][row][0][sub_field][sub_sub_field], tech_broad_category=df_GESDB[field][row][0][sub_field]['Technology Broad Category'])
                            validation_statuses.append(val_results_field_tech_mid_type)
                            error_codes_list.append(val_results_field_tech_mid_type[2])
                        
                        res, des = validation_detail_builder(
                            validation_statuses)
                        # - convert error_codes_list to a string
                        err_codes = convert_err_code_to_str(error_codes_list)
                        

                        validation_details = {'flag': res,
                                              'flag_description': des,
                                              'error_codes': err_codes,
                                              'timestamp': TODAY}

                        # >>>>>> 3. Populate the validation dataframe <<<<<<< #
                        validation_dataFrame.loc[row, sub_field +
                                                 " - " + sub_sub_field] = [validation_details]
                        COUNTER += 1

            # ***** access the fields without any sub-fields
            else:
                extracted_field_name = field
                validation_statuses.clear()
                error_codes_list.clear()
                # # >>>>>>> 1. Perform DATA TYPE validation <<<<<<<< #
                # val_results_data_type = validate_data_type(
                #     data=df_GESDB[field][row],
                #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                #     required_type=rules_GESDB.iloc[COUNTER]['Data Type'])
                # validation_statuses.append(val_results_data_type)
                # error_codes_list.append(val_results_data_type[2])

                # # >>>>>>> 2. Perform DATA RANGE validation <<<<<<<< #
                # val_results_data_range = validate_data_range(
                #     data=df_GESDB[field][row],
                #     required=rules_GESDB.iloc[COUNTER]['Required?'],
                #     lower_range=rules_GESDB.iloc[COUNTER]['Lower Range'],
                #     upper_range=rules_GESDB.iloc[COUNTER]['Upper Range'])
                # validation_statuses.append(val_results_data_range)
                # error_codes_list.append(val_results_data_range[2])
                field_rule = get_rule(field)

                val_results_data_type = validate_data_type(
                    data=df_GESDB[field][row],
                    required=field_rule['Required?'],
                    required_type=field_rule['Data Type'])

                val_results_data_range = validate_data_range(
                    data=df_GESDB[field][row],
                    required=field_rule['Required?'],
                    lower_range=field_rule['Lower Range'],
                    upper_range=field_rule['Upper Range'])

          

                # >>> 3. Perform Validation of GESDB field `Status` <<<< #
                if field.lower() == 'status':
                    val_results_field_status = validate_field_status(
                        data=df_GESDB[field][row])
                    validation_statuses.append(val_results_field_status)
                    error_codes_list.append(val_results_field_status[2])
  
                # >>> Perform Validation of GESDB field `URL` <<< #
                if field.lower() == 'url':
                    val_results_field_url = validate_field_url(
                        data=df_GESDB[field][row]
                    )
                    validation_statuses.append(val_results_field_url)
                    error_codes_list.append(val_results_field_url[2])
                    
                 # >>> Perform Validation of GESDB field 
                 # `Grid Interconnection Level` <<< #
                if field.lower() == 'grid interconnection level':
                    val_results_field_interconnection = validate_field_interconnection_level(
                        data=df_GESDB[field][row]
                    )
                    validation_statuses.append(val_results_field_interconnection)
                    error_codes_list.append(val_results_field_interconnection[2])
                

                res, des = validation_detail_builder(
                    validation_statuses)
                # - convert error_codes_list to a string
                err_codes = convert_err_code_to_str(error_codes_list)

                validation_details = {'flag': res,
                                      'flag_description': des,
                                      'error_codes': err_codes,
                                      'timestamp': TODAY}

                validation_dataFrame.loc[row, field] = [validation_details]

                COUNTER += 1
                
        # ****** These set of validation only need to be performed once per field   
        # *** Check for storage capacity to power ratio
        msg, warn_code = validate_capacity_to_power_ratio(data_rated_power=df_GESDB.iloc[ROW_COUNTER]['Rated Power (kW)'],
                                         data_storage_capacity=df_GESDB.iloc[ROW_COUNTER]['Storage Capacity (kWh)'],
                                         discharge_hours=df_GESDB.iloc[ROW_COUNTER]['Discharge Duration at Rated Power (hrs)'],
                                         threshold_hours=200.0)
        warn_code_str = convert_err_code_to_str([warn_code])
        warning_msg_details = {'warning_message': msg,
                               'error_codes': warn_code_str,
                               'timestamp': TODAY}
        warning_dataFrame.loc[row, 'Warning: Capacity to Power Ratio'] = [warning_msg_details]
        
        # *** Check for dates
        msg, warn_code = validate_dates(df_GESDB.iloc[ROW_COUNTER]['Announced Date'],
                       df_GESDB.iloc[ROW_COUNTER]['Constructed Date'],
                       df_GESDB.iloc[ROW_COUNTER]['Commissioned Date'],
                       df_GESDB.iloc[ROW_COUNTER]['Decommissioned Date'])
        warn_code_str = convert_err_code_to_str([warn_code])
        warning_msg_details = {'warning_message': msg,
                               'error_codes': warn_code_str,
                               'timestamp': TODAY}
        warning_dataFrame.loc[row, 'Warning: Dates'] = [warning_msg_details]
       
        ROW_COUNTER += 1

    # ******  Write results to CSV file
    validation_dataFrame.to_csv(r'validation/output/validation_status.csv', index=False)
    warning_dataFrame.to_csv(r'validation/output/warning_messages.csv', index=False)

    # ****** Write results to JSON file
    validation_data_str = validation_dataFrame.to_json(orient='records')
    validation_data_str_parsed = json.loads(validation_data_str)

    with open(r'output/validation_status.json', 'w') as f:
        json.dump(validation_data_str_parsed, f, indent=2)

    print("VALIDATION CODE EXECUTED !!! ")

if __name__ == '__main__':
   run_validation()
